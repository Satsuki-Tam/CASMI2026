"""064 diagnostic: dev2 4-cell cross comparison {public fold0 FPNet, full_eval} x {rank_v4b, rank_v8w} (same queries, each FPNet's own
shortlist). Delta = v8w - v4b per molecule within each FPNet column; interaction I = Delta(full_eval) - Delta(fold0); identity bootstrap."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 10000
def load(a, b):
    x = pd.read_csv(os.path.join(HERE, a)).merge(pd.read_csv(os.path.join(HERE, b)), on=["set", "view", "molecule"], suffixes=("_a", "_b")); x["d"] = x.main_b - x.main_a; return x
FE = load("diag/r047_rank_v4b_p2dev.csv", "diag/r056_rank_v8w_p2dev.csv"); F0 = load("diag/x064_rank_v4b_p2dev_f0.csv", "diag/x064_rank_v8w_p2dev_f0.csv")
M = FE.merge(F0, on=["set", "view", "molecule"], suffixes=("_fe", "_f0"))
L = ["# 064 dev2 cross comparison (v8w - v4b under each FPNet; I = full_eval - fold0)", "", "| set | view | n | base fold0 | base full_eval | Delta fold0 [95%] | Delta full_eval [95%] | I [95%] |", "|---|---|---:|---:|---:|---|---|---|"]
def ci(v): bs = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(NB)]); return np.percentile(bs, [2.5, 97.5])
for (s, v), g in M.groupby(["set", "view"]):
    if len(g) < 20: continue
    d0, d1 = g.d_f0.values, g.d_fe.values; I = d1 - d0
    a0, a1, ai = ci(d0), ci(d1), ci(I)
    L.append(f"| {s} | {v} | {len(g)} | {g.main_a_f0.mean():.4f} | {g.main_a_fe.mean():.4f} | {d0.mean():+.4f} [{a0[0]:+.4f}, {a0[1]:+.4f}] | {d1.mean():+.4f} [{a1[0]:+.4f}, {a1[1]:+.4f}] | {I.mean():+.4f} [{ai[0]:+.4f}, {ai[1]:+.4f}] |")
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
def macro(col):
    gs = [M[(M.view == "c2") & (M.set == s)][col].values for s in NP]
    p = np.mean([g.mean() for g in gs]); bs = np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]); return p, np.percentile(bs, [2.5, 97.5])
M["I"] = M.d_fe - M.d_f0
for col, name in (("d_f0", "Delta fold0"), ("d_fe", "Delta full_eval"), ("I", "I")):
    p, c = macro(col); L.append(f"- NP C2 macro {name}: {p:+.4f} [{c[0]:+.4f}, {c[1]:+.4f}]")
open(os.path.join(HERE, "diag/x064_read.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
