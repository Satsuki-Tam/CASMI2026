"""W7 parity test (Codex 007): the submission pipeline's candidate dump vs the evaluator's feature table on the same molecules and view.

Compared per molecule: the candidate sets (official scorer keys), whether the truth is in each, and on the common candidates the features
both sides compute (fp, pop, library similarity of the view, in_tier / in_coconut / in_train flags, ppm error). Differences point at
evaluation-vs-submission drift (W7); the official scores of the pipeline run itself are in its eval_scores.json.
Usage: python b1_parity.py --dump <pipeline_out>/b1_candidates.parquet --features_run experiments/b1_baseline/run1_v2 --view c2 --solution <eval_test_set>/solution.csv --out <pipeline_out>/parity.md
"""
import argparse, glob, os
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--dump", required=True); ap.add_argument("--features_run", required=True); ap.add_argument("--view", choices=["c1", "c2"], required=True)
ap.add_argument("--solution", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
D = pd.read_parquet(a.dump); D["molecule"] = D["molecule"].astype(str)
F = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{a.features_run}/b1_features_*.parquet"))], ignore_index=True)
S = pd.read_csv(a.solution); S["molecule_id"] = S["molecule_id"].astype(str)
v = a.view
keep = F[f"in_short_{v}"].astype(bool)
if v == "c2": keep &= (F.in_tier | F.in_coconut | F.in_train_c2).astype(bool)
F = F[keep]
rows, diffs = [], []
for _, s in S.iterrows():
    mid = s.molecule_id; truth = s.scorer_key if "scorer_key" in S.columns else None
    f = F[F.molecule == mid]; p = D[D.molecule == mid]
    fk, pk = set(f.official_key), set(p.key); inter = fk & pk
    rec = dict(molecule=mid, set=s.get("set"), group=s.get("group"), n_f=len(fk), n_p=len(pk), n_inter=len(inter), only_f=len(fk - pk), only_p=len(pk - fk),
               jaccard=len(inter) / max(len(fk | pk), 1), truth_in_f=truth in fk, truth_in_p=truth in pk)
    if inter:
        fm = f.drop_duplicates("official_key").set_index("official_key").loc[sorted(inter)]; pm = p.drop_duplicates("key").set_index("key").loc[sorted(inter)]
        fp_d = np.abs(fm.fp.astype(float).values - pm.fp.astype(float).values); lib_d = np.abs(fm[f"lib_sim_{v}"].astype(float).values - pm.lib.astype(float).values)
        rec.update(fp_absdiff_max=float(np.nanmax(fp_d)), fp_absdiff_mean=float(np.nanmean(fp_d)), lib_absdiff_max=float(np.nanmax(lib_d)),
                   pop_equal=float(np.mean(np.isclose(fm.pop_public.astype(float).values, pm["pop"].astype(float).values, atol=1e-6))),
                   tier_equal=float(np.mean(fm.in_tier.astype(bool).values == pm.in_tier.astype(bool).values)), coco_equal=float(np.mean(fm.in_coconut.astype(bool).values == pm.in_coconut.astype(bool).values)),
                   train_equal=float(np.mean(fm[f"in_train_{v}"].astype(bool).values == pm.in_train.astype(bool).values)),
                   ppm_absdiff_max=float(np.nanmax(np.abs(fm.ppm_err.astype(float).values - pm.ppm_err.astype(float).values))))
    rows.append(rec)
R = pd.DataFrame(rows)
md = [f"# W7 parity: {a.dump} vs {a.features_run} (view {v})", "", f"molecules in solution {len(S)}; with candidates on both sides {int(((R.n_f > 0) & (R.n_p > 0)).sum())}; "
      f"features side only {int(((R.n_f > 0) & (R.n_p == 0)).sum())}; pipeline side only {int(((R.n_f == 0) & (R.n_p > 0)).sum())}", "",
      "| metric | value |", "|---|---:|",
      f"| identical candidate sets | {(R.jaccard == 1).mean():.3f} |", f"| Jaccard median / mean / min | {R.jaccard.median():.3f} / {R.jaccard.mean():.3f} / {R.jaccard.min():.3f} |",
      f"| candidates only in evaluator (mean) | {R.only_f.mean():.1f} |", f"| candidates only in pipeline (mean) | {R.only_p.mean():.1f} |",
      f"| truth in evaluator shortlist / in pipeline shortlist | {R.truth_in_f.mean():.3f} / {R.truth_in_p.mean():.3f} |",
      f"| truth membership disagrees | {int((R.truth_in_f != R.truth_in_p).sum())} molecules |"]
if "fp_absdiff_max" in R.columns:
    md += [f"| fp abs diff: max over molecules of per-molecule max / mean of means | {R.fp_absdiff_max.max():.4f} / {R.fp_absdiff_mean.mean():.5f} |",
           f"| library similarity abs diff max | {R.lib_absdiff_max.max():.4f} |", f"| pop equal share (mean) | {R.pop_equal.mean():.4f} |",
           f"| in_tier / in_coconut / in_train equal share (mean) | {R.tier_equal.mean():.4f} / {R.coco_equal.mean():.4f} / {R.train_equal.mean():.4f} |",
           f"| ppm error abs diff max | {R.ppm_absdiff_max.max():.3f} |"]
md += ["", "## by set", "", "| set | n | identical sets | Jaccard mean | truth in F | truth in P |", "|---|---:|---:|---:|---:|---:|"]
for k, g in R.groupby("set"): md.append(f"| {k} | {len(g)} | {(g.jaccard == 1).mean():.3f} | {g.jaccard.mean():.3f} | {g.truth_in_f.mean():.3f} | {g.truth_in_p.mean():.3f} |")
worst = R.sort_values("jaccard").head(10); cols = ["molecule", "set", "n_f", "n_p", "n_inter", "only_f", "only_p", "jaccard", "truth_in_f", "truth_in_p"]
md += ["", "## largest disagreements", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f"{r_[c]:.3f}" if isinstance(r_[c], float) else str(r_[c]) for c in cols) + " |" for _, r_ in worst.iterrows()]
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); R.to_csv(a.out.replace(".md", "_molecules.csv"), index=False)
print("\n".join(md[:20]))
