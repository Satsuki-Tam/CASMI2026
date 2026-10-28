"""102 (second engine, E-lite): official scorer keys of the extra E-window layers -> diag/e_window_keys.parquet (key, in_pcl, in_bio).
PubChemLite: candidate_key (official, shipped). BIO (ChEBI / LIPID MAPS structures not in COCONUT, bio_structures.parquet): official key
recomputed from its SMILES (RemoveStereochemistry -> TautomerEnumerator().Canonicalize -> InChIKey[:14]); the raw inchikey14 is used only when
the SMILES fails to parse. Inputs are parquet only. Usage: python -X utf8 e_keys.py [--workers 16]"""
import argparse, os
from multiprocessing import Pool
import polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
K = f"{ROOT}/data/external_kaggle"


def _okeys(smiles):
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); T = rdMolStandardize.TautomerEnumerator(); out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s); Chem.RemoveStereochemistry(m); out.append(Chem.MolToInchiKey(T.Canonicalize(m))[:14])
        except Exception:
            out.append(None)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=16); a = ap.parse_args()
    pcl = pl.read_parquet(f"{K}/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet", columns=["candidate_key"])
    bio = pl.read_parquet(f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi-chebi-lmsd-structures/casmi-chebi-lmsd-structures/bio_structures.parquet", columns=["inchikey14", "smiles"])
    smi = bio["smiles"].to_list(); chunks = [smi[i:i + 500] for i in range(0, len(smi), 500)]
    with Pool(a.workers) as p: ok = [k for r in p.map(_okeys, chunks) for k in r]
    raw = bio["inchikey14"].to_list(); bk = [o if o else r for o, r in zip(ok, raw)]
    n_fail = sum(o is None for o in ok); n_diff = sum(o is not None and o != r for o, r in zip(ok, raw))
    P = set(pcl["candidate_key"].drop_nulls().to_list()); B = {k for k in bk if k}
    keys = sorted(P | B)
    pl.DataFrame(dict(key=keys, in_pcl=[k in P for k in keys], in_bio=[k in B for k in keys])).write_parquet(f"{HERE}/diag/e_window_keys.parquet")
    print(f"PubChemLite keys {len(P):,} | BIO structures {len(bk):,} -> keys {len(B):,} (official differs from raw {n_diff:,}, parse failures {n_fail:,}) | overlap {len(P & B):,} | total {len(keys):,}")
