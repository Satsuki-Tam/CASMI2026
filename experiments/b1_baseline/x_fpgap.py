"""Codex 115 (1): descriptive split of the v8w7a main's C2 errors with the truth in the list (diag/x_fpcoll.csv rows, rP > 1): does the table's FP
score (merged-logit f.z, the P input) already prefer the truth over P's wrong rank-1, or does FP itself err? Per row: fp(truth), fp(top-1),
gap = fp(truth) - fp(top-1) (f.z units = Bernoulli log-likelihood difference), the truth's FP rank inside P's view list (pessimistic ties) and
whether the truth's prior (pop_public) is below the top-1's. No new model; label-using diagnostic. Usage (Spark): python -X utf8 x_fpgap.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUN = {"f1dev": "run_f1dev", "np053f1dev": "run_np053_f1dev", "f2dev": "run_f2dev", "np053f2dev": "run_np053_f2dev"}
X = pd.read_csv(os.path.join(HERE, "diag/x_fpcoll.csv")); rows = []
for (tag, s), g in X.groupby(["tag", "set"], sort=False):
    F = pd.read_parquet(os.path.join(HERE, RUN[tag], f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "fp", "pop_public", "in_short_c2", "in_tier", "in_coconut", "in_train_c2", "is_truth"])
    F = F[F.in_short_c2.astype(bool) & (F.in_tier.astype(bool) | F.in_coconut.astype(bool) | F.in_train_c2.astype(bool))]
    for r in g.itertuples(index=False):
        f = F[F.molecule == r.molecule]
        t = f[f.smiles == r.truth]; o = f[f.smiles == r.top1]
        if not len(t) or not len(o): continue
        ft, fo = float(t.fp.values[0]), float(o.fp.values[0]); fps = np.nan_to_num(f.fp.values.astype(float), nan=-1e18)
        rows.append(dict(tag=tag, set=s, molecule=r.molecule, fp_truth=ft, fp_top1=fo, gap=ft - fo, fp_rank_truth=int((fps >= ft).sum()), n_list=len(f),
                         pop_truth=float(t.pop_public.values[0]), pop_top1=float(o.pop_public.values[0]), top1_train=bool(o.in_train_c2.values[0]), tani=r.tanimoto))
D = pd.DataFrame(rows); D.to_csv(os.path.join(HERE, "diag/x_fpgap.csv"), index=False)
L = ["# FP score of the truth vs the main's wrong rank-1 (C2 errors with the truth in the list; table fp = merged-logit f.z)", "",
     "| tag set | errors | FP prefers truth (gap > 0) | median gap | truth FP rank 1 in list | truth FP rank 2-5 | truth prior below top-1 | FP prefers truth AND prior below | top-1 is a train structure |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
def line(lab, g):
    pref = g.gap > 0; pb = g.pop_truth < g.pop_top1
    return (f"| {lab} | {len(g)} | {pref.mean():.3f} | {g.gap.median():+.2f} | {(g.fp_rank_truth == 1).mean():.3f} | {((g.fp_rank_truth >= 2) & (g.fp_rank_truth <= 5)).mean():.3f} | "
            f"{pb.mean():.3f} | {(pref & pb).mean():.3f} | {g.top1_train.mean():.3f} |")
for (tag, s), g in D.groupby(["tag", "set"], sort=False): L.append(line(f"{tag} {s}", g))
L.append(line("**all**", D))
open(os.path.join(HERE, "diag/x_fpgap.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
