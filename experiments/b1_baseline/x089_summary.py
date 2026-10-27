"""089 stage (a) reading (089_prereg_dreams_a.md): per fold and pooled, MRR@25 / top-1 of rF (fold-safe FPNet), rD (DreaMS head), rE0.5 / rE1.0
(z-sums) on the COCONUT-truth stratum (primary), non-COCONUT and all; paired bootstrap (2,000, molecules) of rE1.0 - rF on the pooled COCONUT stratum."""
import json, sys
import numpy as np, polars as pl
def mrr(r): return np.where(r <= 25, 1.0 / r, 0.0)
rows = []
for k in (1, 2):
    R = pl.read_csv(f"dreams_fp_f{k}/eval_rows.csv").with_columns(pl.lit(k).alias("fold")); rows.append(R)
A = pl.concat(rows)
out = ["| fold | stratum | n | MRR F | MRR D | MRR E0.5 | MRR E1.0 | E1.0 - F | top1 F | top1 D | top1 E1.0 |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for k in (1, 2, "pooled"):
    B = A if k == "pooled" else A.filter(pl.col("fold") == k)
    for name, f in (("COCONUT", pl.col("coco")), ("non-COCONUT", ~pl.col("coco")), ("all", pl.lit(True))):
        C = B.filter(f); m = {c: mrr(C[c].to_numpy()).mean() for c in ("rF", "rD", "rE0.5", "rE1.0")}
        t = {c: (C[c].to_numpy() == 1).mean() for c in ("rF", "rD", "rE1.0")}
        out.append(f"| {k} | {name} | {C.height} | {m['rF']:.4f} | {m['rD']:.4f} | {m['rE0.5']:.4f} | {m['rE1.0']:.4f} | {m['rE1.0'] - m['rF']:+.4f} | {t['rF']:.3f} | {t['rD']:.3f} | {t['rE1.0']:.3f} |")
C = A.filter(pl.col("coco")); d = mrr(C["rE1.0"].to_numpy()) - mrr(C["rF"].to_numpy())
rng = np.random.default_rng(0); bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)])
lo, hi = np.quantile(bs, [0.025, 0.975])
f1 = A.filter((pl.col("fold") == 1) & pl.col("coco")); f2 = A.filter((pl.col("fold") == 2) & pl.col("coco"))
d1 = (mrr(f1["rE1.0"].to_numpy()) - mrr(f1["rF"].to_numpy())).mean(); d2 = (mrr(f2["rE1.0"].to_numpy()) - mrr(f2["rF"].to_numpy())).mean()
gate = (d1 >= 0.01) and (d2 >= 0.01) and (lo > 0)
out += ["", f"pooled COCONUT E1.0 - F = {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] (n {len(d)}); fold 1 {d1:+.4f}, fold 2 {d2:+.4f}",
        f"GATE to stage (b) (both folds >= +0.01 and pooled lower > 0): {'PASS' if gate else 'FAIL'}"]
by = A.group_by("lib").agg(pl.len().alias("n"), pl.col("rF").map_elements(lambda s: float(mrr(s.to_numpy()).mean()), return_dtype=pl.Float64).alias("F"),
                           pl.col("rD").map_elements(lambda s: float(mrr(s.to_numpy()).mean()), return_dtype=pl.Float64).alias("D"),
                           pl.col("rE1.0").map_elements(lambda s: float(mrr(s.to_numpy()).mean()), return_dtype=pl.Float64).alias("E1")).sort("n", descending=True)
out += ["", "by library (pooled folds, MRR@25):", "| lib | n | F | D | E1.0 |", "|---|---:|---:|---:|---:|"] + [f"| {r['lib']} | {r['n']} | {r['F']:.4f} | {r['D']:.4f} | {r['E1']:.4f} |" for r in by.iter_rows(named=True)]
open("diag/x089_summary.md", "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
