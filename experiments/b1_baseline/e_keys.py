"""102 (second engine, E-lite): official scorer keys of the extra E-source layers -> diag/e_window_keys_v2.parquet (key, in_pcl, in_bio) + manifest.
v2 (Codex 102 Q5(1)): every key is RECOMPUTED from a SMILES with the official identity function (RemoveStereochemistry -> TautomerEnumerator()
.Canonicalize -> InChIKey[:14], RDKit of this environment); shipped keys are never trusted as official.
- PubChemLite (pubchemlite_annotations.parquet): SMILES from the PubChem tier (tier_row -> data/external/pubchem_tier) or, without a tier row, from
  the v2 pool (pool_row = pool pid). Rows with neither are left out (they cannot be B1 candidates except through the COCONUT store, whose rows are
  E members via in_coconut anyway) and counted. Mapping sanity: the raw InChIKey14 of the fetched SMILES vs the annotation's ik14.
- BIO (bio_structures.parquet, ChEBI / LIPID MAPS not in COCONUT): SMILES shipped; parse failures are left out (no raw-key fallback) and counted.
Inputs are parquet / npy only. Usage: python -X utf8 e_keys.py [--workers 16] [--out diag/e_window_keys_v2]"""
import argparse, hashlib, json, os
from multiprocessing import Pool
import numpy as np, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
K = f"{ROOT}/data/external_kaggle"


def _keys(smiles):
    """-> list of (official key | None, raw ik14 | None)."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); T = rdMolStandardize.TautomerEnumerator(); out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s)
            if m is None: out.append((None, None)); continue
            raw = Chem.MolToInchiKey(m)[:14]; Chem.RemoveStereochemistry(m); out.append((Chem.MolToInchiKey(T.Canonicalize(m))[:14], raw))
        except Exception:
            out.append((None, None))
    return out


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 24), b""): h.update(c)
    return h.hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=16); ap.add_argument("--out", default="diag/e_window_keys_v2"); a = ap.parse_args()
    PCLP = f"{K}/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet"
    BIOP = f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi-chebi-lmsd-structures/casmi-chebi-lmsd-structures/bio_structures.parquet"
    TIER = f"{ROOT}/data/external/pubchem_tier"; POOLP = f"{ROOT}/data/external/v2_pool/pool_meta.parquet"
    pcl = pl.read_parquet(PCLP, columns=["candidate_key", "ik14", "tier_row", "pool_row"])
    toff = np.load(f"{TIER}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{TIER}/pc_smiles.npy", mmap_mode="r")
    pool = pl.read_parquet(POOLP, columns=["pid", "smiles"]); assert (pool["pid"].to_numpy() == np.arange(pool.height)).all(); psmi = pool["smiles"].to_numpy()
    tr = pcl["tier_row"].fill_null(-1).to_numpy(); pr = pcl["pool_row"].fill_null(-1).to_numpy()
    smi, src = [], []
    for t_, p_ in zip(tr, pr):
        if t_ >= 0:
            s0, s1 = int(toff[t_]), int(toff[t_ + 1]); smi.append(bytes(tbuf[s0:s1]).decode("ascii")); src.append("tier")
        elif p_ >= 0: smi.append(str(psmi[p_])); src.append("pool")
        else: smi.append(None); src.append("none")
    have = [i for i, s in enumerate(smi) if s]
    bio = pl.read_parquet(BIOP, columns=["inchikey14", "smiles"]); bsmi = bio["smiles"].to_list()
    jobs = [smi[i] for i in have] + bsmi
    with Pool(a.workers) as p: res = [r for ch in p.imap(_keys, [jobs[i:i + 200] for i in range(0, len(jobs), 200)], chunksize=1) for r in ch]
    rp, rb = res[:len(have)], res[len(have):]
    ck = pcl["candidate_key"].to_list(); ik = pcl["ik14"].to_list()
    P = {o for o, _ in rp if o}; B = {o for o, _ in rb if o}
    stats = dict(pcl_rows=pcl.height, pcl_smiles_tier=src.count("tier"), pcl_smiles_pool=src.count("pool"), pcl_no_smiles_left_out=src.count("none"),
                 pcl_parse_fail=sum(o is None for o, _ in rp), pcl_raw_vs_annotation_ik14_mismatch=sum(1 for i, (o, r) in zip(have, rp) if r and r != ik[i]),
                 pcl_official_vs_candidate_key_mismatch=sum(1 for i, (o, r) in zip(have, rp) if o and o != ck[i]), pcl_keys=len(P),
                 bio_rows=bio.height, bio_parse_fail_left_out=sum(o is None for o, _ in rb), bio_official_vs_raw_mismatch=sum(1 for (o, r), k_ in zip(rb, bio["inchikey14"].to_list()) if o and o != k_),
                 bio_keys=len(B), overlap=len(P & B))
    keys = sorted(P | B)
    pl.DataFrame(dict(key=keys, in_pcl=[k in P for k in keys], in_bio=[k in B for k in keys])).write_parquet(os.path.join(HERE, a.out + ".parquet"))
    import rdkit
    stats.update(total_keys=len(keys), rdkit=rdkit.__version__, inputs={os.path.basename(x): sha(x)[:16] for x in (PCLP, BIOP, POOLP, f"{TIER}/pc_off.npy", f"{TIER}/pc_smiles.npy")},
                 output_sha=sha(os.path.join(HERE, a.out + ".parquet"))[:16])
    json.dump(stats, open(os.path.join(HERE, a.out + "_manifest.json"), "w"), indent=1); print(json.dumps(stats, indent=1))
