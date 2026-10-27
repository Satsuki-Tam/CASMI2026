"""Exploratory (not registered): B-restricted ranking on development tables = the Public probe's policy (keep only COCONUT non-train candidates
of each list, order kept, MRR@25 of the truth among them; truths outside B score 0). Scorers available from the tables + GL jsons without
re-running the evaluator: FP, prior (pop_public), GL z, fixed S = z(fp) + 2 z(gl) + 0.5 pop, and the main (v4b + anaw0.5) approximated
from the gen_eval2d top-10 dump (exact when the truth's overall rank <= 10). Also counts B truths in the window but outside the C2 shortlist."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_evaluate import z, term
def rr_b(score, isB, tr):
    o = np.argsort(-score, kind="stable"); ob = [i for i in o if isB[i]][:25]
    for k, i in enumerate(ob):
        if tr[i]: return 1.0 / (k + 1)
    return 0.0
rows = []
for k in (1, 2):
    run = f"run_np053_f{k}dev"; s = "NP_H"
    F = pd.read_parquet(f"{run}/b1_features_{s}.parquet"); F["molecule"] = F.molecule.astype(str)
    M = pd.read_csv(f"{run}/b1_molecules_{s}.csv"); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    gl = json.load(open(f"{run}/work/gl_{s}.json"))
    D = pd.read_parquet(f"diag/e072_top_v4b_np053f{k}dev.parquet"); D = D[D.view == "c2"]; D["molecule"] = D.molecule.astype(str)
    for mid, g0 in F.groupby("molecule", sort=False):
        keep = g0.in_short_c2.values.astype(bool) & (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
        g = g0[keep].reset_index(drop=True)
        if not len(g): rows.append(dict(fold=k, molecule=mid, nB=0)); continue
        isB = (g.in_coconut.values.astype(bool) & ~g.in_train_c2.values.astype(bool)); tr = g.is_truth.values.astype(bool)
        fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float)
        glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
        zg = term(glv, True); S = z(fp) + (2 * zg if zg is not None else 0) + 0.5 * pop
        r = dict(fold=k, molecule=mid, nB=int(isB.sum()), truthB=bool((tr & isB).any()),
                 fp=rr_b(np.nan_to_num(fp, nan=-1e9), isB, tr), prior=rr_b(pop + 1e-6 * np.nan_to_num(fp, nan=-1e9), isB, tr),
                 gl=rr_b(np.nan_to_num(glv, nan=-1e9), isB, tr) if np.isfinite(glv).any() else np.nan, S=rr_b(S, isB, tr))
        d = D[D.molecule == mid]
        if len(d):
            tr_rank = d[d.is_truth]["rank"].min() if d.is_truth.any() else np.nan
            top = d[d["rank"] <= 10].sort_values("rank")
            if np.isfinite(tr_rank) and tr_rank <= 10:
                above_B = int(((top["rank"] < tr_rank) & top.in_coconut & ~top.in_train).sum()); r["main"] = 1.0 / (above_B + 1) if bool((d.is_truth & d.in_coconut & ~d.in_train).any()) else 0.0
            else: r["main"] = np.nan   # truth beyond rank 10 (or absent): not exact from the dump
        rows.append(r)
R = pd.DataFrame(rows)
print("molecules", len(R), "| truth in B (C2 shortlist):", int(R.truthB.fillna(False).sum()), "| median #B candidates", float(R.nB.median()))
for c in ("fp", "prior", "gl", "S", "main"):
    v = R[c]; print(f"  B-restricted MRR by {c:6s}: {v.mean():.4f} (n {int(v.notna().sum())})" + ("  [main: exact only where truth rank <= 10]" if c == "main" else ""))
sub = R[R.main.notna()]
print("  on the rows where main is exact:", {c: round(float(sub[c].mean()), 4) for c in ("fp", "prior", "gl", "S", "main")}, "n", len(sub))
