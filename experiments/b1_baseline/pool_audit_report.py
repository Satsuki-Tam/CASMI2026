"""Report of the pool-window shortlist audit (b1_features.py audit columns, 2026-10-25): per run and set, truth reach under the current
shortlist (C2 branches) and under + FP top-60 / top-100 among the window's v2-pool structures, plain (truth in the shortlist, C1-like) and
C2-strict (truth also reachable through an external source: reach_external_b1, i.e. not a train-only pool structure), plus the shortlist
size cost and how far down the full window the rescued truths were.
Usage: python -X utf8 pool_audit_report.py RUN_DIR [RUN_DIR ...] [--out report.md]
"""
import argparse, glob, os
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("runs", nargs="+"); ap.add_argument("--out", default=""); a = ap.parse_args()
md = ["# pool-window shortlist branch audit (current fold-0 FPNet unless the run says otherwise)", "",
      "| run | set | n | window reach | short (cur) | +pool60 | +pool100 | C2-strict cur | C2-strict +pool60 | rescued by pool60 | short size cur → +pool60 (median) | rescued truths' full-window FP rank (median) |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
for run in a.runs:
    for f in sorted(glob.glob(os.path.join(run, "b1_molecules_*.csv"))):
        s = os.path.basename(f)[len("b1_molecules_"):-4]; m = pd.read_csv(f)
        if "truth_in_short_pool60" not in m.columns: md.append(f"| {os.path.basename(run)} | {s} | {len(m)} | (no pool audit columns) |"); continue
        tw = m.truth_in_window.fillna(False).astype(bool); cur = m.truth_in_short_c2.fillna(False).astype(bool)
        p60 = m.truth_in_short_pool60.fillna(False).astype(bool); p100 = m.truth_in_short_pool100.fillna(False).astype(bool)
        ext = m.reach_external_b1.fillna(False).astype(bool)
        resc = p60 & ~cur
        size_cur = m.n_short_c2 if "n_short_c2" in m.columns else pd.Series(np.nan, index=m.index)
        rr = m.loc[resc, "truth_fp_rank"]
        md.append(f"| {os.path.basename(run)} | {s} | {len(m)} | {tw.mean():.3f} | {cur.mean():.3f} | {p60.mean():.3f} | {p100.mean():.3f} | {(cur & ext).mean():.3f} | {(p60 & ext).mean():.3f} | "
                  f"{int(resc.sum())} | {size_cur.median():.0f} → {m.n_short_pool60.median():.0f} | {rr.median() if len(rr) else float('nan'):.0f} |")
md += ["", "Columns: 'short (cur)' = truth among the current C2-view shortlist branches (FP top-K, FP+prior, library top-20, prior); '+poolK' = that plus FP top-K among the",
       "window's pool structures. C2-strict multiplies by reach_external_b1 (the class-2 proxy drops a truth that is only a train-structure pool entry).",
       "Rescue counts are audit-only: whether the rescued truth then ranks well depends on the forward models and the ranker."]
text = "\n".join(md); print(text)
if a.out: open(a.out, "w", encoding="utf-8").write(text + "\n")
