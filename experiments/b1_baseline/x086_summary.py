"""086 EAc diagnostic reading (086_prereg_eac.md): eac0.5w1 vs ea0.5w1 vs main on the v7f main (and the 0.379 main on 053 dev)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule)
def load(t):
    p = os.path.join(HERE, f"diag/e086_{t}.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p); d["molecule"] = d.molecule.astype(str); d["eac0.5w1"] = d["eac0.5w1"].fillna(0.0) if "eac0.5w1" in d else np.nan; return d
def stat(frames, a, b):
    pts, bts = [], []
    for df, strata in frames:
        gs = [(df[df.set == s][b] - df[df.set == s][a]).values for s in strata] if strata else [(df[b] - df[a]).values]; gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs])); bts.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(bts), axis=0), [2.5, 97.5])
fmt = lambda r: f"{r[0]:+.4f} [{r[1][0]:+.4f}, {r[1][1]:+.4f}]"
L = ["# 086 EAc diagnostic", ""]
for m in ("v7f", "v4b"):
    X = {t: load(f"{m}_{t}") for t in ("np053f1dev", "np053f2dev", "panel", "f1dev", "f2dev")}
    if X["np053f1dev"] is None or X["np053f2dev"] is None: continue
    prim = [(X[t][X[t].view == "c2"], ["NP_H", "NP_N"]) for t in ("np053f1dev", "np053f2dev")]
    c1np = [(X[t][X[t].view == "c1"], ["NP_H", "NP_N", "NP_X"]) for t in ("np053f1dev", "np053f2dev")]
    L += [f"## {m} main", "", "| aggregate | EA - main | EAc - main | EAc - EA |", "|---|---|---|---|"]
    rows = [("053 NP C2 (H,N) primary", prim), ("053 NP C1 (cost)", c1np)]
    if X["panel"] is not None: rows.append(("panel C1 clean", [(X["panel"][(X["panel"].view == "c1") & X["panel"].molecule.isin(CLEAN)], None)]))
    if X["f1dev"] is not None and X["f2dev"] is not None:
        rows.append(("G C1 (f1,f2)", [(X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")], None) for t in ("f1dev", "f2dev")]))
        rows.append(("f1/f2 NP C2 C-F", [(X[t][X[t].view == "c2"], ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")]))
        rows.append(("f1/f2 NP C1 C/E/F", [(X[t][X[t].view == "c1"], ["C_np_crosslib", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")]))
    for nm, fr in rows:
        L.append(f"| {nm} | {fmt(stat(fr, 'main', 'ea0.5w1'))} | {fmt(stat(fr, 'main', 'eac0.5w1'))} | {fmt(stat(fr, 'ea0.5w1', 'eac0.5w1'))} |")
    p_ea = stat(prim, "main", "ea0.5w1")[0]; p_eac = stat(prim, "main", "eac0.5w1")[0]
    L.append(f"\nC2 retention (EAc gain / EA gain on the primary): {p_eac / p_ea if p_ea else float('nan'):.3f}\n")
open(os.path.join(HERE, "diag/x086_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
