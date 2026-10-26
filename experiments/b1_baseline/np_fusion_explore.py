"""Exploratory (not registered): blend variants of the main output WITHOUT the analog term, on unseen fold-1/2 dev C2 lists with GL cover,
by truth type (COCONUT = NP chemistry, like the hidden test / panel 99.6%; tier-only = mostly drug-like / synthetic).
B = a * z(learned rank_v4b) + z(S), S = z(FP) + wg z(GL) + wp pop."""
import os, sys
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z
from b1_rankfeats import feature_matrix
bst = lgb.Booster(model_file=os.path.join(HERE, "rank_v4b/lambdarank.txt")); FEATS = bst.feature_name()
VAR = [("a2_wg2_wp0.5", 2, 2, 0.5), ("a2_wg1_wp0.5", 2, 1, 0.5), ("a2_wg0.5_wp0.5", 2, 0.5, 0.5), ("a2_wg1_wp1", 2, 1, 1), ("a2_wg0_wp0.5", 2, 0, 0.5),
       ("a1_wg1_wp0.5", 1, 1, 0.5), ("a1_wg0.5_wp1", 1, 0.5, 1), ("a0_wg2_wp0.5", 0, 2, 0.5), ("a0_wg0.5_wp0.5", 0, 0.5, 0.5), ("learned", None, 0, 0)]
rows = []
for run in ["run_f1dev", "run_f2dev"]:
    for s in ["C_np_crosslib", "D_np_single", "G_tims_crosslib"]:
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
            L = z(np.asarray(bst.predict(X), float)); zf, zg = z(fp), z(glv); i = int(np.flatnonzero(g.is_truth.values)[0])
            for name, a_, wg, wp in VAR:
                sc = L if a_ is None else a_ * L + z(zf + wg * zg + wp * pop)
                r = 1 + int((sc > sc[i]).sum()); rows.append(dict(run=run, set=s, coco=bool(g.in_coconut.values[i]), var=name, rr=(1 / r if r <= 25 else 0.0)))
R = pd.DataFrame(rows)
T = R.pivot_table(index="var", columns=["set", "coco"], values="rr", aggfunc="mean")
n = R[R["var"] == "learned"].groupby(["set", "coco"]).size()
print("n:", n.to_dict()); print(T.round(3).to_string())
