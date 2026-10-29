"""W135 stage 2 v2 (139_prereg_w135_stage2.md + 139_decision.md / Codex 139; written before any selector result): the generated-candidate selector
and ONE insertion policy.
Rows: every B product (arm both) of every query of the given worlds; label (training only) = the product's official key is the truth.
Features FEATS (observable only): product f.z, GL (released GLACIER, missing flag + 0), MetFrag-lite (b1_frag; returns 0 when not computable --
not a missing flag), parent score, parents, sources, edit steps and the five edit groups of a FIXED edit-name table (unknown edit -> STOP),
off_mass, f.z rank in B, B size; differences to P's rank-1 candidate (f.z vs fp, GL, MetFrag); rank fractions of f.z / GL among the view list +
B de-duplicated by official key (a key present in both keeps the B product's values: "B wins"); query: P's rank-1 / rank-2 score gap (GL path and
fallback scores differ in scale; used together with gl_ok), gl_ok, lib_max, list size, best analog similarity, peer structures, train parents.
Empty P (empty world window, verified n_cand 0): lib_max = gap = log_ncand = 0 and the P differences 0 with their flags; a non-empty P with a
missing required value -> STOP.
Model: weighted standardisation (row weight 1 / |B|, weighted mean / variance on the training rows) -> logistic regression (L2, C = 1.0,
max_iter 2000, same weights). STOP on a non-converged fit, a non-finite coefficient or a training set without both classes.
q table (Codex 139): P's rank-r correctness by bin (lib_max >= 0.9 / gl_ok / fallback), pooled over the training worlds as the mixture
q_r(bin) = sum_w n_{w,bin,r} / N_w / sum_w n_{w,bin} / N_w (equal world weights); an empty bin takes the q of all bins pooled.
Policy per query: x = argmax p_hat over B (ties: f.z, key); for k in 1 .. min(3, |P| + 1): G_k = p_hat / k - sum_{r=k..min(25, |P|)} q_r d_r with
d_r = 1/r - 1/(r+1) (r < 25), d_25 = 1/25; k* = argmax G_k (ties: the smaller k); insert x at k* if G_k* > 0, else keep P. (A policy built on
a rough cost approximation, not a calibrated expected utility.)
Inputs are checked before use: the world manifest (every file), the generation meta (world manifest hash, output hash, registered arguments),
the product runner input (molecules = batch, candidates = the heavy-atom-filtered B SMILES), the product GL meta (ok / partial) and coverage (a
molecule with a GL-covered query spectrum and candidates must have at least one score), B invariants (B list = B_detail keys, hash, unique,
<= 50, disjoint from P's top 25), one-to-one ids across batch / P / molecules table / generation table.
Modes: --mode cv (exactly the 18 design worlds; leave-one-pair-out over (dFj, dRj); descriptive) | --mode fit (exactly the 18 design worlds ->
<out>_model.json + <out>_freeze.json; refuses to overwrite) | --mode apply (exactly the 13 confirmation worlds with the frozen model).
Per-query outputs (<out>_queries.parquet): the policy's action / k / x / p_hat, P's top 25, the new list, RRs (truth joined after prediction).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_selector.py --mode cv --out experiments/w135/s2/cv"""
import argparse, hashlib, json, os, sys, time, warnings
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
FEATS = ["fz", "gl", "gl_miss", "frag", "apsc", "log_npar", "src_peer", "src_train", "n_steps", "e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other", "off_mass",
         "fz_rank_b", "log_nb", "d_fz_top1", "d_fz_miss", "d_gl_top1", "d_gl_miss", "d_frag_top1", "fz_rankfrac_all", "gl_rankfrac_all", "p_gap12", "gl_ok", "lib_max",
         "log_ncand", "best_analog", "n_peer_struct", "n_train"]
