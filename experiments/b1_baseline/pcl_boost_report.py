"""Paired comparison of the PubChemLite-boosted outputs (blend21_pcl<w>) against the registered main blend21 of the same candidate, from the
per-molecule prediction CSVs written by b1_locked_eval_pcl.py (pred_<set>_<view>_<cand>_<output>.csv with an rr column). Molecule-level
bootstrap (20,000, seed 20261025). Usage: python -X utf8 pcl_boost_report.py EVAL_DIR [EVAL_DIR ...] [--cand M2x] [--out report.md]
"""
import argparse, glob, os, re
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("dirs", nargs="+"); ap.add_argument("--cand", default="M2x"); ap.add_argument("--out", default="")
ap.add_argument("--prefix", default="pcl", help="variant family: pcl (PubChemLite boost) or pcd (PubChem-tier-only demotion, Codex 023b)"); a = ap.parse_args()
rng = np.random.default_rng(20261025)
def ci(d):
    idx = rng.integers(0, len(d), size=(20000, len(d))); m = d[idx].mean(1); return np.percentile(m, 2.5), np.percentile(m, 97.5)
md = ["| eval | set | view | n | blend21 | output | MRR | Δ vs blend21 [95% CI] |", "|---|---|---|---:|---:|---|---:|---|"]
for d in a.dirs:
    for base in sorted(glob.glob(os.path.join(d, f"pred_*_{a.cand}_blend21.csv"))):
        m = re.match(rf"pred_(.+)_(c[12])_{a.cand}_blend21\.csv", os.path.basename(base)); s, view = m.group(1), m.group(2)
        b = pd.read_csv(base)
        for f in sorted(glob.glob(os.path.join(d, f"pred_{s}_{view}_{a.cand}_blend21_{a.prefix}*.csv")), key=lambda x: os.path.basename(x)):
            o = pd.read_csv(f); assert list(o.molecule_id) == list(b.molecule_id)
            dd = o.rr.values - b.rr.values; lo, hi = ci(dd)
            md.append(f"| {os.path.basename(d)} | {s} | {view} | {len(b)} | {b.rr.mean():.3f} | {os.path.basename(f).rsplit('blend21_', 1)[-1][:-4]} | {o.rr.mean():.3f} | {dd.mean():+.3f} [{lo:+.3f}, {hi:+.3f}] |")
text = "\n".join(md); print(text)
if a.out: open(a.out, "w", encoding="utf-8").write(text + "\n")
