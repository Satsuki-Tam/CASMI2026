"""079 reading (079_prereg_v8w_ea.md): EA ea0.5w1 effect with rank_v8w_pc (diag/p079_*) vs with rank_v4b (diag/p074_*), same tables / molecules.
Interaction per molecule = (v8w+EA - v8w) - (v4b+EA - v4b). Aggregates as in 074; G C1 = f1dev / f2dev G_tims_crosslib C1 (blocks equal)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000; V = "ea0.5w1"
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule)
def load(tag):
    a = pd.read_csv(os.path.join(HERE, f"diag/p074_{tag}.csv")); b = pd.read_csv(os.path.join(HERE, f"diag/p079_{tag}.csv"))
    x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_4", "_8")); assert len(x) == len(a) == len(b), tag
    x["e4"] = x[f"{V}_4"] - x.main_4; x["e8"] = x[f"{V}_8"] - x.main_8; x["int"] = x.e8 - x.e4; x["v8"] = x[f"{V}_8"] - x.main_4   # v8w+EA vs v4b
    x["molecule"] = x.molecule.astype(str); return x
X = {t: load(t) for t in ("np053f1dev", "np053f2dev", "panel", "f1dev", "f2dev")}
def stat(frames, col):
    pts, bts = [], []
    for df, strata in frames:
        gs = [df[df.set == s][col].values for s in strata] if strata else [df[col].values]; gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs])); bts.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(bts), axis=0), [2.5, 97.5])
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
AGG = {"primary 053 NP C2 (H,N)": [(X[t][X[t].view == "c2"], ["NP_H", "NP_N"]) for t in ("np053f1dev", "np053f2dev")],
       "panel C1 clean": [(X["panel"][(X["panel"].view == "c1") & X["panel"].molecule.isin(CLEAN)], None)],
       "G C1 (f1,f2)": [(X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")], None) for t in ("f1dev", "f2dev")],
       "f1/f2 NP C2 C-F": [(X[t][X[t].view == "c2"], ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")],
       "053 NP C1": [(X[t][X[t].view == "c1"], ["NP_H", "NP_N", "NP_X"]) for t in ("np053f1dev", "np053f2dev")]}
L = ["# 079: EA (ea0.5w1) with v8w vs with v4b", "", "| aggregate | EA on v4b | EA on v8w | interaction (v8w-EA effect minus v4b-EA effect) | v8w+EA vs v4b |", "|---|---|---|---|---|"]
for nm, fr in AGG.items():
    L.append(f"| {nm} | {fmt(*stat(fr, 'e4'))} | {fmt(*stat(fr, 'e8'))} | {fmt(*stat(fr, 'int'))} | {fmt(*stat(fr, 'v8'))} |")
open(os.path.join(HERE, "diag/x079_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