DESIGN = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)]
CONFIRM = [f"{b}_p{p}" for b in ("cF1", "cR1", "cF2", "cR2", "cF3", "cR3") for p in (30, 0)] + ["cU1_p30"]
EDIT_GROUP = {**{e: "e_sugar" for e in ("Hex_O", "Pen_O", "dHex_O", "GlcA_O", "Hex_C", "dHex_glyc", "dPen_glyc", "ddHex_glyc")},
              **{e: "e_methyl" for e in ("Me_O", "Me_N", "Me_c", "OMe_ar", "dMe_O", "dMe_N")},
              **{e: "e_redox" for e in ("OH_ar", "OH_al", "H2_CC", "H2_CO", "dH2_CC", "ox_CHOH", "COOH_Me", "dOH_ar", "dOH_al", "dCOOH")},
              **{e: "e_acyl" for e in ("Ac_O", "Mal_O", "Cou_O", "Caf_O", "Fer_O", "Gal_O", "dAc_O")},
              **{e: "e_other" for e in ("SO3_O", "dSO3", "Pre_c", "Pre_O", "dPre_c")}}
COV = ("[M+H]+", "[M+Na]+")   # gl_runner.COV
GEN_ARGS = dict(budget=50, n_train=10, n_peer=10, speed_only=False)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_selector): {m}")


def edit_groups(combo):
    g = dict(e_sugar=0, e_methyl=0, e_redox=0, e_acyl=0, e_other=0)
    for step in (combo or "").split("+"):
        if not step: continue
        if step not in EDIT_GROUP: stop(f"unknown edit {step}")
        g[EDIT_GROUP[step]] = 1
    return g


def _frag_job(t):
    import b1_frag as BF
    mid, smiles_list, spectra = t
    return mid, {s: float(BF.score(BF.fragments(s), spectra)) for s in smiles_list}


def check_world(wname):
    """provenance and invariants of one world; returns the world directory."""
    W = os.path.join(ROOT, "experiments/w135/worlds", wname); b, p = wname.split("_p")
    for ln in open(os.path.join(W, "manifest.txt")):
        h, f = ln.split()
        if sha(os.path.join(ROOT, f)) != h: stop(f"{wname}: {f} differs from the world manifest")
    mt = json.load(open(os.path.join(W, "gen_full_v2.meta.json"))); ar = mt["args"]
    if mt["world_manifest_sha256"] != sha(os.path.join(W, "manifest.txt")) or mt["output_sha256"] != sha(os.path.join(W, "gen_full_v2.parquet")): stop(f"{wname}: generation meta mismatch")
    if any(ar[k] != v for k, v in GEN_ARGS.items()) or ar["wclass_col"] != f"wclass_p{p}" or ar["set"] != b: stop(f"{wname}: generation arguments {ar}")
    gm = json.load(open(os.path.join(W, "prod_gl.json.meta.json")))
    if gm.get("status") not in ("ok", "partial"): stop(f"{wname}: product GL status {gm.get('status')}")
    return W


