"""050 confirmation reading (read once): arm a vs base on the 053 conf NP_X layer (COCONUT-listed truths, non-timsTOF queries), fold-1/2
blocks equal weight; registered rule = primary C2 delta > 0 and C1 delta >= -0.01 per fold (049b three-state reported alongside)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 10000
D = {}
for K in (1, 2):
    b = pd.read_csv(os.path.join(HERE, f"diag/pxconf050_f{K}_base.csv")); x = pd.read_csv(os.path.join(HERE, f"diag/pxconf050_f{K}_pxa.csv"))
    m = b.merge(x, on=["set", "view", "molecule"], suffixes=("_b", "_x")); assert len(m) == len(b) == len(x); m["d"] = m.main_x - m.main_b; D[K] = m
L = ["# 050 confirmation (arm a, 053 conf NP_X, read once)", "", "| fold | view | n | base | arm a | delta [95%] | up / down |", "|---|---|---:|---:|---:|---|---|"]
for K, m in D.items():
    for v, g in m.groupby("view"):
        d = g.d.values; bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(NB)]); lo, hi = np.percentile(bs, [2.5, 97.5])
        L.append(f"| {K} | {v} | {len(g)} | {g.main_b.mean():.4f} | {g.main_x.mean():.4f} | {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] | {(d > 0).sum()} / {(d < 0).sum()} |")
c2 = [D[K][D[K].view == "c2"].d.values for K in (1, 2)]
p = np.mean([x.mean() for x in c2]); bs = np.array([np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in c2]) for _ in range(NB)]); lo, hi = np.percentile(bs, [2.5, 97.5])
c1 = {K: D[K][D[K].view == "c1"].d for K in (1, 2)}
ok_c1 = all((len(v) == 0) or (v.mean() >= -0.01) for v in c1.values())
L += ["", f"- primary (C2, blocks equal): {p:+.4f} [{lo:+.4f}, {hi:+.4f}]", f"- C1 per fold: " + ", ".join(f"f{K} n {len(v)} {v.mean() if len(v) else float('nan'):+.4f}" for K, v in c1.items()),
      f"- registered verdict: {'PASS' if (p > 0 and ok_c1) else 'FAIL'} (primary > 0: {p > 0}; C1 >= -0.01 per fold: {ok_c1})",
      f"- 049b reading of the primary aggregate (eps 0.01): {'harm' if hi < -0.01 else ('non-inferior' if lo > -0.01 else 'undetermined')}; C1 n is tiny -> protection evidence comes from the dev F C1 and the panel diagnostic"]
open(os.path.join(HERE, "diag/pxconf050_read.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
