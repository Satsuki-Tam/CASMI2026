"""Exploratory: is GLACIER biased against COCONUT (NP) candidates within a list? (a) mean GL z of COCONUT vs tier-only DECOYS per list;
(b) truth MRR when GL is z-scored WITHIN the candidate's source group (COCONUT / not) instead of over the whole list."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z
rows, bias = [], []
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
            tr = g.is_truth.values.astype(bool); i = int(np.flatnonzero(tr)[0]); co = g.in_coconut.values.astype(bool)
            zg = z(glv); dec = ~tr
            if (dec & co).sum() >= 3 and (dec & ~co).sum() >= 3: bias.append(dict(set=s, coco_truth=bool(co[i]), d=float(np.nanmean(zg[dec & co]) - np.nanmean(zg[dec & ~co]))))
            zgg = np.full(len(g), np.nan)
            for msk in (co, ~co):
                if msk.sum() >= 2: zgg[msk] = z(glv[msk])
                elif msk.sum() == 1: zgg[msk] = 0.0
            zf, pop = z(g.fp.values.astype(float)), g.pop_public.values.astype(float)
            for name, zz in (("list", zg), ("group", np.nan_to_num(zgg, nan=np.nanmin(zgg) if np.isfinite(zgg).any() else 0.0))):
                for wg in (1, 2):
                    for wp in (0.25, 0.5):
                        S = zf + wg * zz + wp * pop; r = 1 + int((S > S[i]).sum())
                        rows.append(dict(set=s, coco=bool(co[i]), z=name, wg=wg, wp=wp, rr=(1 / r if r <= 25 else 0.0)))
B = pd.DataFrame(bias); print("mean GL z of COCONUT decoys minus tier-only decoys (per list):"); print(B.groupby(["set", "coco_truth"]).d.agg(["mean", "median", "size"]).round(3))
R = pd.DataFrame(rows); print(R.pivot_table(index=["set", "coco"], columns=["z", "wg", "wp"], values="rr", aggfunc="mean").round(3).to_string())
