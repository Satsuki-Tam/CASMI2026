"""Codex 030 pre-training audit for the per-condition library support (b1_features --lib_conditions).

Diagnostics only (labels are used here to MEASURE, never to compute the features):
 1. coverage: share of candidates / molecules with lib_sup2 observed (>= 2 comparable query conditions), raw query counts;
 2. matched comparison: within bins of the maximum library similarity (lib_sim) and of the number of conditions, is lib_sup2 (the second-best
    condition) higher for the truth than for decoys that also have references? (C1 view: truth with other-library references);
 3. the best library match per molecule (c_L = argmax lib_sim among candidates with references): P(c_L is the truth) by bins of its lib_sup2
    and of its gap (lib_sim - lib_sup2), at matched lib_sim -- the decision the ranker would face;
 4. the same tables for a symmetric-mask build (query library removed for every candidate) when --sym_run is given: an effect that vanishes
    there exploited the evaluation mask, not the spectra.
Usage: python -X utf8 lc_audit.py --runs RUN:SET[,SET...] ... [--sym_runs ...] --out diag/lc_audit.md
"""
import argparse, glob, os
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--sym_runs", nargs="*", default=[]); ap.add_argument("--out", default="diag/lc_audit.md")
a = ap.parse_args()


def load(specs):
    out = []
    for sp in specs:
        run, sets = sp.split(":");
        for s in sets.split(","):
            f = pd.read_parquet(f"{run}/b1_features_{s}.parquet"); f["run"] = os.path.basename(run); out.append(f)
    return pd.concat(out, ignore_index=True)


def tables(F, label):
    L = [f"## {label}", ""]
    for v in ("c1", "c2"):
        g = F[F[f"in_short_{v}"]].copy()
        has = g[f"lib_sim_{v}"] > 0; obs = np.isfinite(g[f"lib_sup2_{v}"])
        L.append(f"### view {v.upper()}: shortlist rows {len(g):,} | with references {int(has.sum()):,} | lib_sup2 observed {int(obs.sum()):,} | "
                 f"molecules with any observed {g[obs].molecule.nunique()} of {g.molecule.nunique()} | truth rows with references {int((has & g.is_truth).sum())} (observed {int((obs & g.is_truth).sum())})")
        if v == "c1":
            h = g[has & obs].copy()
            h["sim_bin"] = pd.cut(h[f"lib_sim_{v}"], [0, 0.5, 0.7, 0.85, 1.01], right=False)
            h["ncond_bin"] = np.where(h[f"lib_ncond_{v}"] >= 3, "3+", "2")
            t = h.groupby(["sim_bin", "ncond_bin", "is_truth"], observed=True)[f"lib_sup2_{v}"].agg(["count", "median", "mean"]).round(3)
            L += ["", "matched comparison (rows with references and >= 2 conditions): lib_sup2 by max-similarity bin x condition count x truth", "", "```", t.to_string(), "```"]
        # best library match per molecule
        h = g[has].copy()
        if len(h):
            top = h.loc[h.groupby("molecule")[f"lib_sim_{v}"].idxmax()].copy()
            top["gap"] = top[f"lib_sim_{v}"] - top[f"lib_sup2_{v}"]
            top["sim_bin"] = pd.cut(top[f"lib_sim_{v}"], [0, 0.5, 0.7, 0.85, 1.01], right=False)
            top["sup_bin"] = pd.cut(top["gap"], [-0.01, 0.05, 0.15, 1.01], right=False).astype(str).where(np.isfinite(top["gap"]), "unobserved")
            t2 = top.groupby(["sim_bin", "sup_bin"], observed=True).is_truth.agg(["count", "mean"]).round(3).rename(columns={"mean": "P(c_L is truth)"})
            L += ["", f"best library match c_L per molecule ({len(top)} molecules): P(c_L is the truth) by max similarity x gap to the second condition", "", "```", t2.to_string(), "```", ""]
    return L


F = load(a.runs)
L = ["# Per-condition library support: pre-training audit (Codex 030)", "", f"runs: {a.runs}", ""] + tables(F, "standard tables (training / evaluation masks)")
if a.sym_runs:
    L += tables(load(a.sym_runs), "symmetric-mask diagnostic (query library removed for every candidate in the C1 view)")
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))
