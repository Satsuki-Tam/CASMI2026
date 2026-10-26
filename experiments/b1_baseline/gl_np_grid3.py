"""Exploratory: list-adaptive GL weight. p = share of COCONUT candidates among the GL top-10 of the list (observable, label-free).
Rule: S = z(FP) + wg(p) z(GL) + 0.5 pop with wg = w_lo if p >= theta else 2. Reports MRR by truth type and the share of lists switched."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z
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
            tr = g.is_truth.values.astype(bool); i = int(np.flatnonzero(tr)[0]); co = g.in_coconut.values.astype(bool)
            zg = z(glv); zf, pop = z(g.fp.values.astype(float)), g.pop_public.values.astype(float)
            top = np.argsort(-np.nan_to_num(glv, nan=-1e9))[:10]; p = float(co[top].mean())
            for th in (0.3, 0.5, 0.7, 1.1):
                for wlo in (0, 0.5, 1):
                    wg = wlo if p >= th else 2.0
                    S = zf + wg * zg + 0.5 * pop; r = 1 + int((S > S[i]).sum())
                    rows.append(dict(set=s, coco=bool(co[i]), th=th, wlo=wlo, p=p, rr=(1 / r if r <= 25 else 0.0)))
R = pd.DataFrame(rows)
print(R.pivot_table(index=["set", "coco"], columns=["th", "wlo"], values="rr", aggfunc="mean").round(3).to_string())
x = R[(R.wlo == 0)].groupby(["set", "coco", "th"]).p.apply(lambda s: s.mean()).unstack(); print("mean p:"); print(x.round(3))
sw = R[R.wlo == 0].groupby(["set", "coco", "th"]).apply(lambda d: (d.p >= d.th.iloc[0]).mean()).unstack(); print("share switched:"); print(sw.round(3))
