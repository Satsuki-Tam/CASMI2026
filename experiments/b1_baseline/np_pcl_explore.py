"""Exploratory (not registered): PubChemLite membership boost on the blend (no analog term), by truth type, unseen fold-1/2 dev C2 + panel C2
(panel = Enveda NP, FPNet-seen, GL MSG-contaminated: stress only). B = 2 z(learned) + z(S) (+ w * 1[PubChemLite]) on GL-covered lists."""
import os, sys
import numpy as np, pandas as pd, polars as pl, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z
from b1_rankfeats import feature_matrix
bst = lgb.Booster(model_file=os.path.join(HERE, "rank_v4b/lambdarank.txt")); FEATS = bst.feature_name()
P = pl.read_parquet(os.path.join(HERE, "../../data/external_kaggle/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet"), columns=["candidate_key", "ik14"])
PCL = set(P["candidate_key"].drop_nulls().to_list()) | set(P["ik14"].drop_nulls().to_list())
rows = []
for run, sets in [("run_f1dev", ["C_np_crosslib", "D_np_single", "G_tims_crosslib"]), ("run_f2dev", ["C_np_crosslib", "D_np_single", "G_tims_crosslib"]), ("run_panel_fe", ["P_np250"])]:
    for s in sets:
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
        M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        gl, _, _ = E.runner(os.path.join(HERE, run), s, "gl"); gl = gl or {}
        for mid in M.index:
            g = E.view_frame(F, M, mid, "c2")
            if not len(g) or not g.is_truth.any(): continue
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            if np.isfinite(glv).sum() < max(2, 0.5 * len(g)): continue
            fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g["lib_sim_c2"].values.astype(float)
            X = feature_matrix(fp, glv, np.full(len(g), np.nan), pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                               g["lib_same_c2"].values, g["lib_nref_c2"].values, g.in_tier.values, g["in_train_c2"].values, g.in_coconut.values, g.ppm_err.values,
                               g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=FEATS)
            B = 2 * z(np.asarray(bst.predict(X), float)) + z(z(fp) + 2 * z(glv) + 0.5 * pop)
            pc = np.array([k in PCL for k in g.official_key.astype(str)], float); i = int(np.flatnonzero(g.is_truth.values)[0])
            for w in (0, 0.5, 1, 2, 4):
                sc = B + w * pc; r = 1 + int((sc > sc[i]).sum())
                rows.append(dict(set=s, coco=bool(g.in_coconut.values[i]), t_pcl=bool(pc[i]), w=w, rr=(1 / r if r <= 25 else 0.0)))
R = pd.DataFrame(rows)
print(R.pivot_table(index="w", columns=["set", "coco"], values="rr", aggfunc="mean").round(3).to_string())
print(R[R.w == 0].groupby(["set", "coco"]).agg(n=("rr", "size"), truth_in_pcl=("t_pcl", "mean")).round(3).to_string())
