"""111 DESCRIPTIVE diagnostic anchored on the frozen P0 (Codex 123 Q2), written before any 111 result; never used for the gate or the budget choice.
Per budget ck and cell (tag, set, view), from diag/r111_<ck>_<tag>.csv (the registered evaluation's rows): main = P0's RR, t1N_0.5 = the registered
rank-1-fixed connection, rP_n = the truth's rank in P0's view list (0 = not in the list), rN / rN_pess = the truth's rank under N alone (ties by P0
order / pessimistic). Reported:
  rows, P0 wrong (main < 1) split into "truth not in the view list" (rP_n = 0) and "in the list";
  among P0-wrong rows with the truth in the list: share with rN_pess < rP_n (N ranks the truth above P0 does), share with rN_pess = 1 (N alone would
  put it first, i.e. above P0's wrong rank-1), median rP_n -> median rN_pess;
  dRR = t1N_0.5 - main: sum of positive and of negative changes over ALL rows of the cell (whole-cell denominators), rows improved / worsened, and
  rows with main = 1 that changed (0 by design: rank 1 is kept).
The GLACIER-path / fallback split is not available in these rows (not reported). Usage (Spark, experiments/b1_baseline): python -X utf8 x111_p0fail.py"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TOL = 1e-12
CKS = ["s2000", "s8000", "s20000"]; TAGS = ["f1dev", "np053f1dev", "c1bankdev"]
L = ["# 111 diagnostic anchored on the frozen P0 (descriptive; not used for the gate or the budget choice)", "",
     "| budget | cell | rows | P0 wrong: not in list / in list | in list: N above P0 / N first | median rank P0 -> N | dRR + sum / - sum | improved / worsened | main=1 changed |",
     "|---|---|---:|---|---|---|---|---|---:|"]
for ck in CKS:
    for t in TAGS:
        p = os.path.join(HERE, f"diag/r111_{ck}_{t}.csv")
        if not os.path.exists(p): L.append(f"| {ck} | {t} | missing | | | | | | |"); continue
        x = pd.read_csv(p)
        for (s, v), r in x.groupby(["set", "view"], sort=True):
            m = r.main.values.astype(float); c = r["t1N_0.5"].values.astype(float); rp = r.rP_n.values.astype(int); rn = r.rN_pess.values.astype(float)
            w = m < 1 - TOL; inl = w & (rp > 0); d = c - m
            above = (rn[inl] < rp[inl]).mean() if inl.any() else float("nan"); first = (rn[inl] == 1).mean() if inl.any() else float("nan")
            med = f"{np.median(rp[inl]):.0f} -> {np.median(rn[inl]):.0f}" if inl.any() else "-"
            L.append(f"| {ck} | {t} {s} {v} | {len(r)} | {int((w & (rp == 0)).sum())} / {int(inl.sum())} | {above:.2f} / {first:.2f} | {med} | "
                     f"{d[d > TOL].sum() / len(r):+.4f} / {d[d < -TOL].sum() / len(r):+.4f} | {int((d > TOL).sum())} / {int((d < -TOL).sum())} | {int(((m >= 1 - TOL) & (np.abs(d) > TOL)).sum())} |")
open(os.path.join(HERE, "diag/x111_p0fail.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
