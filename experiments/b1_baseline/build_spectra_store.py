"""B1 data layer: flat, memory-mappable store of all train MS/MS spectra for library search.

Writes <out>/spec_mz.npy (float32), <out>/spec_int.npy (float32), <out>/spec_off.npy (int64, len n+1) in train.parquet row order, and
<out>/spec_meta.parquet (row, inchikey14, ingest_lib, adduct, ionization_mode, instrument_type, precursor_mz, ce_mean, n_peaks,
scorer_ik14 via train_scorer_keys) plus <out>/structure_rows.parquet (inchikey14 -> sorted row ids) for per-structure access.
Usage: python -X utf8 build_spectra_store.py <raw_dir> <processed_dir> <out_dir>
"""
import json, os, sys, time
import numpy as np, polars as pl, pyarrow.parquet as pq

RAW, PROC, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True); t0 = time.time()
pf = pq.ParquetFile(f"{RAW}/train.parquet")
cols = ["inchikey14", "ingest_lib", "adduct", "ionization_mode", "instrument_type", "precursor_mz", "collision_energy_ev", "ms2_mzs", "ms2_normalized_intensities"]
mz_parts, it_parts, lens, metas = [], [], [], []
n = 0
for b in pf.iter_batches(batch_size=100_000, columns=cols):
    d = b.to_pydict() if False else None
    mz = b.column("ms2_mzs"); it = b.column("ms2_normalized_intensities")
    # flatten list arrays (chunked)
    for chunk_mz, chunk_it in zip(mz.chunks if hasattr(mz, "chunks") else [mz], it.chunks if hasattr(it, "chunks") else [it]):
        off = np.asarray(chunk_mz.offsets); lens.append(np.diff(off).astype(np.int64))
        mz_parts.append(np.asarray(chunk_mz.flatten(), dtype=np.float32)); it_parts.append(np.asarray(chunk_it.flatten(), dtype=np.float32))
    tb = pl.from_arrow(b.select(["inchikey14", "ingest_lib", "adduct", "ionization_mode", "instrument_type", "precursor_mz", "collision_energy_ev"]))
    tb = tb.with_columns(pl.col("collision_energy_ev").list.mean().alias("ce_mean")).drop("collision_energy_ev")
    metas.append(tb); n += b.num_rows
    if n % 500_000 < 100_000: print(f"  {n:,} rows ({time.time()-t0:.0f}s)", flush=True)
mz_all = np.concatenate(mz_parts); it_all = np.concatenate(it_parts); lens = np.concatenate(lens)
off = np.zeros(len(lens) + 1, np.int64); np.cumsum(lens, out=off[1:])
assert off[-1] == len(mz_all) == len(it_all), (off[-1], len(mz_all), len(it_all))
np.save(f"{OUT}/spec_mz.npy", mz_all); np.save(f"{OUT}/spec_int.npy", it_all); np.save(f"{OUT}/spec_off.npy", off)
meta = pl.concat(metas).with_row_index("row").with_columns(pl.Series("n_peaks", lens))
keys = pl.read_parquet(f"{PROC}/train_scorer_keys.parquet").select("inchikey14", "scorer_ik14").unique("inchikey14")
meta = meta.join(keys, on="inchikey14", how="left")
meta.write_parquet(f"{OUT}/spec_meta.parquet")
rows = meta.group_by("inchikey14").agg(pl.col("row").sort().alias("rows"), pl.len().alias("n_spectra"), pl.col("scorer_ik14").first())
rows.write_parquet(f"{OUT}/structure_rows.parquet")
json.dump(dict(n_spectra=int(len(lens)), n_peaks=int(off[-1]), n_structures=rows.height, seconds=round(time.time() - t0),
               mz_bytes=int(mz_all.nbytes), it_bytes=int(it_all.nbytes)), open(f"{OUT}/MANIFEST.json", "w"), indent=1)
print(f"done: {len(lens):,} spectra, {off[-1]:,} peaks, {rows.height:,} structures, {time.time()-t0:.0f}s")
