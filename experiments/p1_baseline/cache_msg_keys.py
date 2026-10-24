"""Cache MassSpecGym identities once: raw InChIKey14 and official scorer keys (RemoveStereo -> tautomer canonical -> IK14).
Usage: python -X utf8 cache_msg_keys.py <MassSpecGym.tsv> <out_dir> [workers]
Writes <out_dir>/msg_raw_keys.txt and <out_dir>/msg_scorer_keys.txt (one key per line) + msg_keys_manifest.json."""
import json, sys, time, hashlib
from multiprocessing import Pool
import polars as pl


def _init():
    global Chem, TAUT
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()


def _key(smi):
    try:
        m = Chem.MolFromSmiles(smi)
        if m is None: return None
        Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]
    except Exception:
        return None


def main():
    tsv, out = sys.argv[1], sys.argv[2]; workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    t0 = time.time()
    msg = pl.read_csv(tsv, separator="\t", columns=["inchikey", "smiles"], infer_schema_length=10000, ignore_errors=True)
    raw = sorted(set(msg["inchikey"].str.slice(0, 14).drop_nulls().to_list()))
    smis = msg["smiles"].drop_nulls().unique().sort().to_list()
    with Pool(workers, initializer=_init) as pool:
        keys = pool.map(_key, smis, chunksize=200)
    sk = sorted({k for k in keys if k})
    open(f"{out}/msg_raw_keys.txt", "w").write("\n".join(raw)); open(f"{out}/msg_scorer_keys.txt", "w").write("\n".join(sk))
    import rdkit
    json.dump(dict(tsv_sha256=hashlib.sha256(open(tsv, "rb").read()).hexdigest(), n_smiles=len(smis), n_raw=len(raw), n_scorer=len(sk), n_failed=sum(k is None for k in keys),
                   rdkit=rdkit.__version__, seconds=round(time.time() - t0)), open(f"{out}/msg_keys_manifest.json", "w"), indent=1)
    print(f"MSG: {len(raw)} raw keys, {len(sk)} scorer keys, {sum(k is None for k in keys)} failed ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
