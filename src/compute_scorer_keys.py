"""Precompute the scorer identity key (tautomer-canonical InChIKey14, RDKit 2026.03.3) for every
unique training SMILES, in parallel.

Usage: python -I src/compute_scorer_keys.py data/processed/train_meta.parquet data/processed/train_scorer_keys.parquet
Output columns: normalized_smiles, inchikey14 (stored), scorer_ik14, key_changed
"""
import os, sys, time
from multiprocessing import Pool
from pathlib import Path

import polars as pl


def _init():
    global canon
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from metric import canonicalize_smiles_to_ik14 as canon  # noqa: F401


def _work(smiles_chunk):
    return [canon(s) for s in smiles_chunk]


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    t0 = time.time()
    pairs = (
        pl.scan_parquet(src)
        .select("normalized_smiles", "inchikey14")
        .unique()
        .sort("normalized_smiles")
        .collect()
    )
    smiles = pairs["normalized_smiles"].to_list()
    n = len(smiles)
    workers = max(1, (os.cpu_count() or 4) - 2)
    chunk = 500
    chunks = [smiles[i:i + chunk] for i in range(0, n, chunk)]
    print(f"{n:,} unique SMILES, {len(chunks)} chunks, {workers} workers", flush=True)
    keys = []
    with Pool(workers, initializer=_init) as pool:
        for i, res in enumerate(pool.imap(_work, chunks, chunksize=1)):
            keys.extend(res)
            if (i + 1) % 50 == 0:
                done = len(keys)
                print(f"  {done:,}/{n:,}  {time.time()-t0:.0f}s", flush=True)
    out = pairs.with_columns(pl.Series("scorer_ik14", keys, dtype=pl.Utf8)).with_columns(
        (pl.col("scorer_ik14") != pl.col("inchikey14")).alias("key_changed"))
    out.write_parquet(dst)
    print(f"wrote {dst} rows={out.height:,} unparsable={out['scorer_ik14'].null_count():,} "
          f"key_changed={out['key_changed'].sum():,} ({out['key_changed'].mean()*100:.2f}%) in {time.time()-t0:.0f}s")
    merged = out.group_by("scorer_ik14").agg(pl.col("inchikey14").n_unique().alias("n")).filter(pl.col("n") > 1)
    print(f"scorer keys that merge >1 stored inchikey14: {merged.height:,}")


if __name__ == "__main__":
    main()
