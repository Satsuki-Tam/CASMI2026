"""Build a test-format parquet from frozen evaluation molecules so the SUBMISSION pipeline itself can be evaluated (Codex 007, W6/W7).

For every molecule of the selection CSV: its spectra from the selection library with test adducts (up to --max_spectra, adduct round-robin,
the pipeline applies its own policy on top) are written in the test.parquet schema, the truth SMILES goes to a separate solution CSV, and
two mask files are produced for the pipeline's evaluation mode:
  exclude_rows_c1.json   : store rows of the query acquisitions themselves (the pipeline additionally drops exact / near duplicates)
  exclude_identities_c2.json : official scorer keys of the truths (all their references removed, train membership hidden -> class-2 proxy)
Usage: python -X utf8 make_eval_test.py --eval_csv p1_molecules.csv --store DIR --raw DIR --out DIR [--max_spectra 16] [--sets A_timstof B_nplib]
"""
import argparse, json, os
import numpy as np, polars as pl
from b1_common import ADDUCT_SHIFT

ap = argparse.ArgumentParser(); ap.add_argument("--eval_csv", required=True); ap.add_argument("--store", required=True); ap.add_argument("--raw", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--max_spectra", type=int, default=16); ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"])
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
mols = pl.read_csv(a.eval_csv).filter(pl.col("set").is_in(a.sets))
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
keys = pl.read_parquet(os.path.join(os.path.dirname(a.store), "train_scorer_keys.parquet")).select("inchikey14", "normalized_smiles").unique("inchikey14")
sel = meta.join(mols.select("molecule", "lib"), left_on="inchikey14", right_on="molecule", how="inner").filter((pl.col("ingest_lib") == pl.col("lib")) & pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
# adduct round-robin per molecule, [M+H]+ first, then by CE
sel = sel.with_columns(pl.col("ce_mean").fill_null(0.0), (pl.col("adduct") != "[M+H]+").cast(pl.Int8).alias("not_mh"))
sel = sel.sort(["inchikey14", "not_mh", "adduct", "ce_mean"]).with_columns(pl.col("row").cum_count().over(["inchikey14", "adduct"]).alias("k_in_adduct"))
sel = sel.sort(["inchikey14", "k_in_adduct", "not_mh", "adduct"]).with_columns(pl.col("row").cum_count().over("inchikey14").alias("k")).filter(pl.col("k") <= a.max_spectra)
rows = sorted(sel["row"].to_list())
raw = pl.scan_parquet(f"{a.raw}/train.parquet").with_row_index("row").filter(pl.col("row").is_in(rows)).select(
    "row", "inchikey14", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type", "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units").collect()
test = raw.rename({"inchikey14": "molecule_id"}).with_columns(pl.col("row").cast(pl.Int64).alias("spectrum_row"))
test.drop("row").write_parquet(f"{a.out}/test.parquet")
sol = mols.select("molecule", "scorer_key", "set", "group", "lib").join(keys, left_on="molecule", right_on="inchikey14", how="left").rename({"molecule": "molecule_id", "normalized_smiles": "smiles"})
assert sol["smiles"].null_count() == 0, "truth SMILES missing"
sol.write_csv(f"{a.out}/solution.csv")
json.dump(rows, open(f"{a.out}/exclude_rows_c1.json", "w"))
json.dump(sorted(set(mols["scorer_key"].to_list())), open(f"{a.out}/exclude_identities_c2.json", "w"))
print(f"test: {test.height} spectra / {test['molecule_id'].n_unique()} molecules -> {a.out}; adducts {test.group_by('adduct').agg(pl.len()).sort('len', descending=True).to_dict(as_series=False)}")