def load_world(wname, with_truth):
    """-> (rows of B products with features, per-query frame) of one checked world."""
    from b1_features import heavy_ok
    W = check_world(wname); b, p = wname.split("_p")
    G = pd.read_parquet(os.path.join(W, "gen_full_v2.parquet")); G["molecule"] = G.molecule.astype(str)
    P = pd.read_parquet(os.path.join(W, "P.parquet")); P["molecule"] = P.molecule.astype(str)
    M = pd.read_csv(os.path.join(W, f"b1_molecules_{b}.csv")); M["molecule"] = M.molecule.astype(str)
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str)
    for nm, ids in (("generation", G.molecule), ("P", P.molecule), ("molecules table", M.molecule)):
        if ids.duplicated().any() or set(ids) != set(bt.molecule): stop(f"{wname}: {nm} ids are not one-to-one with the batch")
    G = G.set_index("molecule"); P = P.set_index("molecule"); M = M.set_index("molecule"); bt = bt.set_index("molecule")
    F = pd.read_parquet(os.path.join(W, f"b1_features_{b}.parquet")); F["molecule"] = F.molecule.astype(str)
    gl = json.load(open(os.path.join(W, "work", f"gl_{b}.json"))); pgl = json.load(open(os.path.join(W, "prod_gl.json")))
    runner = {d["mid"]: d for d in json.load(open(os.path.join(W, "prod_runner_in.json")))}
    if set(runner) != set(bt.index): stop(f"{wname}: product runner molecules != batch")
    tasks = []
    for m in bt.index:
        det = json.loads(G.loc[m, "B_detail_both"]); Bl = json.loads(G.loc[m, "B_both"]); t25 = json.loads(P.loc[m, "top25"]); keys = [d[0] for d in det]
        if keys != Bl or hashlib.sha1(";".join(Bl).encode()).hexdigest()[:16] != G.loc[m, "B_hash_both"] or len(set(Bl)) != len(Bl) or len(Bl) > 50: stop(f"{wname} {m}: B invariant")
        if set(Bl) & {e[1] for e in t25}: stop(f"{wname} {m}: B intersects P's top 25")
        if runner[m]["cands"] != [d[1] for d in det if heavy_ok(d[1])]: stop(f"{wname} {m}: product runner candidates != B")
        covered = any(s.get("mode") in ("positive", 1) and s.get("adduct") in COV for s in runner[m]["spectra"])
        if covered and runner[m]["cands"] and not any(v is not None for v in (pgl.get(m) or {}).values()): stop(f"{wname} {m}: GL-covered molecule with candidates but no product score")
        if int(P.loc[m, "n_cand"]) > 0 and not t25: stop(f"{wname} {m}: non-empty list without top 25")
        sm = [d[1] for d in det] + ([t25[0][2]] if t25 else [])
        sp = [dict(mz=np.asarray(s["mz"]), it=np.asarray(s["it"]), prec=s["prec"], mode=s["mode"]) for s in runner[m]["spectra"]]
        tasks.append((m, sm, sp))
    with Pool(12) as pool_: FR = dict(pool_.map(_frag_job, tasks, chunksize=2))
    rows, qrows = [], []
    for m in bt.index:
        det = json.loads(G.loc[m, "B_detail_both"]); t25 = json.loads(P.loc[m, "top25"]); gq = gl.get(m) or {}; pq = pgl.get(m) or {}
        n_cand = int(P.loc[m, "n_cand"]); empty = n_cand == 0
        if empty:
            lib_max, gap, top_fp, top_gl, top_fr = 0.0, 0.0, np.nan, np.nan, 0.0; view = F.iloc[0:0]
        else:
            lib_max = float(M.loc[m, "lib_max_c2"])
            if not np.isfinite(lib_max): stop(f"{wname} {m}: lib_max missing for a non-empty list")
            view = F[(F.molecule == m) & F.in_short_c2.astype(bool) & (F.in_tier | F.in_coconut | F.in_train_c2).astype(bool)]
            sc = [e[3] for e in t25]; gap = float(sc[0] - sc[1]) if len(sc) >= 2 else 0.0
            tv = view[view.official_key.astype(str) == t25[0][1]]
            if not len(tv): stop(f"{wname} {m}: P rank-1 not in the view list")
            top_fp = float(tv.fp.astype(float).max()); top_gl = np.nan if gq.get(t25[0][2]) is None else float(gq[t25[0][2]]); top_fr = FR[m].get(t25[0][2], 0.0)
        an = json.loads(P.loc[m, "analogs"]); bkeys = {d[0] for d in det}
        vb = view[~view.official_key.astype(str).isin(bkeys)]   # "B wins" on duplicate keys
        db_fz = vb.fp.astype(float).values; db_fz = db_fz[np.isfinite(db_fz)]
        db_gl = np.array([np.nan if gq.get(s) is None else float(gq[s]) for s in vb.smiles], float); db_gl = db_gl[np.isfinite(db_gl)]
        fz_b = np.array([d[2] for d in det], float); gl_b = np.array([np.nan if pq.get(d[1]) is None else float(pq[d[1]]) for d in det], float)
        all_fz = np.concatenate([db_fz, fz_b]); all_gl = np.concatenate([db_gl, gl_b[np.isfinite(gl_b)]])
        q = dict(world=wname, batch=b, pi=int(p), molecule=m, fam=int(bt.loc[m, "fam"]), wclass=str(bt.loc[m, f"wclass_p{p}"]), used=bool(bt.loc[m, "used"]),
                 top25=json.dumps([e[1] for e in t25]), gl_ok=int(P.loc[m, "gl_ok"]), lib_max=lib_max, n_cand=n_cand, n_b=len(det), truth_in_B=bool(G.loc[m, "reach_both"]) if with_truth else None)
        q["bin"] = "lib" if lib_max >= 0.9 else ("gl" if q["gl_ok"] else "fb"); qrows.append(q)
        for i, d in enumerate(det):
            key, smi, fz, apsc, npar, srcs, combo, loc, off = d; g_ = gl_b[i]; fr = FR[m].get(smi, 0.0)
            rows.append(dict(world=wname, molecule=m, key=key, fz=fz, gl=0.0 if not np.isfinite(g_) else g_, gl_miss=int(not np.isfinite(g_)), frag=fr, apsc=apsc, log_npar=np.log1p(npar),
                             src_peer=int("peer" in srcs), src_train=int("train" in srcs), n_steps=(combo or "").count("+") + 1, off_mass=int(bool(off)),
                             fz_rank_b=(i + 1) / len(det), log_nb=np.log1p(len(det)), d_fz_top1=(fz - top_fp) if np.isfinite(top_fp) else 0.0, d_fz_miss=int(not np.isfinite(top_fp)),
                             d_gl_top1=(g_ - top_gl) if (np.isfinite(g_) and np.isfinite(top_gl)) else 0.0, d_gl_miss=int(not (np.isfinite(g_) and np.isfinite(top_gl))), d_frag_top1=fr - top_fr,
                             fz_rankfrac_all=float((all_fz > fz).sum()) / len(all_fz), gl_rankfrac_all=(float((all_gl > g_).sum()) / len(all_gl)) if np.isfinite(g_) else 1.0,
                             p_gap12=gap, gl_ok=q["gl_ok"], lib_max=lib_max, log_ncand=np.log1p(n_cand), best_analog=float(an[0][1]) if an else 0.0,
                             n_peer_struct=int(G.loc[m, "n_peer_struct"]), n_train=int(G.loc[m, "n_train"]), w=1.0 / len(det), **edit_groups(combo)))
    R = pd.DataFrame(rows, columns=["world", "molecule", "key", "w"] + FEATS); Q = pd.DataFrame(qrows)
    if len(R) and not np.isfinite(R[FEATS].values.astype(float)).all(): stop(f"{wname}: non-finite feature")
    if with_truth:
        T = bt["scorer_key"].astype(str).to_dict(); Q["truth"] = Q.molecule.map(T); R["y"] = (R.key == R.molecule.map(T)).astype(int)
    return R, Q


