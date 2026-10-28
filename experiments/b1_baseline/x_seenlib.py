"""Descriptive (no new model): can class-1 evidence separate the main's WRONG training-structure rank-1 in C2 from the RIGHT training-structure
rank-1 in C1? For C2 rows whose rank-1 is a training structure (always wrong in C2), the library similarity of that candidate (lib_sim_c2 = best
entropy similarity of the query to the candidate's own references, same masks as the evaluator) vs, for C1 rows with the truth at rank 1, the
truth's lib_sim_c1 (its other-library references). Quantiles and the share above fixed thresholds. Uses diag/top102_<tag>.parquet,
diag/r102_<tag>.csv and the tables. Usage (Spark, experiments/b1_baseline): python -X utf8 x_seenlib.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUN = {"f1dev": "run_f1dev", "np053f1dev": "run_np053_f1dev", "f2dev": "run_f2dev", "np053f2dev": "run_np053_f2dev"}
c2w, c1r = [], []
for tag, run in RUN.items():
    T = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); T = T[T["rank"] == 1][["set", "view", "molecule", "smiles"]]
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv"), usecols=["set", "view", "molecule", "main"])
    m = T.merge(R, on=["set", "view", "molecule"])
    for s, g in m.groupby("set"):
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "in_train_c2", "in_train_c1", "lib_sim_c1", "lib_sim_c2", "is_truth"])
        F = F.set_index(["molecule", "smiles"])
        for r in g.itertuples(index=False):
            if (r.molecule, r.smiles) not in F.index: continue
            f = F.loc[(r.molecule, r.smiles)]
            if r.view == "c2" and bool(f.in_train_c2): c2w.append(dict(tag=tag, set=s, lib=float(f.lib_sim_c2)))
            if r.view == "c1" and r.main == 1 and bool(f.is_truth): c1r.append(dict(tag=tag, set=s, lib=float(f.lib_sim_c1)))
A, Bc = pd.DataFrame(c2w), pd.DataFrame(c1r)
L = ["# Library similarity: wrong training-structure rank-1 in C2 vs right truth rank-1 in C1", "",
     "| group | n | q10 | q25 | median | q75 | q90 | >= 0.6 | >= 0.7 | >= 0.8 | >= 0.9 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for lab, d in (("C2 rank-1 = training structure (wrong)", A), ("C1 rank-1 = truth (right)", Bc)):
    v = d.lib.values
    L.append(f"| {lab} | {len(v)} | " + " | ".join(f"{np.quantile(v, q):.3f}" for q in (0.1, 0.25, 0.5, 0.75, 0.9)) + " | " + " | ".join(f"{(v >= t).mean():.3f}" for t in (0.6, 0.7, 0.8, 0.9)) + " |")
open(os.path.join(HERE, "diag/x_seenlib.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
