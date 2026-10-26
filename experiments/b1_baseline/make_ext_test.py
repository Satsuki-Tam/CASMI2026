"""065: EXT benchmark = external reference spectra (E0 knowledge table, public MassBank / MoNA / GNPS records) of structures that are NOT in
train.parquet (delta_kind 'structure_without_train_spectrum') -> unseen by every FPNet (full_eval, public folds), every ranker and the
library; a small but clean class-2 / class-3 test (the truth may or may not be in PubChem / COCONUT = reach is part of the measurement).
Writes <out>/test.parquet (competition test schema), solution.csv (molecule_id, scorer_key, smiles, set, group, lib), empty masks, and
ext_manifest.json (counts by source / adduct / instrument, MassSpecGym overlap of the truths = GLACIER/ICEBERG exposure).
Usage: python -I -X utf8 make_ext_test.py --kt <knowledge table dir> --msg data/external/massspecgym/msg_scorer_keys.txt --out DIR [--max_spectra 8]
"""
import argparse, hashlib, json, os, sys
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import ADDUCT_SHIFT, select_queries
ap = argparse.ArgumentParser(); ap.add_argument("--kt", required=True); ap.add_argument("--msg", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--max_spectra", type=int, default=8); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
D = pl.read_parquet(f"{a.kt}/external_reference_spectra/external_delta.parquet")
Q = pl.read_parquet(f"{a.kt}/external_reference_spectra/external_record_quality.parquet").select("record_id", "mass_check_status", "engine_adduct_recognised")
D = D.join(Q, on="record_id", how="left")
counts = dict(records=D.height, new_structure_records=D.filter(pl.col("delta_kind") == "structure_without_train_spectrum").height)
D = D.filter((pl.col("delta_kind") == "structure_without_train_spectrum") & (~pl.col("in_train_structure")))
counts["after_kind"] = D.height
D = D.filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
counts["after_test_adducts"] = D.height
D = D.filter(pl.col("mass_check_status").is_null() | (pl.col("mass_check_status") == "within_diagnostic_threshold"))
counts["after_mass_check"] = D.height
D = D.filter(pl.col("ms2_mzs").list.len() >= 3)
counts["after_min_peaks"] = D.height
D = D.sort(["scorer_key", "record_id"])
rows = []
for key, g in D.group_by("scorer_key", maintain_order=True):
    items = list(range(g.height)); adds = g["adduct"].to_list(); ces = g["collision_energy_ev"].to_list()
    def ce_of(i):
        c = ces[i]
        if c is None: return None
        if isinstance(c, (list, tuple)): return float(np.mean(c)) if len(c) else None
        return None if (isinstance(c, float) and np.isnan(c)) else float(c)
    keep = select_queries(items, a.max_spectra, lambda i: adds[i], ce_of)
    mid = "m_ext_" + hashlib.sha1(str(key[0]).encode()).hexdigest()[:8]
    for i in keep:
        r = g.row(i, named=True)
        rows.append(dict(molecule_id=mid, spectrum_id="s_ext_" + hashlib.sha1(str(r["record_id"]).encode()).hexdigest()[:10],
                         ms2_mzs=[float(x) for x in r["ms2_mzs"]], ms2_normalized_intensities=[float(x) for x in r["ms2_normalized_intensities"]],
                         base_peak_intensity=1.0, adduct=r["adduct"], ionization_mode=r["ionization_mode"], instrument_type=r["instrument_type"],
                         precursor_mz=float(r["precursor_mz"]), collision_energy_orig=str(r.get("collision_energy_orig") or ""),
                         collision_energy_ev=([float(ce_of(i))] if ce_of(i) is not None else None),
                         collision_energy_orig_units=str(r.get("collision_energy_units") or ""), scorer_key=str(key[0]), smiles=r["smiles"], source=r["source"]))
T = pl.DataFrame(rows)
test = T.drop("scorer_key", "smiles", "source")
test.write_parquet(f"{a.out}/test.parquet")
sol = T.group_by("molecule_id", maintain_order=True).agg(pl.col("scorer_key").first(), pl.col("smiles").first(), pl.col("source").first().alias("lib")).with_columns(pl.lit("EXT").alias("set"), pl.lit("diag").alias("group"))
sol.select("molecule_id", "scorer_key", "smiles", "set", "group", "lib").write_csv(f"{a.out}/solution.csv")
json.dump({}, open(f"{a.out}/mask_c2.json", "w")); json.dump({}, open(f"{a.out}/mask_c1.json", "w"))
msg = set(open(a.msg).read().split())
man = dict(counts=counts, molecules=sol.height, spectra=test.height, truths_in_msg=int(sol["scorer_key"].is_in(list(msg)).sum()),
           by_source=T.group_by("source").agg(pl.col("molecule_id").n_unique()).sort("molecule_id", descending=True).to_dict(as_series=False),
           by_adduct=T.group_by("adduct").agg(pl.len()).sort("len", descending=True).to_dict(as_series=False),
           by_instrument=T.group_by("instrument_type").agg(pl.len()).sort("len", descending=True).to_dict(as_series=False), max_spectra=a.max_spectra)
json.dump(man, open(f"{a.out}/ext_manifest.json", "w"), indent=1); print(json.dumps(man, indent=1)[:2500])
