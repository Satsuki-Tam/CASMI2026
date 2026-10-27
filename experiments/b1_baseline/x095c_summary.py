"""095 confirmation on the reserved np096_conf095 (096_reserved_conf.md, reallocation): NP_H 400, C2 strict, bpp - main >= +0.010 and identity
bootstrap (4,000) lower > 0; checks: rows whose truth is not B (reach-conditioned flag) and every C1 row must have d == 0."""
import numpy as np, pandas as pd
rng = np.random.default_rng(20261028)
x = pd.read_csv("diag/c095_np096.csv"); x["d"] = x.bpp - x.main; x["truth_B"] = x.truth_B.astype(str).isin(["True", "1", "1.0"])
bad = set(x.truth_B.astype(str)) - {"True", "False"}
c2 = x[(x.view == "c2") & (x.set == "NP_H")]; d = c2.d.values
bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]; lo, hi = np.percentile(bs, [2.5, 97.5])
chk_nonB = float(np.abs(x[~x.truth_B].d).max()) if (~x.truth_B).any() else 0.0; chk_c1 = float(np.abs(x[x.view == "c1"].d).max()) if (x.view == "c1").any() else 0.0
ok = d.mean() >= 0.010 and lo > 0 and chk_nonB == 0 and chk_c1 == 0
L = ["# 095 confirmation on np096_conf095 (NP_H 400)", "", f"- NP_H C2 (n {len(d)}): bpp - main {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}]; main {c2.main.mean():.4f} -> bpp {c2.bpp.mean():.4f}",
     f"- truth-B (reached) rows {int(c2.truth_B.sum())}; checks: non-B max |d| {chk_nonB:.6f}, C1 max |d| {chk_c1:.6f}; unexpected truth_B strings {sorted(bad)}",
     f"- **CONFIRMATION: {'PASS' if ok else 'FAIL'}**"]
open("diag/x095c_summary.md", "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