def q_table(Q):
    """mixture over the training worlds (equal weights, N_w = queries of world w); empty bin -> all bins pooled."""
    def est(Qb_by_w):
        num = np.zeros(25); den = 0.0
        for w, (Qb, N) in Qb_by_w.items():
            for t, top in zip(Qb.truth, Qb.top25):
                tl = json.loads(top)
                if t in tl: num[tl.index(t)] += 1.0 / N
            den += len(Qb) / N
        return (num / den).tolist() if den > 0 else None
    allq = est({w: (g, len(g)) for w, g in Q.groupby("world")}); out = {}
    for bn in ("lib", "gl", "fb"):
        v = est({w: (g[g["bin"] == bn], len(g)) for w, g in Q.groupby("world") if (g["bin"] == bn).any()}); out[bn] = v if v is not None else allq
    return out


def predict(R, model):
    if not len(R): return np.zeros(0)
    Z = (R[FEATS].values.astype(float) - np.asarray(model["mean"])) / np.asarray(model["scale"])
    return 1.0 / (1.0 + np.exp(-(Z @ np.asarray(model["coef"]) + model["intercept"])))


def policy(R, Q, model, qt):
    R = R.copy(); R["p"] = predict(R, model)
    best = (R.sort_values(["world", "molecule", "p", "fz", "key"], ascending=[True, True, False, False, True]).groupby(["world", "molecule"]).head(1).set_index(["world", "molecule"])
            if len(R) else pd.DataFrame(columns=["p", "key"]))
    out = []
    for q in Q.itertuples(index=False):
        top = json.loads(q.top25); act, kstar, ph, xk = "keep", 0, float("nan"), ""
        if (q.world, q.molecule) in best.index:
            x = best.loc[(q.world, q.molecule)]; ph = float(x["p"]); xk = str(x["key"]); qq = qt[q.bin]; G = []
            for k in range(1, min(3, len(top) + 1) + 1):
                loss = sum(qq[r - 1] * ((1.0 / r - 1.0 / (r + 1)) if r < 25 else 1.0 / 25) for r in range(k, min(25, len(top)) + 1))
                G.append(ph / k - loss)
            kb = int(np.argmax(G))   # first maximum = the smaller k
            if G[kb] > 0: act, kstar = "insert", kb + 1
        new = (top[:kstar - 1] + [xk] + top[kstar - 1:])[:25] if act == "insert" else top[:25]
        out.append(dict(world=q.world, batch=q.batch, pi=q.pi, molecule=q.molecule, fam=q.fam, wclass=q.wclass, used=q.used, bin=q.bin, n_b=q.n_b, n_cand=q.n_cand,
                        action=act, k=kstar, p_hat=ph, x_key=xk, top25=json.dumps(top), new25=json.dumps(new)))
    res = pd.DataFrame(out)
    if "truth" in Q.columns:   # truth joined after the predictions
        T = dict(zip(zip(Q.world, Q.molecule), Q.truth)); TB = dict(zip(zip(Q.world, Q.molecule), Q.truth_in_B))
        res["truth"] = [T[(w, m)] for w, m in zip(res.world, res.molecule)]; res["truth_in_B"] = [TB[(w, m)] for w, m in zip(res.world, res.molecule)]
        rr = lambda lst, t: next((1.0 / (i + 1) for i, k in enumerate(json.loads(lst)[:25]) if k == t), 0.0)
        res["rrP"] = [rr(a_, t) for a_, t in zip(res.top25, res.truth)]; res["rr"] = [rr(a_, t) for a_, t in zip(res.new25, res.truth)]; res["x_is_truth"] = (res.x_key == res.truth).astype(int)
    return res


