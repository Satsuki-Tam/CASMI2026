"""Exploratory (not a registered test): truth rank under fixed-rule variants S = z(FP) + wg z(GL) + wp pop on the C2 lists of unseen
NP molecules, split by whether the truth is a COCONUT structure. Shows how GL / prior weights trade NP (COCONUT) truths vs tier-only truths."""
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
            i = int(np.flatnonzero(g.is_truth.values)[0]); zf, zg, pop = z(g.fp.values.astype(float)), z(glv), g.pop_public.values.astype(float)
            for wg in (0, 0.5, 1, 2, 3):
                for wp in (0, 0.25, 0.5, 1, 2):
                    S = zf + wg * zg + wp * pop; r = 1 + int((S > S[i]).sum())
                    rows.append(dict(run=run, set=s, molecule=mid, coco=bool(g.in_coconut.values[i]), wg=wg, wp=wp, rr=(1 / r if r <= 25 else 0.0)))
R = pd.DataFrame(rows)
for (s, c), g in R.groupby(["set", "coco"]):
    t = g.pivot_table(index="wg", columns="wp", values="rr", aggfunc="mean")
    print(f"== {s} truth {'COCONUT' if c else 'tier-only'} (n {g.molecule.nunique()}) MRR of S = z(FP) + wg z(GL) + wp pop (rows wg, cols wp)")
    print(t.round(3).to_string())
