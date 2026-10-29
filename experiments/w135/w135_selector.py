"""W135 stage 2 (139_prereg_w135_stage2.md): the generated-candidate selector and the ONE insertion policy.
Rows: every B product (arm both) of every query of the given worlds; label = the product's official key is the truth (training only).
Features (observable only; fixed list FEATS): product f.z, GL (released GLACIER on the product, missing flag), MetFrag-lite, parent score, parents,
sources, edit steps / groups, off_mass, f.z rank in B, B size; differences to P's rank-1 candidate (f.z vs fp, GL, MetFrag) and the rank fractions
of f.z / GL among the view list + B; query: P's rank-1 / rank-2 score gap, gl_ok, lib_max, list size, best analog similarity, peer structures,
train parents. No truth, class, P-rank-of-truth or popularity / source feature.
Model: standardised features -> logistic regression (L2, C = 1.0, max_iter 2000), row weight 1 / (B size of the query).
q table: P's rank-r correctness by r (1..25) x bin (lib_max >= 0.9 / gl_ok / fallback), from the training worlds (equal weight per world).
Policy per query: x = argmax p_hat over B (ties: f.z, key); G_k = p_hat / k - (1 - p_hat) * sum_{r=k..25} q_r (1/r - 1/(r+1)) (r = 25 -> 1/25);
insert x at k* = argmax G_k if G_k* > 0, else keep P.
Modes: --cv (leave-one-pair-out over the design pairs (dFj, dRj), all pi of a pair in the same fold) | --fit (all given worlds -> frozen model) |
--apply (frozen model on other worlds). Every mode writes per-query outcomes (P's RR, the policy's RR, action) = <out>_queries.parquet.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_selector.py --mode cv --worlds dF1_p30 dR1_p30 ... --out experiments/w135/s2/cv"""
import argparse, hashlib, json, os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
FEATS = ["fz", "gl", "gl_miss", "frag", "apsc", "log_npar", "src_peer", "src_train", "n_steps", "e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other", "off_mass",
         "fz_rank_b", "log_nb", "d_fz_top1", "d_gl_top1", "d_gl_miss", "d_frag_top1", "fz_rankfrac_all", "gl_rankfrac_all", "p_gap12", "gl_ok", "lib_max", "log_ncand",
         "best_analog", "n_peer_struct", "n_train"]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_selector): {m}")
def edit_groups(combo):
    c = combo or ""; g = dict(e_sugar=0, e_methyl=0, e_redox=0, e_acyl=0, e_other=0)
    for step in c.split("+"):
        if not step: continue
        if any(t in step for t in ("Hex", "Pen", "GlcA", "glyc")): g["e_sugar"] = 1
        elif "Me" in step: g["e_methyl"] = 1
        elif any(t in step for t in ("OH", "H2", "ox_", "COOH")): g["e_redox"] = 1
        elif any(t in step for t in ("Ac_", "Mal", "Cou", "Caf", "Fer", "Gal")): g["e_acyl"] = 1
        else: g["e_other"] = 1
    return g
_FR = {}
def _frag_job(t):
    import b1_frag as BF
    mid, smiles_list, spectra = t
    return mid, {s: float(BF.score(BF.fragments(s), spectra)) for s in smiles_list}


