"""Exploratory (transductive generation potential): for each molecule of a set, is its official key produced by b1_gen.derive (1-2 biosynthetic
edits, exact-mass check) from ANOTHER molecule of the same set used as the parent (test-side parent, label-free at inference only if the parent's
identity is known/predicted; here the TRUE structures are used = an upper bound of the potential)? Compares the panel (Enveda NP examples) with
random NP sets. Usage: python -X utf8 tgen_panel.py CSV [CSV ...]"""
import sys, os, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_gen as G
from rdkit import Chem, RDLogger
from rdkit.Chem.Descriptors import ExactMolWt
RDLogger.DisableLog("rdApp.*")
tk = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "processed", "train_scorer_keys.parquet")).select("scorer_ik14", "normalized_smiles").unique("scorer_ik14")
SMI = dict(zip(tk["scorer_ik14"].to_list(), tk["normalized_smiles"].to_list()))
def job(args):
    i, keys, smis, masses = args
    hits = []
    for j in range(len(keys)):
        if j == i or smis[j] is None: continue
        try: prods = G.derive(smis[j], masses[i])
        except Exception: continue
        if any(G.official_key(ps) == keys[i] for ps in prods): hits.append(j)
    return i, hits
if __name__ == "__main__":
    for csv in sys.argv[1:]:
        d = pd.read_csv(csv); keys = d.scorer_key.astype(str).tolist(); smis = [SMI.get(k) for k in keys]
        masses = [ExactMolWt(Chem.MolFromSmiles(s)) if s else np.nan for s in smis]
        t0 = time.time()
        with Pool(16) as p: res = dict(p.map(job, [(i, keys, smis, masses) for i in range(len(keys))], chunksize=4))
        n_hit = sum(1 for v in res.values() if v)
        print(f"{csv}: molecules {len(keys)}, derivable from another molecule of the set (1-2 edits): {n_hit} ({n_hit / len(keys):.1%}) [{time.time() - t0:.0f}s]", flush=True)
