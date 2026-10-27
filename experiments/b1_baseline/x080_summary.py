"""080 development reading (080_prereg_v7f_ea.md): (v7f main + ea0.5w1) - v7f main from gen_eval2pv (diag/v080_*), with the 074 v4b effect
for the interaction. Gate to the 053 conf: primary >= +0.005, panel C1 clean and f1/f2 G C1 lower > -0.01, f1/f2 NP C2 not harm (U >= -0.01)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000; V = "ea0.5w1"
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule)
TAGS = ("np053f1dev", "np053f2dev", "panel", "f1dev", "f2dev", "p2dev")
def load(pref, tag):
    p = os.path.join(HERE, f"diag/{pref}_{tag}.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p); d["molecule"] = d.molecule.astype(str); d["d"] = d[V] - d.main; assert not d[[V, "main"]].isna().any().any(); return d
V7 = {t: load("v080", t) for t in TAGS}; V4 = {t: load("p074", t) for t in TAGS}
def stat(frames):
    pts, bts = [], []
    for df, strata in frames:
        gs = [df[df.set == s].d.values for s in strata] if strata else [df.d.values]; gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs])); bts.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(bts), axis=0), [2.5, 97.5])
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
def agg(X):
    if any(X[t] is None for t in TAGS[:5]): return None
    return {"primary 053 NP C2 (H,N)": stat([(X[t][X[t].view == "c2"], ["NP_H", "NP_N"]) for t in ("np053f1dev", "np053f2dev")]),
            "panel C1 clean": stat([(X["panel"][(X["panel"].view == "c1") & X["panel"].molecule.isin(CLEAN)], None)]),
            "G C1 (f1,f2)": stat([(X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")], None) for t in ("f1dev", "f2dev")]),
            "f1/f2 NP C2 C-F": stat([(X[t][X[t].view == "c2"], ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")]),
            "053 NP C1 (stress)": stat([(X[t][X[t].view == "c1"], ["NP_H", "NP_N", "NP_X"]) for t in ("np053f1dev", "np053f2dev")]),
            "dev2 NP C2 (stress)": stat([(X["p2dev"][X["p2dev"].view == "c2"], ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"])]) if X["p2dev"] is not None else (np.nan, (np.nan, np.nan))}
A7, A4 = agg(V7), agg(V4)
L = ["# 080 development: EA (ea0.5w1) on the v7f main vs on the v4b main (074)", "", "| aggregate | EA on v7f (080) | EA on v4b (074) |", "|---|---|---|"]
for k in A7: L.append(f"| {k} | {fmt(*A7[k])} | {fmt(*A4[k]) if A4 else 'n/a'} |")
mains = {t: (V7[t].main.mean(), V4[t].main.mean()) for t in TAGS if V7[t] is not None and V4[t] is not None}
L += ["", "v7f main vs v4b main (mean RR over all rows, sanity of the v7f reproduction): " + "; ".join(f"{t} {a:.4f} vs {b:.4f}" for t, (a, b) in mains.items())]
p, ci = A7["primary 053 NP C2 (H,N)"]; pc = A7["panel C1 clean"][1]; gc = A7["G C1 (f1,f2)"][1]; fc = A7["f1/f2 NP C2 C-F"][1]
gate = (p >= 0.005) and (pc[0] > -0.01) and (gc[0] > -0.01) and (fc[1] >= -0.01)
L.append(f"GATE to the 053 conf: {'PASS' if gate else 'FAIL'} (primary >= +0.005: {p >= 0.005}; panel C1 clean lower > -0.01: {pc[0] > -0.01}; G C1 lower > -0.01: {gc[0] > -0.01}; f1/f2 NP C2 not harm: {fc[1] >= -0.01})")
open(os.path.join(HERE, "diag/x080_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