def load_world(wname, need_label):
    """-> (rows DataFrame of B products with features, per-query DataFrame) for one world experiments/w135/worlds/<wname>."""
    W = os.path.join(ROOT, "experiments/w135/worlds", wname); b, p = wname.split("_p")
    G = pd.read_parquet(os.path.join(W, "gen_full_v2.parquet")); G["molecule"] = G.molecule.astype(str)
    P = pd.read_parquet(os.path.join(W, "P.parquet")); P["molecule"] = P.molecule.astype(str); P = P.set_index("molecule")
    M = pd.read_csv(os.path.join(W, f"b1_molecules_{b}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    F = pd.read_parquet(os.path.join(W, f"b1_features_{b}.parquet")); F["molecule"] = F.molecule.astype(str)
    gl = json.load(open(os.path.join(W, "work", f"gl_{b}.json"))); pgl = json.load(open(os.path.join(W, "prod_gl.json")))
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str); bt = bt.set_index("molecule")
    if set(G.molecule) != set(bt.index) or set(P.index) != set(bt.index) or G.molecule.duplicated().any(): stop(f"{wname}: roster")
    runner = {d["mid"]: d for d in json.load(open(os.path.join(W, "prod_runner_in.json")))}
    # MetFrag-lite for the B products and P's rank-1 (query spectra of the product runner input)
    tasks = []
    for r in G.itertuples(index=False):
        det = json.loads(r.B_detail_both); t25 = json.loads(P.loc[r.molecule, "top25"])
        sm = [d[1] for d in det] + ([t25[0][2]] if t25 else [])
        sp = [dict(mz=np.asarray(s["mz"]), it=np.asarray(s["it"]), prec=s["prec"], mode=s["mode"]) for s in runner[r.molecule]["spectra"]]
        tasks.append((r.molecule, sm, sp))
    with Pool(12) as pool_: FR = dict(pool_.map(_frag_job, tasks, chunksize=2))
    rows, qrows = [], []
    for r in G.itertuples(index=False):
        m = r.molecule; det = json.loads(r.B_detail_both); t25 = json.loads(P.loc[m, "top25"]); gq = gl.get(m) or {}; pq = pgl.get(m) or {}
        view = F[(F.molecule == m) & F.in_short_c2.astype(bool) & (F.in_tier | F.in_coconut | F.in_train_c2).astype(bool)]
        fp_all = view.fp.astype(float).values; gl_all = np.array([np.nan if gq.get(s) is None else float(gq[s]) for s in view.smiles], float)
        top_fp = float(view[view.official_key.astype(str) == t25[0][1]].fp.astype(float).max()) if t25 else np.nan
        top_gl = (np.nan if gq.get(t25[0][2]) is None else float(gq[t25[0][2]])) if t25 else np.nan
        top_fr = FR[m].get(t25[0][2], 0.0) if t25 else 0.0
        sc = [e[3] for e in t25]; gap = float(sc[0] - sc[1]) if len(sc) >= 2 else (10.0 if len(sc) == 1 else 0.0)
        an = json.loads(P.loc[m, "analogs"]); tk = str(bt.loc[m, "scorer_key"]) if need_label else None
        q = dict(world=wname, batch=b, pi=int(p), molecule=m, fam=int(bt.loc[m, "fam"]), wclass=str(bt.loc[m, f"wclass_p{p}"]), truth=str(bt.loc[m, "scorer_key"]),
                 top25=[e[1] for e in t25], gl_ok=int(P.loc[m, "gl_ok"]), lib_max=float(M.loc[m, "lib_max_c2"]) if m in M.index and "lib_max_c2" in M.columns else 0.0,
                 n_cand=int(P.loc[m, "n_cand"]), n_b=len(det))
        q["bin"] = "lib" if q["lib_max"] >= 0.9 else ("gl" if q["gl_ok"] else "fb"); qrows.append(q)
        fz_b = np.array([d[2] for d in det], float); all_fz = np.concatenate([fp_all[np.isfinite(fp_all)], fz_b]) if len(det) else fp_all
        gl_b = np.array([np.nan if pq.get(d[1]) is None else float(pq[d[1]]) for d in det], float); all_gl = np.concatenate([gl_all[np.isfinite(gl_all)], gl_b[np.isfinite(gl_b)]])
        for i, d in enumerate(det):
            key, smi, fz, apsc, npar, srcs, combo, loc, off = d
            g_ = gl_b[i]; fr = FR[m].get(smi, 0.0)
            row = dict(world=wname, molecule=m, key=key, fz=fz, gl=0.0 if not np.isfinite(g_) else g_, gl_miss=int(not np.isfinite(g_)), frag=fr, apsc=apsc, log_npar=np.log1p(npar),
                       src_peer=int("peer" in srcs), src_train=int("train" in srcs), n_steps=(combo or "").count("+") + 1, off_mass=int(bool(off)),
                       fz_rank_b=(i + 1) / len(det), log_nb=np.log1p(len(det)), d_fz_top1=(fz - top_fp) if np.isfinite(top_fp) else 0.0,
                       d_gl_top1=(g_ - top_gl) if (np.isfinite(g_) and np.isfinite(top_gl)) else 0.0, d_gl_miss=int(not (np.isfinite(g_) and np.isfinite(top_gl))), d_frag_top1=fr - top_fr,
                       fz_rankfrac_all=float((all_fz > fz).sum()) / max(1, len(all_fz)), gl_rankfrac_all=(float((all_gl > g_).sum()) / max(1, len(all_gl))) if np.isfinite(g_) else 1.0,
                       p_gap12=gap, gl_ok=q["gl_ok"], lib_max=q["lib_max"], log_ncand=np.log1p(q["n_cand"]), best_analog=float(an[0][1]) if an else 0.0,
                       n_peer_struct=int(r.n_peer_struct), n_train=int(r.n_train), w=1.0 / len(det), **edit_groups(combo))
            if need_label: row["y"] = int(key == tk)
            rows.append(row)
    R = pd.DataFrame(rows); Q = pd.DataFrame(qrows)
    if len(R) and not np.isfinite(R[FEATS].values.astype(float)).all(): stop(f"{wname}: non-finite feature")
    return R, Q


def q_table(Qs):
    """P's rank-r correctness by bin, equal weight per world: q[bin][r-1]."""
    out = {}
    for bn in ("lib", "gl", "fb"):
        acc = np.zeros(25); wsum = 0.0
        for w, Q in Qs.groupby("world"):
            Qb = Q[Q["bin"] == bn]
            if not len(Qb): continue
            h = np.zeros(25)
            for t, top in zip(Qb.truth, Qb.top25):
                if t in top[:25]: h[top.index(t)] += 1
            acc += h / len(Qb); wsum += 1
        out[bn] = (acc / wsum).tolist() if wsum else [0.0] * 25
    return out


def policy(R, Q, model, qt):
    """per-query action and RR (P and policy)."""
    R = R.copy()
    if len(R):
        Z = (R[FEATS].values.astype(float) - np.asarray(model["mean"])) / np.asarray(model["scale"]); R["p"] = 1.0 / (1.0 + np.exp(-(Z @ np.asarray(model["coef"]) + model["intercept"])))
    else: R["p"] = []
    best = R.sort_values(["world", "molecule", "p", "fz", "key"], ascending=[True, True, False, False, True]).groupby(["world", "molecule"]).head(1).set_index(["world", "molecule"])
    out = []
    for q in Q.itertuples(index=False):
        top = list(q.top25); rrP = next((1.0 / (i + 1) for i, k in enumerate(top[:25]) if k == q.truth), 0.0)
        act, kstar, ph, xk = "keep", 0, 0.0, ""
        if (q.world, q.molecule) in best.index:
            x = best.loc[(q.world, q.molecule)]; ph = float(x["p"]); xk = str(x["key"]); qq = qt[q.bin]
            G = []
            for k in (1, 2, 3):
                loss = sum(qq[r - 1] * ((1.0 / r - 1.0 / (r + 1)) if r < 25 else 1.0 / 25) for r in range(k, 26)) if len(top) >= k else 0.0
                G.append(ph / k - (1 - ph) * loss)
            kb = int(np.argmax(G))
            if G[kb] > 0: act, kstar = "insert", kb + 1
        new = (top[:kstar - 1] + [xk] + top[kstar - 1:])[:25] if act == "insert" else top[:25]
        rr = next((1.0 / (i + 1) for i, k in enumerate(new) if k == q.truth), 0.0)
        out.append(dict(world=q.world, batch=q.batch, pi=q.pi, molecule=q.molecule, fam=q.fam, wclass=q.wclass, rrP=rrP, rr=rr, action=act, k=kstar, p_hat=ph, x_key=xk, x_is_truth=int(xk == q.truth), bin=q.bin))
    return pd.DataFrame(out)


def fit(R, Q):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    X = R[FEATS].values.astype(float); y = R.y.values.astype(int)
    if y.sum() == 0: stop("no positive rows")
    sc = StandardScaler().fit(X); clf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X), y, sample_weight=R.w.values)
    model = dict(mean=sc.mean_.tolist(), scale=sc.scale_.tolist(), coef=clf.coef_[0].tolist(), intercept=float(clf.intercept_[0]))   # plain JSON (no pickle)
    return model, q_table(Q)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", required=True, choices=["cv", "fit", "apply"]); ap.add_argument("--worlds", nargs="+", required=True)
    ap.add_argument("--model", default=""); ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time()
    OUT = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out); os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.exists(OUT + "_queries.parquet"): stop(f"{OUT}_queries.parquet exists")
    Rs, Qs = [], []
    for w in a.worlds:
        R, Q = load_world(w, need_label=(a.mode != "apply")); Rs.append(R); Qs.append(Q); print(f"[{time.time()-t0:5.0f}s] {w}: {len(Q)} queries, {len(R)} product rows", flush=True)
    R = pd.concat(Rs, ignore_index=True); Q = pd.concat(Qs, ignore_index=True)
    meta = dict(mode=a.mode, worlds=a.worlds, feats=FEATS, script_sha256=sha(os.path.abspath(__file__)))
    if a.mode == "cv":
        pair = lambda w: w.split("_p")[0][-1]   # dF1 / dR1 -> "1"
        outs = []
        for f in sorted({pair(w) for w in a.worlds}):
            tr = [w for w in a.worlds if pair(w) != f]; te = [w for w in a.worlds if pair(w) == f]
            model, qt = fit(R[R.world.isin(tr)], Q[Q.world.isin(tr)]); outs.append(policy(R[R.world.isin(te)], Q[Q.world.isin(te)], model, qt))
        res = pd.concat(outs, ignore_index=True)
    elif a.mode == "fit":
        model, qt = fit(R, Q); json.dump(dict(model=model, q_table=qt, feats=FEATS, worlds=a.worlds), open(OUT + "_model.json", "w"), indent=1)
        meta["model_sha256"] = sha(OUT + "_model.json")
        res = policy(R, Q, model, qt)
    else:
        d = json.load(open(a.model))   # the frozen model written by --mode fit (plain JSON)
        if d["feats"] != FEATS: stop("feature list differs from the frozen model")
        meta["model_sha256"] = sha(a.model); res = policy(R, Q, d["model"], d["q_table"])
    res.to_parquet(OUT + "_queries.parquet", index=False); meta["queries_sha256"] = sha(OUT + "_queries.parquet"); meta["seconds"] = round(time.time() - t0)
    json.dump(meta, open(OUT + "_meta.json", "w"), indent=1)
    print(f"[{time.time()-t0:5.0f}s] {a.mode}: {len(res)} queries -> {OUT}_queries.parquet (no score printed; read with w135_read_s2.py)")
