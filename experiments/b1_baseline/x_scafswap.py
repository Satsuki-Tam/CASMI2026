"""Exploratory, label-using DESCRIPTION (not a registered candidate, not a gate): what a structural 'seen-analog swap' would do to the frozen v8w7a
main (diag/top102_<tag>.parquet lists, both views) -- the C2 gain g and the C1 cost c that fix the break-even class-1 share pi_C1 < g / (g + c)
(Codex 116). Rule S_k (no tuned score): if P's rank-1 candidate is a training structure in that view (in_train_c1 / in_train_c2 of the view's
features) and some candidate at ranks 2..k is NOT a training structure, has the SAME molecular formula and the SAME Murcko scaffold as the
rank-1, the best-ranked such candidate moves to rank 1 (the old rank-1 to rank 2, the rest shift). k in {2, 3, 5}. Lists are the stored top
lists (ranks 1..25); RR from the truth's new rank. Usage (Spark, experiments/b1_baseline): python -X utf8 x_scafswap.py"""
import os
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")
HERE = os.path.dirname(os.path.abspath(__file__))
TAGS = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_f0"}
_c = {}
def info(s):
    if s not in _c:
        m = Chem.MolFromSmiles(s)
        _c[s] = (None, None) if m is None else (CalcMolFormula(m), Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(m)))
    return _c[s]
rows = []
for tag, run in TAGS.items():
    p = os.path.join(HERE, f"diag/top102_{tag}.parquet")
    if not os.path.exists(p): print("missing", p); continue
    T = pd.read_parquet(p); T["molecule"] = T.molecule.astype(str)
    for s, ts in T.groupby("set"):
        fp = os.path.join(HERE, run, f"b1_features_{s}.parquet")
        if not os.path.exists(fp): print("missing", fp); continue
        F = pd.read_parquet(fp, columns=["molecule", "smiles", "in_train_c1", "in_train_c2"]); F["molecule"] = F.molecule.astype(str)
        tr = {v: dict(zip(zip(F.molecule, F.smiles), F[f"in_train_{v}"].astype(bool))) for v in ("c1", "c2")}
        for (v, mol), g in ts.groupby(["view", "molecule"]):
            g = g.sort_values("rank"); sm = g.smiles.astype(str).tolist(); it = g.is_truth.astype(bool).tolist()
            r0 = (it.index(True) + 1) if True in it else None
            rec = dict(tag=tag, set=s, view=v, molecule=mol, rr0=0.0 if r0 is None else 1.0 / r0)
            t1_train = tr[v].get((mol, sm[0]), False)
            for k in (2, 3, 5):
                new = r0
                if t1_train and len(sm) > 1:
                    f0, s0 = info(sm[0])
                    for j in range(1, min(k, len(sm))):
                        fj, sj = info(sm[j])
                        if not tr[v].get((mol, sm[j]), False) and fj is not None and fj == f0 and sj == s0:
                            order = [j] + [i for i in range(len(sm)) if i != j]
                            new = (order.index(it.index(True)) + 1) if True in it else None
                            break
                rec[f"rr_S{k}"] = 0.0 if new is None else 1.0 / new
            rows.append(rec)
R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "diag/x_scafswap.csv"), index=False)
L = ["# Seen-analog swap S_k on the frozen v8w7a lists (exploratory description; label-using; not a candidate)", "",
     "| tag | set | view | n | MRR P | dS2 | dS3 | dS5 | rows changed (S5) |", "|---|---|---|---:|---:|---:|---:|---:|---:|"]
for (tag, s, v), g in R.groupby(["tag", "set", "view"], sort=False):
    L.append(f"| {tag} | {s} | {v} | {len(g)} | {g.rr0.mean():.3f} | {(g.rr_S2 - g.rr0).mean():+.4f} | {(g.rr_S3 - g.rr0).mean():+.4f} | {(g.rr_S5 - g.rr0).mean():+.4f} | {int((g.rr_S5 != g.rr0).sum())} |")
open(os.path.join(HERE, "diag/x_scafswap.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
