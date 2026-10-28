"""Descriptive audit (label-using, no model, not a gate): structural relation between the truth and P's (v8w7a) wrong rank-1 in the C2 errors with
the truth in the list (diag/x_fpcoll.csv rows; FP gap and train flag from diag/x_fpgap.csv). Per row: same Murcko scaffold (RDKit
MurckoScaffold, SMILES equality), same generic scaffold, ring-count difference, sugar rings (pyranose-like SMARTS with 3 O substituents).
Reports NP strata (np053 NP_H/X/N, f1/f2 D) and the other strata separately, split by same scaffold.
Usage: python -I -X utf8 x_errtypes.py <dir with x_fpcoll.csv and x_fpgap.csv> <out.md>"""
import sys
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
RDLogger.DisableLog("rdApp.*")
SRC, OUT = sys.argv[1], sys.argv[2]
C = pd.read_csv(f"{SRC}/x_fpcoll.csv"); G = pd.read_csv(f"{SRC}/x_fpgap.csv")
D = C.merge(G[["tag", "set", "molecule", "gap", "top1_train"]], on=["tag", "set", "molecule"], how="left")
SUGAR = Chem.MolFromSmarts("[OX2;R1]1[CX4;R1][CX4;R1]([OX2])[CX4;R1]([OX2])[CX4;R1]([OX2])[CX4;R1]1")
def feats(s):
    m = Chem.MolFromSmiles(s)
    if m is None: return None
    sc = MurckoScaffold.GetScaffoldForMol(m)
    return dict(scaf=Chem.MolToSmiles(sc), gscaf=Chem.MolToSmiles(MurckoScaffold.MakeScaffoldGeneric(sc)), nsug=len(m.GetSubstructMatches(SUGAR)), nring=m.GetRingInfo().NumRings())
rows = []
for r in D.itertuples(index=False):
    a, b = feats(r.truth), feats(r.top1)
    if a is None or b is None: continue
    rows.append(dict(tag=r.tag, set=r.set, same_formula=bool(r.same_formula), tani=r.tanimoto, same_scaf=a["scaf"] == b["scaf"], same_gscaf=a["gscaf"] == b["gscaf"],
                     sug_t=a["nsug"], ring_diff=a["nring"] - b["nring"], gap=r.gap, top1_train=bool(r.top1_train)))
R = pd.DataFrame(rows); NP = R.set.isin(["NP_H", "NP_X", "NP_N", "D_np_single"])
L = ["# Structural relation of the truth and P's wrong rank-1 (C2 errors with the truth in the list, folds 1+2; descriptive)", "",
     f"rows {len(R)} of {len(D)} (both SMILES parsed)", "",
     "| strata | errors | same formula | same Murcko scaffold (of same-formula) | Tanimoto q25/q50/q75 (same formula) | truth has a sugar ring | top-1 is train | FP prefers truth |",
     "|---|---:|---:|---:|---|---:|---:|---:|"]
for lab, g in (("NP (np053 NP_H/X/N, f1/f2 D)", R[NP]), ("other (C, E, F, G)", R[~NP])):
    sf = g[g.same_formula]; q = np.percentile(sf.tani, [25, 50, 75])
    L.append(f"| {lab} | {len(g)} | {g.same_formula.mean():.2f} | {sf.same_scaf.mean():.2f} | {q[0]:.2f} / {q[1]:.2f} / {q[2]:.2f} | {(sf.sug_t > 0).mean():.2f} | {g.top1_train.mean():.2f} | {(g.gap > 0).mean():.2f} |")
L += ["", "| strata | same scaffold | n | Tanimoto median | top-1 is train | FP prefers truth | median FP gap |", "|---|---|---:|---:|---:|---:|---:|"]
for lab, g in (("NP", R[NP]), ("other", R[~NP])):
    for k, gg in g[g.same_formula].groupby("same_scaf"):
        L.append(f"| {lab} | {k} | {len(gg)} | {gg.tani.median():.2f} | {gg.top1_train.mean():.2f} | {(gg.gap > 0).mean():.2f} | {gg.gap.median():+.1f} |")
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
