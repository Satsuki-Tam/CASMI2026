"""087 confirmation on the reserved 083 set (087_prereg_v8w7a.md amendment): rank_v8w7a - rank_v7a_pc under the v7f main.
Pass: NP_H C2 (600, strict) point >= +0.005 and identity bootstrap (4,000) lower > 0; NP_H C1 fails only on harm (U < -0.01); NP_X / NP_N must be exactly 0."""
import numpy as np, pandas as pd
rng = np.random.default_rng(20261027)
a = pd.read_csv("diag/c087_rank_v7a_pc.csv"); b = pd.read_csv("diag/c087_rank_v8w7a.csv")
x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_a", "_b")); assert len(x) == len(a) == len(b); x["d"] = x.main_b - x.main_a
def ci(d): bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]; return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
c2 = x[(x.set == "NP_H") & (x.view == "c2")].d.values; c1 = x[(x.set == "NP_H") & (x.view == "c1")].d.values
p, lo, hi = ci(c2); q, qlo, qhi = ci(c1) if len(c1) else (np.nan, np.nan, np.nan)
inv = float(np.abs(x[x.set.isin(["NP_X", "NP_N"])].d.values).max()) if x.set.isin(["NP_X", "NP_N"]).any() else 0.0
ok = p >= 0.005 and lo > 0 and not (qhi < -0.01) and inv == 0.0
L = ["# 087 confirmation on 083 (rank_v8w7a - rank_v7a_pc, v7f main)", "",
     f"- NP_H C2 (n {len(c2)}): {p:+.4f} [{lo:+.4f}, {hi:+.4f}]; v7a_pc {x[(x.set == 'NP_H') & (x.view == 'c2')].main_a.mean():.4f} -> v8w7a {x[(x.set == 'NP_H') & (x.view == 'c2')].main_b.mean():.4f}",
     f"- NP_H C1 (n {len(c1)}): {q:+.4f} [{qlo:+.4f}, {qhi:+.4f}]",
     f"- NP_X / NP_N (fallback, must be 0): max |d| {inv:.6f}",
     f"- **CONFIRMATION: {'PASS' if ok else 'FAIL'}**"]
open("diag/x087c_summary.md", "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
