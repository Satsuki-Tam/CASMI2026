"""Exploratory DESCRIPTION (label-using; not a candidate, not a gate): a continuous training-structure penalty on the frozen v8w7a lists
(diag/top102_<tag>.parquet, both views): S'(c) = score(c) - gamma * seen(c), seen = in_train_<view> of the view's features; re-sort the stored
top-25 (candidates beyond 25 cannot enter -- an approximation). For gamma in a grid: the C2 gain g (unknown-compound condition, the truth is never a
training structure) and the C1 cost c (known-compound condition) per cell, and the break-even known share pi* = g / (g + c) on the NP strata and the
panel (Codex 116: the benefit wins iff pi_C1 < g / (g + c); a sensitivity, not an estimate of pi). Literature idea (seen_analog_bias report, idea 1).
Usage (Spark, experiments/b1_baseline): python -X utf8 x_seenpen.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
TAGS = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_f0"}
GAMMAS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
rows = []
for tag, run in TAGS.items():
    T = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); T["molecule"] = T.molecule.astype(str)
    for s, ts in T.groupby("set"):
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "in_train_c1", "in_train_c2"]); F["molecule"] = F.molecule.astype(str)
        tr = {v: dict(zip(zip(F.molecule, F.smiles), F[f"in_train_{v}"].astype(bool))) for v in ("c1", "c2")}
        for (v, mol), g in ts.groupby(["view", "molecule"]):
            g = g.sort_values("rank"); sc = g.score.values.astype(float); it = g.is_truth.astype(bool).values
            seen = np.array([tr[v].get((mol, sm), False) for sm in g.smiles.astype(str)], float)
            rec = dict(tag=tag, set=s, view=v, molecule=mol, rr0=(1.0 / (np.flatnonzero(it)[0] + 1)) if it.any() else 0.0, top1_seen=bool(seen[0]))
            for gm in GAMMAS:
                s2 = sc - gm * seen; order = np.argsort(-s2, kind="stable")
                rec[f"g{gm}"] = (1.0 / (int(np.flatnonzero(it[order])[0]) + 1)) if it.any() else 0.0
            rows.append(rec)
R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "diag/x_seenpen.csv"), index=False)
NP = ["NP_H", "NP_X", "NP_N", "D_np_single"]
def d(g, gm): return float((g[f"g{gm}"] - g.rr0).mean())
L = ["# Continuous training-structure penalty S - gamma * seen on the frozen v8w7a top-25 lists (exploratory description; label-using)", "",
     "Score scale: the stored main score (median within-list gap rank1 - rank2 shown below). g = mean C2 delta (NP strata, molecule-weighted over folds), "
     "c = -mean C1 delta (same), pi* = g / (g + c).", ""]
gap = []
for (tag, s, v, m), g in pd.read_parquet(os.path.join(HERE, "diag/top102_np053f1dev.parquet")).groupby(["tag"] if False else ["set", "view", "molecule", "set"]):
    pass
L += ["| gamma | NP C2 g | NP C1 c | NP pi* | other C2 g | other C1 c | other pi* | panel C2 g | panel C1 c | panel pi* |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for gm in GAMMAS:
    out = []
    for msk in (R.set.isin(NP) & (R.tag != "panel"), (~R.set.isin(NP)) & (R.tag != "panel"), R.tag == "panel"):
        g2 = d(R[msk & (R.view == "c2")], gm); c1 = -d(R[msk & (R.view == "c1")], gm)
        pis = g2 / (g2 + c1) if (g2 + c1) > 0 and g2 > 0 else float("nan")
        out += [f"{g2:+.4f}", f"{c1:+.4f}", f"{pis:.2f}"]
    L.append(f"| {gm} | " + " | ".join(out) + " |")
sc = pd.concat([pd.read_parquet(os.path.join(HERE, f"diag/top102_{t}.parquet")) for t in TAGS])
sc = sc[sc["rank"].isin([1, 2])].pivot_table(index=["set", "view", "molecule"], columns="rank", values="score", aggfunc="first").dropna()
L += ["", f"- median score gap rank 1 - rank 2 over all stored lists: {float((sc[1] - sc[2]).median()):.3f} (q25 {float((sc[1] - sc[2]).quantile(0.25)):.3f}, q75 {float((sc[1] - sc[2]).quantile(0.75)):.3f})"]
open(os.path.join(HERE, "diag/x_seenpen.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
