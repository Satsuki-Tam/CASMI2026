"""Descriptive audit of the existing v8w7a main (diag/top102_<tag>.parquet, diag/r102_<tag>.csv; no new model): for C2 rows where the main misses
rank 1 while the truth is in the view list (rP > 1), compare the main's rank-1 structure with the truth: same molecular formula, IDENTICAL
10,226-bit fingerprint vector (casmi.chem.raw_fingerprint[fp_bits]; a collision no fingerprint-based score -- FPNet f.z, single-spectrum mean,
or a fingerprint-MLP molecule encoder -- can separate), Tanimoto on those bits. Also: how often the truth collides with ANY same-formula candidate
of the view list. Usage (Spark, experiments/b1_baseline): python -X utf8 x_fpcoll.py"""
import os, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CODE = os.path.join(ROOT, "data", "external", "v3_models", "code"); BITS = os.path.join(ROOT, "data", "external", "fold_safe_fpnet", "fp_bits.npy")
TAGS = {"f1dev": "run_f1dev", "np053f1dev": "run_np053_f1dev", "f2dev": "run_f2dev", "np053f2dev": "run_np053_f2dev"}


def _init():
    global chem, B, Chem, CalcMolFormula
    sys.path.insert(0, CODE)
    from casmi import chem
    from rdkit import Chem, RDLogger
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    RDLogger.DisableLog("rdApp.*"); B = np.load(BITS)


def _fp(smis):
    out = []
    for s in smis:
        f = chem.raw_fingerprint(s); m = Chem.MolFromSmiles(s)
        out.append((None if f is None else np.packbits(np.asarray(f[B], np.uint8)).tobytes(), CalcMolFormula(m) if m is not None else None))
    return out


def tani(a, b):
    x = np.unpackbits(np.frombuffer(a, np.uint8)); y = np.unpackbits(np.frombuffer(b, np.uint8)); u = int((x | y).sum())
    return float((x & y).sum() / u) if u else 1.0


rows = []; need = set(); frames = {}
for tag, run in TAGS.items():
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv"), usecols=["set", "view", "molecule", "main", "rP"]); R = R[(R.view == "c2") & (R.rP > 1)]
    T = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); T = T[(T.view == "c2") & (T["rank"] == 1)].set_index(["set", "molecule"])
    for s, g in R.groupby("set"):
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "is_truth", "in_short_c2", "in_tier", "in_coconut", "in_train_c2"])
        F = F[F.in_short_c2.astype(bool) & (F.in_tier.astype(bool) | F.in_coconut.astype(bool) | F.in_train_c2.astype(bool))]
        frames[(tag, s)] = F; need |= set(F.smiles.astype(str))
        for r in g.itertuples(index=False):
            t = F[(F.molecule == r.molecule) & F.is_truth.astype(bool)]
            if not len(t) or (s, r.molecule) not in T.index: continue
            rows.append(dict(tag=tag, set=s, molecule=r.molecule, main=r.main, truth=str(t.smiles.values[0]), top1=str(T.loc[(s, r.molecule), "smiles"])))
need = sorted(need)
with Pool(12, initializer=_init) as p: res = p.map(_fp, [need[i:i + 2000] for i in range(0, len(need), 2000)])
FP = dict(zip(need, [x for r in res for x in r]))
D = pd.DataFrame(rows)
D["same_formula"] = [FP[a][1] is not None and FP[a][1] == FP[b][1] for a, b in zip(D.truth, D.top1)]
D["fp_identical"] = [FP[a][0] is not None and FP[a][0] == FP[b][0] for a, b in zip(D.truth, D.top1)]
D["tanimoto"] = [tani(FP[a][0], FP[b][0]) if FP[a][0] is not None and FP[b][0] is not None else np.nan for a, b in zip(D.truth, D.top1)]
anyc = []
for r in D.itertuples(index=False):
    F = frames[(r.tag, r.set)]; g = F[F.molecule == r.molecule]; tf, tb = FP[r.truth][1], FP[r.truth][0]
    anyc.append(any((FP[x][1] == tf and FP[x][0] == tb) for x in g.smiles.astype(str) if x != r.truth))
D["truth_collides_any"] = anyc
L = ["# FP-collision audit of the v8w7a main's C2 errors with the truth in the list (rP > 1)", "",
     "| tag set | errors | top-1 same formula | top-1 FP-identical to truth | truth FP-identical to any same-formula candidate | median Tanimoto top-1 vs truth | share Tanimoto >= 0.9 |", "|---|---:|---:|---:|---:|---:|---:|"]
for (tag, s), g in D.groupby(["tag", "set"], sort=False):
    L.append(f"| {tag} {s} | {len(g)} | {g.same_formula.mean():.3f} | {g.fp_identical.mean():.3f} | {g.truth_collides_any.mean():.3f} | {g.tanimoto.median():.3f} | {(g.tanimoto >= 0.9).mean():.3f} |")
L.append(f"| **all** | {len(D)} | {D.same_formula.mean():.3f} | {D.fp_identical.mean():.3f} | {D.truth_collides_any.mean():.3f} | {D.tanimoto.median():.3f} | {(D.tanimoto >= 0.9).mean():.3f} |")
D.to_csv(os.path.join(HERE, "diag/x_fpcoll.csv"), index=False)
open(os.path.join(HERE, "diag/x_fpcoll.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
