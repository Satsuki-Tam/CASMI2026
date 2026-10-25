"""Codex 024: 2x2 report (ranker x Pc demotion) from the evaluator's per-molecule predictions on the same tables:
A = OLD blend21, B = OLD blend21_pcd<w>, C = NEW blend21, D = NEW blend21_pcd<w>. Paired molecule-level bootstrap (identity-joint: one index per
resample shared by all four outputs). Reports C−A (ranker), B−A and D−C (demotion under each ranker) and the interaction (D−C)−(B−A).
Usage: python -X utf8 twobytwo_report.py EVAL_DIR [EVAL_DIR ...] --old RK_old --new RK_new --w 0.5 [--out md]
"""
import argparse, glob, os, re
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("dirs", nargs="+"); ap.add_argument("--old", default="RK_old"); ap.add_argument("--new", default="RK_new"); ap.add_argument("--w", default="0.5")
ap.add_argument("--out", default=""); a = ap.parse_args()
rng = np.random.default_rng(20261025)
md = ["| eval | set | view | n | A old | B old+pcd | C new | D new+pcd | C−A [95% CI] | B−A | D−C [95% CI] | (D−C)−(B−A) [95% CI] |", "|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|"]
for d in a.dirs:
    for base in sorted(glob.glob(os.path.join(d, f"pred_*_{a.old}_blend21.csv"))):
        m = re.match(rf"pred_(.+)_(c[12])_{a.old}_blend21\.csv", os.path.basename(base)); s, view = m.group(1), m.group(2)
        P = {k: os.path.join(d, f"pred_{s}_{view}_{c}_{o}.csv") for k, c, o in (("A", a.old, "blend21"), ("B", a.old, f"blend21_pcd{a.w}"), ("C", a.new, "blend21"), ("D", a.new, f"blend21_pcd{a.w}"))}
        if not all(os.path.exists(p) for p in P.values()): md.append(f"| {os.path.basename(d)} | {s} | {view} | missing outputs | | | | | | | | |"); continue
        R = {k: pd.read_csv(p).set_index("molecule_id").rr for k, p in P.items()}
        ids = R["A"].index; assert all(list(R[k].index) == list(ids) for k in R), "molecule order differs"
        X = {k: R[k].values.astype(float) for k in R}; n = len(ids)
        idx = rng.integers(0, n, size=(5000, n))
        def ci(v): b = v[idx].mean(1); return np.percentile(b, 2.5), np.percentile(b, 97.5)
        ca, ba, dc = X["C"] - X["A"], X["B"] - X["A"], X["D"] - X["C"]; it = dc - ba
        f = lambda v: f"{v.mean():+.3f} [{ci(v)[0]:+.3f}, {ci(v)[1]:+.3f}]"
        md.append(f"| {os.path.basename(d)} | {s} | {view} | {n} | {X['A'].mean():.3f} | {X['B'].mean():.3f} | {X['C'].mean():.3f} | {X['D'].mean():.3f} | {f(ca)} | {ba.mean():+.3f} | {f(dc)} | {f(it)} |")
text = "\n".join(md); print(text)
if a.out: open(a.out, "w", encoding="utf-8").write(text + "\n"); print("wrote", a.out)
