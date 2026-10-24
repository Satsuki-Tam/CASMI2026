"""Write lightweight metadata parquet files (no peak-list columns) for fast EDA.

Usage: python -I src/make_meta.py data/raw data/processed
"""
import sys, time
from pathlib import Path
import polars as pl

raw, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
t0 = time.time()

train = (
    pl.scan_parquet(raw / "train.parquet")
    .with_row_index("row_id")
    .select(
        "row_id", "ingest_lib", "normalized_smiles", "inchikey", "inchikey14", "molecular_formula",
        "ionization_mode", "instrument_type", "adduct", "adduct_orig", "precursor_mz", "precursor_error_ppm",
        "num_peaks", "base_peak_intensity", "collision_energy_orig", "collision_energy_orig_units",
        pl.col("collision_energy_ev").list.len().alias("n_ce"),
        pl.col("collision_energy_ev").list.min().alias("ce_min"),
        pl.col("collision_energy_ev").list.max().alias("ce_max"),
        pl.col("ms2_mzs").list.min().alias("mz_min"),
        pl.col("ms2_mzs").list.max().alias("mz_max"),
        pl.col("ms2_normalized_intensities").list.max().alias("int_max"),
        pl.col("ms2_normalized_intensities").list.sum().alias("int_sum"),
    )
    .collect()
)
train.write_parquet(out / "train_meta.parquet")
print(f"train_meta: {train.shape} -> {out/'train_meta.parquet'} ({(out/'train_meta.parquet').stat().st_size/1e6:.1f} MB) in {time.time()-t0:.1f}s")

mols = (
    train.group_by("inchikey14")
    .agg(
        pl.col("normalized_smiles").mode().first().alias("smiles"),
        pl.col("molecular_formula").mode().first().alias("formula"),
        pl.len().alias("n_spectra"),
        pl.col("ingest_lib").n_unique().alias("n_libs"),
        pl.col("ingest_lib").unique().sort().str.join("|").alias("libs"),
        pl.col("adduct").n_unique().alias("n_adducts"),
        pl.col("ionization_mode").n_unique().alias("n_polarities"),
        (pl.col("instrument_type") == "timsTOF").any().alias("has_timstof"),
    )
    .sort("n_spectra", descending=True)
)
mols.write_parquet(out / "train_molecules.parquet")
print(f"train_molecules: {mols.shape} -> {out/'train_molecules.parquet'}")

test = (
    pl.read_parquet(raw / "test.parquet")
    .select(
        "molecule_id", "spectrum_id", "adduct", "ionization_mode", "instrument_type", "precursor_mz",
        "base_peak_intensity", "collision_energy_orig", "collision_energy_orig_units",
        pl.col("collision_energy_ev").list.len().alias("n_ce"),
        pl.col("ms2_mzs").list.len().alias("num_peaks"),
        pl.col("ms2_mzs").list.max().alias("mz_max"),
    )
)
test.write_parquet(out / "test_meta.parquet")
print(f"test_meta: {test.shape} -> {out/'test_meta.parquet'}")
print(f"done in {time.time()-t0:.1f}s")