def fit(R, Q):
    from sklearn.linear_model import LogisticRegression
    X = R[FEATS].values.astype(float); y = R.y.values.astype(int); w = R.w.values.astype(float)
    if y.sum() == 0 or y.sum() == len(y): stop("training rows without both classes")
    mu = (w[:, None] * X).sum(0) / w.sum(); var = (w[:, None] * (X - mu) ** 2).sum(0) / w.sum(); scale = np.where(var > 0, np.sqrt(var), 1.0)
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        try: clf = LogisticRegression(C=1.0, max_iter=2000).fit((X - mu) / scale, y, sample_weight=w)
        except Warning as e_: stop(f"logistic fit warning: {e_}")
    if clf.n_iter_[0] >= 2000 or not np.isfinite(clf.coef_).all() or not np.isfinite(clf.intercept_).all(): stop("logistic fit not converged / non-finite")
    return dict(mean=mu.tolist(), scale=scale.tolist(), coef=clf.coef_[0].tolist(), intercept=float(clf.intercept_[0])), q_table(Q)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", required=True, choices=["cv", "fit", "apply"]); ap.add_argument("--model", default=""); ap.add_argument("--out", required=True)
    a = ap.parse_args(); t0 = time.time()
    OUT = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out); os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for suf in ("_queries.parquet", "_model.json", "_freeze.json"):
        if os.path.exists(OUT + suf): stop(f"{OUT}{suf} exists (no overwrite)")
    worlds = CONFIRM if a.mode == "apply" else DESIGN
    Rs, Qs = [], []
    for w in worlds:
        R, Q = load_world(w, with_truth=True); Rs.append(R); Qs.append(Q)
        print(f"[{time.time()-t0:5.0f}s] {w}: {len(Q)} queries, {len(R)} product rows", flush=True)
    R = pd.concat(Rs, ignore_index=True); Q = pd.concat(Qs, ignore_index=True)
    meta = dict(mode=a.mode, worlds=worlds, feats=FEATS, script_sha256=sha(os.path.abspath(__file__)), b1_frag_sha256=sha(os.path.join(B, "b1_frag.py")),
                inputs={w: dict(gen=sha(os.path.join(ROOT, "experiments/w135/worlds", w, "gen_full_v2.parquet")), prod_gl=sha(os.path.join(ROOT, "experiments/w135/worlds", w, "prod_gl.json")),
                                world_manifest=sha(os.path.join(ROOT, "experiments/w135/worlds", w, "manifest.txt"))) for w in worlds})
    if a.mode == "cv":
        pair = lambda w: w.split("_p")[0][-1]; outs = []
        for f in sorted({pair(w) for w in worlds}):
            tr = [w for w in worlds if pair(w) != f]; te = [w for w in worlds if pair(w) == f]
            if set(tr) & set(te): stop("cv fold overlap")
            model, qt = fit(R[R.world.isin(tr)], Q[Q.world.isin(tr)])
            Qte = Q[Q.world.isin(te)]; outs.append(policy(R[R.world.isin(te)], Qte.drop(columns=["truth", "truth_in_B"]).assign(truth=Qte.truth.values, truth_in_B=Qte.truth_in_B.values), model, qt))
        res = pd.concat(outs, ignore_index=True)
    elif a.mode == "fit":
        model, qt = fit(R, Q); md = dict(model=model, q_table=qt, feats=FEATS, worlds=worlds, edit_group=EDIT_GROUP)
        json.dump(md, open(OUT + "_model.json", "w"), indent=1); meta["model_sha256"] = sha(OUT + "_model.json")
        meta["n_rows"] = int(len(R)); meta["n_pos_rows"] = int(R.y.sum()); meta["n_pos_identities"] = int(R[R.y == 1].molecule.nunique())
        json.dump(meta, open(OUT + "_freeze.json", "w"), indent=1)
        res = policy(R, Q, model, qt)
    else:
        md = json.load(open(a.model)); fz = json.load(open(a.model.replace("_model.json", "_freeze.json")))
        if md["feats"] != FEATS or md["edit_group"] != EDIT_GROUP or sha(a.model) != fz["model_sha256"]: stop("frozen model / feature definition mismatch")
        if set(md["worlds"]) & set(worlds): stop("apply worlds overlap the training worlds")
        meta["model_sha256"] = sha(a.model); meta["freeze_sha256"] = sha(a.model.replace("_model.json", "_freeze.json"))
        res = policy(R, Q.drop(columns=["truth", "truth_in_B"]).assign(truth=Q.truth.values, truth_in_B=Q.truth_in_B.values), md["model"], md["q_table"])
    res.to_parquet(OUT + "_queries.parquet", index=False); meta["queries_sha256"] = sha(OUT + "_queries.parquet"); meta["seconds"] = round(time.time() - t0)
    json.dump(meta, open(OUT + "_meta.json", "w"), indent=1)
    print(f"[{time.time()-t0:5.0f}s] {a.mode}: {len(res)} queries -> {OUT}_queries.parquet (no score printed)")
