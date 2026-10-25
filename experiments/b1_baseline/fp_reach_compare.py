"""Codex 018 step 2: same-window FPNet comparison. The candidate window of a molecule depends only on its neutral masses (not on the FPNet), so
feature runs of the same evaluation CSV made with different FPNet checkpoints share the windows; b1_molecules_<set>.csv records the truth's
FP-only rank in the window (truth_fp_rank), the FP+prior ranks (truth_fppop_rank / truth_fppop50_rank) and the prior-only rank. This script
joins the runs on molecule and reports, per set: Recall@25/60/100/200 of the truth under each ranking, FP-only MRR@25, paired differences
with molecule-level bootstrap CIs, and how many molecules change reach. Runs are labelled (label=run_dir).
Usage: python -X utf8 fp_reach_compare.py --eval_csv CSV --runs fold0=run_a seen=run_b [...] --sets A_timstof B_nplib [--out report.md]
"""
import argparse, os
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--eval_csv", required=True); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--sets", nargs="+", required=True)
ap.add_argument("--out", default=""); ap.add_argument("--boot", type=int, default=5000); a = ap.parse_args()
rng = np.random.default_rng(20261025)
def boot_ci(d):
    if len(d) < 2: return (float("nan"), float("nan"))
    idx = rng.integers(0, len(d), size=(a.boot, len(d))); m = d[idx].mean(1); return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))
runs = dict(r.split("=", 1) for r in a.runs); ev = pd.read_csv(a.eval_csv)
md = [f"# same-window FPNet comparison ({', '.join(f'{k}={v}' for k, v in runs.items())})", ""]
RANKS = [("truth_fp_rank", "FP only"), ("truth_fppop_rank", "FP + prior (shortlist lambda)"), ("truth_fppop50_rank", "FP + 0.5 prior"), ("truth_pop_rank", "prior only")]
for s in a.sets:
    tabs = {}
    for lab, run in runs.items():
        p = f"{run}/b1_molecules_{s}.csv"
        if not os.path.exists(p): print("missing", p); continue
        t = pd.read_csv(p).set_index("molecule"); tabs[lab] = t
    if len(tabs) < 2: continue
    common = sorted(set.intersection(*[set(t.index) for t in tabs.values()]))
    base = tabs[list(tabs)[0]].loc[common]
    md += [f"## {s}: {len(common)} molecules (windows identical across runs: n_unique equal for {int(np.mean([(tabs[l].loc[common, 'n_unique'].values == base['n_unique'].values).mean() for l in tabs]) * 100)}% ; truth in window {int(base['truth_in_window'].sum())})", ""]
    md += ["| ranking | run | R@25 | R@60 | R@100 | R@200 | MRR@25 (FP rank) |", "|---|---|---:|---:|---:|---:|---:|"]
    for col, name in RANKS:
        for lab, t in tabs.items():
            r = t.loc[common, col].values.astype(float); r = np.where(r < 1, np.inf, r)   # -1 = truth not in window -> never reached
            rec = {k: float((r <= k).mean()) for k in (25, 60, 100, 200)}; mrr = float(np.where(r <= 25, 1.0 / np.maximum(r, 1), 0.0).mean())
            md.append(f"| {name} | {lab} | {rec[25]:.3f} | {rec[60]:.3f} | {rec[100]:.3f} | {rec[200]:.3f} | {mrr:.3f} |")
    md += ["", "| ranking | comparison | Δ R@200 (paired) | 95% CI | Δ MRR@25 (FP rank) | 95% CI | gained / lost reach@200 |", "|---|---|---:|---|---:|---|---|"]
    labs = list(tabs); ref = labs[0]
    for lab in labs[1:]:
        for col, name in RANKS[:2]:
            rx = tabs[lab].loc[common, col].values.astype(float); ry = tabs[ref].loc[common, col].values.astype(float)
            rx = np.where(rx < 1, np.inf, rx); ry = np.where(ry < 1, np.inf, ry)
            dr = (rx <= 200).astype(float) - (ry <= 200).astype(float); dm = np.where(rx <= 25, 1 / np.maximum(rx, 1), 0.0) - np.where(ry <= 25, 1 / np.maximum(ry, 1), 0.0)
            ci1 = boot_ci(dr); ci2 = boot_ci(dm)
            md.append(f"| {name} | {lab} − {ref} | {dr.mean():+.3f} | [{ci1[0]:+.3f}, {ci1[1]:+.3f}] | {dm.mean():+.3f} | [{ci2[0]:+.3f}, {ci2[1]:+.3f}] | {int((dr > 0).sum())} / {int((dr < 0).sum())} |")
    # shortlist reach actually used by the pipeline (all branches)
    md += ["", "| run | truth in shortlist (any branch) | truth in short c2 | truth in short c1 (usable) |", "|---|---:|---:|---:|"]
    for lab, t in tabs.items():
        tt = t.loc[common]
        c1 = tt.loc[tt["c1_usable"] == True, "truth_in_short_c1"].mean() if "c1_usable" in tt.columns and (tt["c1_usable"] == True).any() else float("nan")
        md.append(f"| {lab} | {tt['truth_in_shortlist'].mean():.3f} | {tt['truth_in_short_c2'].mean():.3f} | {c1:.3f} |")
    md.append("")
text = "\n".join(md); print(text)
if a.out: open(a.out, "w", encoding="utf-8").write(text + "\n"); print("wrote", a.out)
