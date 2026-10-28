"""Descriptive (no new model): is the v8w7a main's C2 rank-1 a training structure more often when it is WRONG than its base rate in the C2 view
list, and than when it is right? Uses diag/top102_<tag>.parquet (rank-1 SMILES), diag/r102_<tag>.csv (main RR) and the C2 view frames
(in_short_c2 & (in_tier | in_coconut | in_train_c2)). in_train_c2 = the candidate is a training structure (the truth's own flag is hidden in
C2). Usage (Spark, experiments/b1_baseline): python -X utf8 x_seenbias.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUN = {"f1dev": "run_f1dev", "np053f1dev": "run_np053_f1dev", "f2dev": "run_f2dev", "np053f2dev": "run_np053_f2dev"}
L = ["# Training-structure share of the main's C2 rank-1 (wrong vs right) and of the C2 view lists", "",
     "| tag set | train share of the list | rank-1 is train when WRONG (n) | rank-1 is train when RIGHT (n) |", "|---|---:|---:|---:|"]
W = [0, 0]; Rr = [0, 0]; bases = []
for tag, run in RUN.items():
    T = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); T = T[(T.view == "c2") & (T["rank"] == 1)][["set", "molecule", "smiles"]]
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv"), usecols=["set", "view", "molecule", "main"]); R = R[R.view == "c2"]
    for s, g in T.groupby("set"):
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "in_short_c2", "in_tier", "in_coconut", "in_train_c2"])
        F = F[F.in_short_c2.astype(bool) & (F.in_tier.astype(bool) | F.in_coconut.astype(bool) | F.in_train_c2.astype(bool))]
        tr = F.in_train_c2.astype(bool); trs = set(zip(F.molecule[tr], F.smiles[tr])); base = float(tr.mean()); bases.append(base)
        m = g.merge(R[R.set == s][["set", "molecule", "main"]], on=["set", "molecule"])
        t1 = np.array([(a, b) in trs for a, b in zip(m.molecule, m.smiles)]); w = (m.main < 1).values
        W[0] += int(t1[w].sum()); W[1] += int(w.sum()); Rr[0] += int(t1[~w].sum()); Rr[1] += int((~w).sum())
        fm = lambda x, k: f"{x[k].mean():.3f} ({int(k.sum())})" if k.any() else "n/a"
        L.append(f"| {tag} {s} | {base:.3f} | {fm(t1, w)} | {fm(t1, ~w)} |")
L.append(f"| **all** | {np.mean(bases):.3f} (mean) | {W[0] / max(1, W[1]):.3f} ({W[1]}) | {Rr[0] / max(1, Rr[1]):.3f} ({Rr[1]}) |")
open(os.path.join(HERE, "diag/x_seenbias.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
