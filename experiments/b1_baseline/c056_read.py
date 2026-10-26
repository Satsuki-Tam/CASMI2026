"""056 confirmation reading (read once): rank_v8w - rank_v4b on the reserved fold-3b/4b tables. Registered: primary = NP C2 (C/D/E/F equal)
per block (3b, 4b), blocks equal; PASS = point > 0 and the aggregate's lower 95% bound > -0.01 (identity bootstrap within blocks)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 10000
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]; X = {}
for K in (3, 4):
    a = pd.read_csv(os.path.join(HERE, f"diag/c056_rank_v4b_f{K}b.csv")); b = pd.read_csv(os.path.join(HERE, f"diag/c056_rank_v8w_f{K}b.csv"))
    m = a.merge(b, on=["set", "view", "molecule"], suffixes=("_a", "_b")); assert len(m) == len(a) == len(b); m["d"] = m.main_b - m.main_a; X[K] = m
L = ["# 056 confirmation (rank_v8w - rank_v4b, reserved 3b/4b, read once)", "", "| block | set | view | n | v4b | v8w | delta | up / down |", "|---|---|---|---:|---:|---:|---:|---|"]
for K, m in X.items():
    for (s, v), g in m.groupby(["set", "view"]):
        L.append(f"| {K}b | {s} | {v} | {len(g)} | {g.main_a.mean():.4f} | {g.main_b.mean():.4f} | {g.d.mean():+.4f} | {(g.d > 0).sum()} / {(g.d < 0).sum()} |")
blocks = []
for K, m in X.items():
    blocks.append([m[(m.view == "c2") & (m.set == s)].d.values for s in NP if len(m[(m.view == "c2") & (m.set == s)])])
pts = [np.mean([x.mean() for x in bl]) for bl in blocks]
bs = np.array([np.mean([np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in bl]) for bl in blocks]) for _ in range(NB)])
lo, hi = np.percentile(bs, [2.5, 97.5]); p = float(np.mean(pts))
L += ["", f"- primary NP C2 (blocks equal): {p:+.4f} [{lo:+.4f}, {hi:+.4f}]; blocks " + " / ".join(f"{x:+.4f}" for x in pts),
      f"- registered verdict: {'PASS' if (p > 0 and lo > -0.01) else 'FAIL'} (point > 0: {p > 0}; lower bound > -0.01: {lo > -0.01})"]
open(os.path.join(HERE, "diag/c056_read.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
