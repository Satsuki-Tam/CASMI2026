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
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries

ap = argparse.ArgumentParser(); ap.add_argument("--eval_csv", required=True); ap.add_argument("--store", required=True); ap.add_argument("--raw", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--max_spectra", type=int, default=16); ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); ap.add_argument("--limit", type=int, default=0, help="first N molecules per set (parity subsets)")
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
mols = pl.read_csv(a.eval_csv).filter(pl.col("set").is_in(a.sets))
if a.limit: mols = pl.concat([mols.filter(pl.col("set") == s_).head(a.limit) for s_ in a.sets])
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
keys = pl.read_parquet(os.path.join(os.path.dirname(a.store), "train_scorer_keys.parquet")).select("inchikey14", "normalized_smiles").unique("inchikey14")
sel = meta.join(mols.select("molecule", "lib"), left_on="inchikey14", right_on="molecule", how="inner").filter((pl.col("ingest_lib") == pl.col("lib")) & pl.col("adduct").is_in(list(ADDUCT_SHIFT)))   # raw inchikey14 + selection library + test adducts, exactly as b1_features (2026-10-25 check)
# query policy shared with the evaluator and the pipeline (b1_common.select_queries): per molecule, store-row order as tie-break, adduct round-robin
add_of = dict(zip(sel["row"].to_list(), sel["adduct"].to_list())); ce_of = dict(zip(sel["row"].to_list(), sel["ce_mean"].to_list()))
rows_by_mol = {}
for r_, k_ in zip(sel["row"].to_list(), sel["inchikey14"].to_list()): rows_by_mol.setdefault(k_, []).append(int(r_))
keep = set()
for k_, rs in rows_by_mol.items(): keep.update(select_queries(sorted(rs), a.max_spectra, add_of.__getitem__, ce_of.__getitem__))
sel = sel.filter(pl.col("row").is_in(sorted(keep)))
assert sel.filter(~pl.col("adduct").is_in(list(ADDUCT_SHIFT)) | (pl.col("ingest_lib") != pl.col("lib"))).height == 0, "selected query outside the selection library / test adducts"
assert sel.group_by("inchikey14").agg(pl.len()).filter(pl.col("len") > a.max_spectra).height == 0, "more than max_spectra queries for a molecule"
rows = sorted(sel["row"].to_list())
raw = pl.scan_parquet(f"{a.raw}/train.parquet").with_row_index("row").filter(pl.col("row").is_in(rows)).select(
    "row", "inchikey14", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type", "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units").collect()
# the evaluator (b1_features) reads enveda-180 positive-mode spectra with the electron-mass correction; the pipeline treats test spectra as
# given, so the same correction is applied here (otherwise the two paths see precursors ~1.5 ppm apart)
lib_of_row = dict(zip(sel["row"].to_list(), sel["ingest_lib"].to_list()))
rows_l = raw["row"].to_list(); shift = [ELECTRON if (lib_of_row.get(r_) == "enveda-180" and m_ == "positive") else 0.0 for r_, m_ in zip(rows_l, raw["ionization_mode"].to_list())]
raw = raw.with_columns(pl.Series("shift", shift))
# the evaluator reads peaks from the float32 spectra store (b1_features: float32 -> float64 - shift); reproduce that precision here, otherwise FPNet
# and the similarity see float64 peaks and a few boundary candidates / rankings differ (parity 2026-10-24)
f32 = lambda xs: np.asarray(xs, np.float32).astype(np.float64).tolist()
raw = raw.with_columns((pl.col("precursor_mz") - pl.col("shift")).alias("precursor_mz"),
                       pl.struct(["ms2_mzs", "shift"]).map_elements(lambda d: [x - d["shift"] for x in f32(d["ms2_mzs"])], return_dtype=pl.List(pl.Float64)).alias("ms2_mzs"),
                       pl.col("ms2_normalized_intensities").map_elements(f32, return_dtype=pl.List(pl.Float64)).alias("ms2_normalized_intensities"))
test = raw.rename({"inchikey14": "molecule_id"}).with_columns(pl.col("row").cast(pl.Int64).alias("spectrum_row"))
test.drop("row", "shift").write_parquet(f"{a.out}/test.parquet")
# per-molecule masks with the evaluator's conventions: C2 hides every reference of the query's own identity (+ train membership);
# C1 keeps the identity but removes the query acquisitions and the truth's references from the query's own library (cross-library matching)
rows_of = {}
for r_, k_ in zip(sel["row"].to_list(), sel["inchikey14"].to_list()): rows_of.setdefault(k_, []).append(int(r_))
rows_of = {k_: sorted(v_) for k_, v_ in rows_of.items()}   # order-independent masks (the pipeline consumes them as sets); stable across rebuilds
mask_c2 = {m: {"ids": [k], "rows": rows_of.get(m, [])} for m, k in zip(mols["molecule"].to_list(), mols["scorer_key"].to_list())}
mask_c1 = {m: {"rows": rows_of.get(m, []), "same_lib": {"identity": k, "lib": l}} for m, k, l in zip(mols["molecule"].to_list(), mols["scorer_key"].to_list(), mols["lib"].to_list())}
json.dump(mask_c2, open(f"{a.out}/mask_c2.json", "w")); json.dump(mask_c1, open(f"{a.out}/mask_c1.json", "w"))
json.dump(dict(max_spectra=a.max_spectra, sets=a.sets, limit=a.limit, electron_shift_enveda180_positive=True, n_molecules=mols.height), open(f"{a.out}/eval_test_manifest.json", "w"), indent=1)
sol = mols.select("molecule", "scorer_key", "set", "group", "lib").join(keys, left_on="molecule", right_on="inchikey14", how="left").rename({"molecule": "molecule_id", "normalized_smiles": "smiles"})
assert sol["smiles"].null_count() == 0, "truth SMILES missing"
sol.write_csv(f"{a.out}/solution.csv")
json.dump(rows, open(f"{a.out}/exclude_rows_c1.json", "w"))
json.dump(sorted(set(mols["scorer_key"].to_list())), open(f"{a.out}/exclude_identities_c2.json", "w"))
print(f"test: {test.height} spectra / {test['molecule_id'].n_unique()} molecules -> {a.out}; adducts {test.group_by('adduct').agg(pl.len()).sort('len', descending=True).to_dict(as_series=False)}")
