"""W135 stage 2 (139_decision.md; before any selector result): structural proximity table of the confirmation molecules -- for each molecule of the
fold-2 confirmation batches, the maximum Tanimoto (Morgan radius 2 / 2048 bits on the official-key structure: RemoveStereochemistry -> tautomer
canonical) to the 600 fold-1 design molecules. A descriptive audit of nearness (not a structural isolation); the reader's sensitivity uses the
frozen threshold 0.85. Writes experiments/w135/s2/w135_prox_audit.parquet + .json (counts, hashes).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_prox_audit.py"""
import hashlib, json, os
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); BD = os.path.join(ROOT, "experiments/w135/batches"); OUT = os.path.join(ROOT, "experiments/w135/s2")
os.makedirs(OUT, exist_ok=True); sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
if os.path.exists(os.path.join(OUT, "w135_prox_audit.parquet")): raise SystemExit("REFUSED: the proximity table exists")
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.MolStandardize import rdMolStandardize
RDLogger.DisableLog("rdApp.*"); T = rdMolStandardize.TautomerEnumerator()
st = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet")).select("inchikey14", "smiles").unique("inchikey14"); SMI = dict(zip(st["inchikey14"].to_list(), st["smiles"].to_list()))
def fp(ik):
    m = Chem.MolFromSmiles(SMI.get(ik) or "")
    if m is None: return None
    Chem.RemoveStereochemistry(m); return AllChem.GetMorganFingerprintAsBitVect(T.Canonicalize(m), 2, nBits=2048)
DES = [b for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3")]; CON = ["cF1", "cR1", "cU1", "cF2", "cR2", "cF3", "cR3"]
dm = pd.concat([pd.read_csv(os.path.join(BD, f"{b}.csv")) for b in DES]).molecule.astype(str).tolist(); dfp = [f for f in (fp(m) for m in dm) if f is not None]
rows = []
for b in CON:
    bt = pd.read_csv(os.path.join(BD, f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str)
    for r in bt.itertuples(index=False):
        f = fp(r.molecule); mx = float(max(DataStructs.BulkTanimotoSimilarity(f, dfp))) if f is not None else np.nan
        rows.append(dict(batch=b, molecule=r.molecule, used=bool(r.used), max_tan_design=mx))
X = pd.DataFrame(rows); X.to_parquet(os.path.join(OUT, "w135_prox_audit.parquet"), index=False)
summ = dict(n=len(X), design_fps=len(dfp), ge085=int((X.max_tan_design >= 0.85).sum()), lt085=int((X.max_tan_design < 0.85).sum()), nan=int(X.max_tan_design.isna().sum()),
            by_batch={b: dict(n=int(len(g)), ge085=int((g.max_tan_design >= 0.85).sum())) for b, g in X.groupby("batch")},
            table_sha256=sha(os.path.join(OUT, "w135_prox_audit.parquet")), batches_sha256={b: sha(os.path.join(BD, f"{b}.csv")) for b in DES + CON}, script_sha256=sha(os.path.abspath(__file__)))
json.dump(summ, open(os.path.join(OUT, "w135_prox_audit.json"), "w"), indent=1); print(json.dumps(summ)[:1500])
