"""089 stage (a) reading under the amended registration (Codex 088 contract): dreams_fp_eval_f{1,2}/units.csv.
Primary: COCONUT-truth identities, identity score = mean RR@25 over its units; E - F per fold (F = production-merged fold-safe FPNet, E = z(F) + z(D));
gate: both folds >= +0.01 and the fold-equal pooled difference has a paired bootstrap (2,000, identities resampled within fold) 95% lower bound > 0.
Diagnostics only: D alone, E05, ES, Fs; non-COCONUT; library / polarity / adduct class; reach; window size; rescue / corruption; same-formula ranks."""
import json, os
import numpy as np, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(0)
M = ["F", "Fs", "D", "E", "E05", "ES"]
U = {k: pl.read_csv(os.path.join(HERE, f"dreams_fp_eval_f{k}/units.csv")) for k in (1, 2)}
def ident(u): return u.group_by("pid").agg(pl.col("coco").first(), *[pl.col(f"rr_{c}").mean() for c in M])
I = {k: ident(u) for k, u in U.items()}
L = ["# 089 stage (a) reading (DreaMS-FP head vs fold-safe FPNet, Codex 088 contract)", ""]
L += ["| fold | stratum | identities | units | reached units | " + " | ".join(f"MRR {c}" for c in M) + " | E - F |", "|---|---|---:|---:|---:|" + "---:|" * (len(M) + 1)]
for k in (1, 2):
    for nm, f in (("COCONUT", pl.col("coco")), ("non-COCONUT", ~pl.col("coco"))):
        J = I[k].filter(f); uu = U[k].filter(f)
        L.append(f"| {k} | {nm} | {J.height} | {uu.height} | {int(uu['reached'].sum())} | " + " | ".join(f"{J[f'rr_{c}'].mean():.4f}" for c in M) + f" | {(J['rr_E'] - J['rr_F']).mean():+.4f} |")
d = {k: (I[k].filter(pl.col("coco"))["rr_E"] - I[k].filter(pl.col("coco"))["rr_F"]).to_numpy() for k in (1, 2)}
pt = 0.5 * (d[1].mean() + d[2].mean())
bs = np.array([0.5 * (d[1][rng.integers(0, len(d[1]), len(d[1]))].mean() + d[2][rng.integers(0, len(d[2]), len(d[2]))].mean()) for _ in range(2000)])
lo, hi = np.percentile(bs, [2.5, 97.5])
gate = d[1].mean() >= 0.01 and d[2].mean() >= 0.01 and lo > 0
L += ["", f"**Primary (COCONUT identities)**: fold 1 E - F {d[1].mean():+.4f}, fold 2 {d[2].mean():+.4f}; pooled {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]",
      f"**GATE to stage (b): {'PASS' if gate else 'FAIL'}**", ""]
A = pl.concat([U[1].with_columns(pl.lit(1).alias("fold")), U[2].with_columns(pl.lit(2).alias("fold"))])
R = A.filter(pl.col("reached"))
L += ["Diagnostics (units, both folds; RR@25 means; reached units only for the by-group rows)", "",
      "| group | units | " + " | ".join(M) + " | E - F |", "|---|---:|" + "---:|" * (len(M) + 1)]
for col in ("lib", "mode", "addcls"):
    for (g,), G in R.group_by(col):
        if G.height < 50: continue
        L.append(f"| {col}={g} | {G.height} | " + " | ".join(f"{G[f'rr_{c}'].mean():.4f}" for c in M) + f" | {(G['rr_E'] - G['rr_F']).mean():+.4f} |")
for nm, f in (("COCONUT", pl.col("coco")), ("non-COCONUT", ~pl.col("coco"))):
    G = R.filter(f)
    top_F = G["rank_F"] == 1; top_E = G["rank_E"] == 1
    L.append(f"- {nm} reached units {G.height}: rescue (E top-1, F not) {int((top_E & ~top_F).sum())}, corruption (F top-1, E not) {int((top_F & ~top_E).sum())}; "
             f"same-formula MRR F {G['rrsf_F'].mean():.4f} / D {G['rrsf_D'].mean():.4f} / E {G['rrsf_E'].mean():.4f}; median window {int(G['n_cand'].median())}")
L.append(f"- reach: {int(A['reached'].sum())}/{A.height} units; D missing units {int((~A['d_ok']).sum())}")
mona = R.filter(pl.col("lib") == "mona")
if mona.height: L.append(f"- MoNA units (DreaMS backbone exposure caveat): {mona.height}, E - F {(mona['rr_E'] - mona['rr_F']).mean():+.4f}")
open(os.path.join(HERE, "diag/x089_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
