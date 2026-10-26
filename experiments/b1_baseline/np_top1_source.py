"""Exploratory: for C2 lists of unseen fold-1/2 dev molecules (GL-covered), which source wins rank 1 when the truth does not?
blend = 2 z(learned rank_v4b) + z(S) (no analog term). Split by truth type (COCONUT NP vs non-NP)."""
import os, sys
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z
from b1_rankfeats import feature_matrix
bst = lgb.Booster(model_file=os.path.join(HERE, "rank_v4b/lambdarank.txt")); FEATS = bst.feature_name()
rows = []
for run in ["run_f1dev", "run_f2dev"]:
    for s in ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]:
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
        M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        gl, _, _ = E.runner(os.path.join(HERE, run), s, "gl"); gl = gl or {}
        for mid in M.index:
            g = E.view_frame(F, M, mid, "c2")
            if not len(g) or not g.is_truth.any(): continue
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g["lib_sim_c2"].values.astype(float)
            ok = np.isfinite(glv).sum() >= max(2, 0.5 * len(g))
            if ok:
                X = feature_matrix(fp, glv, np.full(len(g), np.nan), pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                   g["lib_same_c2"].values, g["lib_nref_c2"].values, g.in_tier.values, g["in_train_c2"].values, g.in_coconut.values, g.ppm_err.values,
                                   g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=FEATS)
                sc = 2 * z(np.asarray(bst.predict(X), float)) + z(z(fp) + 2 * z(glv) + 0.5 * pop)
            else: sc = z(fp) + 0.5 * pop
            tr = g.is_truth.values.astype(bool); i = int(np.flatnonzero(tr)[0]); co = g.in_coconut.values.astype(bool)
            o = np.argsort(-sc, kind="stable"); r = int(np.flatnonzero(o == i)[0]) + 1; t1 = o[0]
            rows.append(dict(set=s, gl=ok, coco_truth=bool(co[i]), rank=r, top1_coco=bool(co[t1]), n=len(g), n_coco=int(co.sum()), top1_pop=float(pop[t1]), truth_pop=float(pop[i])))
R = pd.DataFrame(rows); R["miss"] = R["rank"] > 1
print(R.groupby(["coco_truth", "gl"]).agg(n=("rank", "size"), top1=("miss", lambda s: 1 - s.mean()), coco_share_list=("n_coco", "sum")).round(3))
x = R[R.miss]; print("when the truth misses rank 1: share of rank-1 winners that are COCONUT structures")
print(x.groupby(["coco_truth", "gl"]).agg(n=("rank", "size"), winner_coco=("top1_coco", "mean"), winner_pop_med=("top1_pop", "median"), truth_pop_med=("truth_pop", "median")).round(3))
print("list composition: median share of COCONUT candidates", R.groupby("coco_truth").apply(lambda d: (d.n_coco / d.n).median()).round(3).to_dict())
