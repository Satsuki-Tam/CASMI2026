"""102 exploratory (after the registered reading): variant - main by the truth's popularity rank inside the view list (pop_public desc, fp tie-break;
strata 1 / 2-3 / 4-10 / 11+ / truth absent), per layer. Descriptive only (Codex 103 Q4: popularity bias of the protection layers)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
rows = []
for tag, run in RUN_OF.items():
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str)
    for f in sorted(os.listdir(os.path.join(HERE, run))):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(HERE, run, f)); F["molecule"] = F.molecule.astype(str)
        for mid, g0 in F.groupby("molecule", sort=False):
            for view in ("c2", "c1"):
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]; tr = g.is_truth.values.astype(bool)
                if tr.any():
                    o = np.lexsort((-np.nan_to_num(g.fp.values.astype(float), nan=-1e9), -g.pop_public.values.astype(float))); pos = np.empty(len(g), int); pos[o] = np.arange(1, len(g) + 1); pr = int(pos[tr].min())
                else: pr = 0
                rows.append((tag, s, view, mid, pr))
P = pd.DataFrame(rows, columns=["tag", "set", "view", "molecule", "prank"])
A = []
for tag in RUN_OF:
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R["tag"] = tag; A.append(R)
A = pd.concat(A).merge(P, on=["tag", "set", "view", "molecule"], how="left")
A["stratum"] = pd.cut(A.prank.fillna(0), [-0.5, 0.5, 1.5, 3.5, 10.5, 1e9], labels=["absent", "1", "2-3", "4-10", "11+"])
LAY = {"panel C1 clean": (A.tag == "panel") & (A.view == "c1") & A.molecule.isin(CLEAN), "panel C2": (A.tag == "panel") & (A.view == "c2"),
       "G C1": A.tag.isin(["f1dev", "f2dev"]) & (A.view == "c1") & (A.set == "G_tims_crosslib"),
       "A 053 NP C2": A.tag.str.startswith("np053") & (A.view == "c2") & A.set.isin(["NP_H", "NP_N"]),
       "old B f1/f2 NP C2": A.tag.isin(["f1dev", "f2dev"]) & (A.view == "c2") & A.set.isin(NP)}
L = ["# 102 exploratory: variant - main by the truth's popularity rank in the view list", "", "| layer | stratum | n (share) | main | rrf_pe_0.5 | rrf_e1b_0.5 | rrf_e1r_0.5 | e1r alone |", "|---|---|---:|---:|---:|---:|---:|---:|"]
for lab, m in LAY.items():
    d = A[m]
    for st, g in d.groupby("stratum", observed=True):
        L.append(f"| {lab} | {st} | {len(g)} ({len(g) / len(d):.2f}) | {g.main.mean():.3f} | {(g.rrf_pe_0_5 if 'rrf_pe_0_5' in g else g['rrf_pe_0.5'] - g.main).mean():+.4f} | {(g['rrf_rank_e1b_0.5'] - g.main).mean():+.4f} | {(g['rrf_rank_e1r_0.5'] - g.main).mean():+.4f} | {g.rank_e1r_only.mean():.3f} |")
open(os.path.join(HERE, "diag/x102_popstrata.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
