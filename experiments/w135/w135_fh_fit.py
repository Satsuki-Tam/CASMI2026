"""153 FH v0 fit / apply (153 registration; written before any FH number is read).
Inputs: experiments/w135/fh/U_<world>.parquet + Q_<world>.parquet (w135_fh.py), checked against U_<world>.meta.json.
Arms (same worlds, rules and capacity): db = U restricted to P's top-25 rows (a learned re-ranking of P's own list: the connection control);
gen = P's top-25 + the generated products B (the S3 candidate). P = P's own order (rP), the frozen control.
Features (observable only; per query, computed inside the arm's U):
  candidate : is_gen, in_wwin (P rows 1; products: the generator's location is in the world window), p_empty (no P row), rP/25 (26/25 for products), sP_z (z of P's score among P rows; 0 for products) + sP_miss, fz, gl + gl_miss, frag,
              fz / gl / frag rank fractions in U (gl among non-missing; missing -> 1), differences to P's rank-1 (fz, gl (+ miss), frag),
              apsc, log_npar, src_peer, src_train, n_steps, off_mass, five edit groups;
  query     : p_gap12, gl_ok, lib_max, log_ncand (P's wide view list size), best_analog, n_peer_struct, n_train, log1p(|B|), log1p(|P|) -- the same
              query summary in both arms (Codex 153).
Model: LightGBM binary, fixed PARAMS / ROUNDS; row weight = 1/|U(q)| x 1/(number of training worlds containing the query's identity).
Final list: U sorted by the head's score (ties: rP, key), first 25.
Two-way cross (153): --train design --test confirm, and --train confirm --test design. The truth is used for labels and for the RR after
prediction only. Writes <out>_queries.parquet (per query: P / db / gen top-25 keys and RRs) + <out>_meta.json; prints no summary.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_fh_fit.py --train design --test confirm --out experiments/w135/fh/x153_d2c"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
import w135_selector as S

FHD = os.path.join(ROOT, "experiments/w135/fh")
EDITS = ["e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other"]
FEATS = ["is_gen", "in_wwin", "p_empty", "rP_frac", "sP_z", "sP_miss", "fz", "gl", "gl_miss", "frag", "fz_rf", "gl_rf", "frag_rf", "d_fz_top1", "d_gl_top1", "d_gl_miss",
         "d_frag_top1", "apsc", "log_npar", "src_peer", "src_train", "n_steps", "off_mass"] + EDITS + \
        ["p_gap12", "gl_ok", "lib_max", "log_ncand", "best_analog", "n_peer_struct", "n_train", "log_nb", "log_np"]
PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=15, max_depth=-1, min_data_in_leaf=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
              lambda_l2=1.0, verbose=-1, seed=7, num_threads=8, deterministic=True, force_col_wise=True)
ROUNDS = 300
# Codex 153: fit and the primary comparison on the pi 0 / 0.3 worlds common to both sides (12 each); d-side pi 0.6 and cU1_p30 are applied
# (descriptive) but never fitted on
SETS = dict(design=[w for w in S.DESIGN if not w.endswith("_p60")], confirm=[w for w in S.CONFIRM if w != "cU1_p30"])
EXTRA = dict(design=[w for w in S.DESIGN if w.endswith("_p60")], confirm=["cU1_p30"])
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_fh_fit): {m}")


def load(worlds):
    Us, Qs = [], []
    for w in worlds:
        mt = json.load(open(os.path.join(FHD, f"U_{w}.meta.json")))
        if sha(os.path.join(FHD, f"U_{w}.parquet")) != mt["U_sha256"] or sha(os.path.join(FHD, f"Q_{w}.parquet")) != mt["Q_sha256"]: stop(f"{w}: U / Q differ from the meta")
        Wd = os.path.join(ROOT, "experiments/w135/worlds", w)
        if sha(os.path.join(Wd, "P.parquet")) != mt["inputs"]["P"] or sha(os.path.join(Wd, "gen_full_v2.parquet")) != mt["inputs"]["gen"]: stop(f"{w}: world inputs changed")
        U = pd.read_parquet(os.path.join(FHD, f"U_{w}.parquet")); Q = pd.read_parquet(os.path.join(FHD, f"Q_{w}.parquet"))
        if set(U.molecule) - set(Q.molecule): stop(f"{w}: U molecules outside Q")
        Us.append(U); Qs.append(Q)
    return pd.concat(Us, ignore_index=True), pd.concat(Qs, ignore_index=True)


def featurize(U, Q, arm):
    """per-query features inside the arm's U; returns the arm's rows with FEATS."""
    R = U[U.src == "P"].copy() if arm == "db" else U.copy()
    qf = Q.set_index(["world", "molecule"])
    out = []
    for (w, m), g in R.groupby(["world", "molecule"], sort=False):
        g = g.copy(); q = qf.loc[(w, m)]
        g["rP_frac"] = g.rP / 25.0
        pm = g.src == "P"
        if pm.any():
            s = g.loc[pm, "sP"].astype(float); sd = s.std(ddof=0)
            g["sP_z"] = 0.0; g.loc[pm, "sP_z"] = (s - s.mean()) / sd if sd > 0 else 0.0
            top = g[pm].sort_values("rP").iloc[0]; tfz, tgl, tgm, tfr = float(top.fz), float(top.gl), int(top.gl_miss), float(top.frag)
        else:
            g["sP_z"] = 0.0; tfz, tgl, tgm, tfr = np.nan, np.nan, 1, 0.0
        n = len(g)
        g["fz_rf"] = [(g.fz.values > v).sum() / n for v in g.fz.values]
        glv = g.gl.values.astype(float); glm = g.gl_miss.values.astype(bool); ng = max(1, int((~glm).sum()))
        g["gl_rf"] = [((glv[~glm] > v).sum() / ng) if not mm else 1.0 for v, mm in zip(glv, glm)]
        g["frag_rf"] = [(g.frag.values > v).sum() / n for v in g.frag.values]
        g["d_fz_top1"] = (g.fz - tfz) if np.isfinite(tfz) else 0.0
        both = (~glm) & (tgm == 0) & np.isfinite(tgl)
        g["d_gl_top1"] = np.where(both, glv - (tgl if np.isfinite(tgl) else 0.0), 0.0); g["d_gl_miss"] = (~both).astype(int)
        g["d_frag_top1"] = g.frag - tfr
        for k in ("p_gap12", "gl_ok", "lib_max", "log_ncand", "best_analog", "n_peer_struct", "n_train"): g[k] = float(q[k])
        g["log_nb"] = float(np.log1p(q["n_b"])); g["log_np"] = float(np.log1p(q["n_p"])); g["p_empty"] = int(q["n_p"] == 0)   # same query summary in both arms (Codex 153)
        g["nU"] = n
        out.append(g)
    R = pd.concat(out, ignore_index=True) if out else R.iloc[0:0]
    if len(R) and not np.isfinite(R[FEATS].values.astype(float)).all(): stop(f"{arm}: non-finite feature")
    return R


def weights(R, Q):
    """1/|U(q)| x 1/(number of worlds of this set that contain the identity)."""
    nw = Q.groupby("molecule").world.nunique()
    return (1.0 / R.nU.values) * (1.0 / R.molecule.map(nw).values.astype(float))


def rank_lists(R, scores):
    R = R.assign(s=scores)
    R = R.sort_values(["world", "molecule", "s", "rP", "key"], ascending=[True, True, False, True, True])
    return {k: g.key.tolist()[:25] for k, g in R.groupby(["world", "molecule"], sort=False)}


if __name__ == "__main__":
    import lightgbm as lgb
    ap = argparse.ArgumentParser(); ap.add_argument("--train", required=True, choices=list(SETS)); ap.add_argument("--test", required=True, choices=list(SETS))
    ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time()
    if a.train == a.test: stop("train and test sets must differ")
    OUT = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    for suf in ("_queries.parquet", "_meta.json"):
        if os.path.exists(OUT + suf): stop(f"{OUT}{suf} exists (no overwrite)")
    Utr, Qtr = load(SETS[a.train]); Ute, Qte = load(SETS[a.test] + EXTRA[a.test])
    if set(Qtr.molecule) & set(Qte.molecule): stop("train / test identities overlap")
    res = Qte[["world", "batch", "pi", "molecule", "fam", "wclass", "used", "n_b", "n_p", "n_cand", "truth"]].copy()
    # P's own order (control)
    P_lists = {k: g.sort_values("rP").key.tolist()[:25] for k, g in Ute[Ute.src == "P"].groupby(["world", "molecule"], sort=False)}
    res["top25_P"] = [json.dumps(P_lists.get((w, m), [])) for w, m in zip(res.world, res.molecule)]
    meta = dict(train=a.train, test=a.test, train_worlds=SETS[a.train], test_worlds=SETS[a.test] + EXTRA[a.test], feats=FEATS, params=PARAMS, rounds=ROUNDS,
                script_sha256=sha(os.path.abspath(__file__)), fh_builder_sha256=sha(os.path.join(HERE, "w135_fh.py")),
                inputs={w: json.load(open(os.path.join(FHD, f"U_{w}.meta.json")))["U_sha256"] for w in SETS[a.train] + SETS[a.test] + EXTRA[a.test]})
    for arm in ("db", "gen"):
        Rtr = featurize(Utr, Qtr, arm); Rte = featurize(Ute, Qte, arm)
        y = Rtr.y.values.astype(int); wtr = weights(Rtr, Qtr)
        pos = Rtr[Rtr.y == 1]; qk = set(zip(Rtr.world, Rtr.molecule)); fam = Qtr.set_index(["world", "molecule"])
        wcl = dict(zip(zip(Qtr.world, Qtr.molecule), Qtr.wclass))   # the class is per (world, identity): the same identity changes class across pi
        meta[f"{arm}_train_desc"] = dict(groups=int(len(Qtr)), groups_with_rows=len(qk), empty_groups=int(len(Qtr) - len(qk)), pos_rows_P=int((pos.src == "P").sum()),
                                          pos_rows_B=int((pos.src == "B").sum()), pos_identities_P=int(pos[pos.src == "P"].molecule.nunique()),
                                          pos_identities_B=int(pos[pos.src == "B"].molecule.nunique()),
                                          pos_families_B=int(len({(fam.loc[(w_, m_), "batch"], fam.loc[(w_, m_), "fam"]) for w_, m_ in zip(pos[pos.src == "B"].world, pos[pos.src == "B"].molecule)})),
                                          class_weight={c: round(float(wtr[np.array([wcl[(w_, m_)] for w_, m_ in zip(Rtr.world, Rtr.molecule)]) == c].sum()), 3) for c in ("C1", "C2", "C3")})
        print(f"[{time.time()-t0:5.0f}s] {arm} training set: {meta[arm + '_train_desc']}", flush=True)
        if y.sum() == 0 or y.sum() == len(y): stop(f"{arm}: training rows without both classes")
        bst = lgb.train(PARAMS, lgb.Dataset(Rtr[FEATS].values.astype(float), y, weight=wtr, feature_name=FEATS), num_boost_round=ROUNDS)
        p = bst.predict(Rte[FEATS].values.astype(float))
        if not np.isfinite(p).all(): stop(f"{arm}: non-finite prediction")
        L = rank_lists(Rte, p)
        res[f"top25_{arm}"] = [json.dumps(L.get((w, m), [])) for w, m in zip(res.world, res.molecule)]
        mp = OUT + f"_{arm}_model.txt"; bst.save_model(mp)
        meta[f"{arm}_model_sha256"] = sha(mp); meta[f"{arm}_n_train_rows"] = int(len(Rtr)); meta[f"{arm}_n_train_pos"] = int(y.sum())
        meta[f"{arm}_n_train_pos_identities"] = int(Rtr[Rtr.y == 1].molecule.nunique())
        print(f"[{time.time()-t0:5.0f}s] {arm}: trained on {len(Rtr)} rows, applied to {len(Rte)} rows", flush=True)
    rr = lambda lst, t: next((1.0 / (i + 1) for i, k in enumerate(json.loads(lst)[:25]) if k == t), 0.0)
    for arm in ("P", "db", "gen"):
        res[f"rr_{arm}"] = [rr(l_, t) for l_, t in zip(res[f"top25_{arm}"], res.truth)]
    res.to_parquet(OUT + "_queries.parquet", index=False); meta["queries_sha256"] = sha(OUT + "_queries.parquet"); meta["seconds"] = round(time.time() - t0)
    json.dump(meta, open(OUT + "_meta.json", "w"), indent=1)
    print(f"[{time.time()-t0:5.0f}s] {len(res)} test queries -> {OUT}_queries.parquet (no score printed)")
