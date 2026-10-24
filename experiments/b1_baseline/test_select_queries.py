"""Codex 015 (c): one query-selection function for the evaluator, the pipeline and the test builder. This test replays the three LEGACY
implementations (copied verbatim from the 2026-10-25 code) against b1_common.select_queries on the real inputs (spectra store + evaluation
molecules + the W7 test file) and checks that (1) each path's selection is unchanged and (2) the evaluator and the pipeline select the same
store rows for every W7 molecule. CPU only, ~1 min.
Usage: python -X utf8 test_select_queries.py --store data/processed/spectra_store --eval_csv eval_set/p1_molecules.csv --test eval_test_full3/test.parquet
"""
import argparse, sys, os
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import ADDUCT_SHIFT, select_queries

ap = argparse.ArgumentParser(); ap.add_argument("--store", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--test", default="")
ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); a = ap.parse_args()
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
add_of_row = meta["adduct"].to_numpy(); lib_of_row = meta["ingest_lib"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
mols = pl.read_csv(a.eval_csv).filter(pl.col("set").is_in(a.sets))
fails = 0

# ---- (1) evaluator path: legacy inline loop vs shared function
def legacy_features(qrows, max_spectra):
    by_add = {}
    for x in sorted(sorted(qrows), key=lambda x: (add_of_row[x] != "[M+H]+", add_of_row[x], ce_of_row[x] if np.isfinite(ce_of_row[x]) else 0)):
        by_add.setdefault(add_of_row[x], []).append(x)
    q = []
    while len(q) < max_spectra and any(by_add.values()):
        for ad in list(by_add):
            if by_add[ad] and len(q) < max_spectra: q.append(by_add[ad].pop(0))
    return q
feat_sel = {}
for mid, lib in zip(mols["molecule"].to_list(), mols["lib"].to_list()):
    qrows = [int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT]
    for mq in (8, 16):
        old = legacy_features(qrows, mq); new = select_queries(sorted(qrows), mq, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        if old != new: fails += 1; print("EVALUATOR DIFF", mid, mq, old[:8], new[:8])
        if mq == 8: feat_sel[mid] = new
print(f"evaluator path: {mols.height} molecules x (8,16) checked")

# ---- (2) builder path: legacy polars round-robin vs shared function (row sets per molecule)
sel0 = meta.join(mols.select("molecule", "lib"), left_on="inchikey14", right_on="molecule", how="inner").filter((pl.col("ingest_lib") == pl.col("lib")) & pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
for mq in (8, 16):
    sel = sel0.with_columns(pl.col("ce_mean").fill_null(0.0), (pl.col("adduct") != "[M+H]+").cast(pl.Int8).alias("not_mh"))
    sel = sel.sort(["inchikey14", "not_mh", "adduct", "ce_mean", "row"], maintain_order=True).with_columns(pl.col("row").cum_count().over(["inchikey14", "adduct"]).alias("k_in_adduct"))
    sel = sel.sort(["inchikey14", "k_in_adduct", "not_mh", "adduct", "row"], maintain_order=True).with_columns(pl.col("row").cum_count().over("inchikey14").alias("k")).filter(pl.col("k") <= mq)
    legacy_rows = {}
    for r_, k_ in zip(sel["row"].to_list(), sel["inchikey14"].to_list()): legacy_rows.setdefault(k_, set()).add(int(r_))
    add_of = dict(zip(sel0["row"].to_list(), sel0["adduct"].to_list())); ce_of = dict(zip(sel0["row"].to_list(), sel0["ce_mean"].to_list()))
    rows_by_mol = {}
    for r_, k_ in zip(sel0["row"].to_list(), sel0["inchikey14"].to_list()): rows_by_mol.setdefault(k_, []).append(int(r_))
    new_rows = {k_: set(select_queries(sorted(rs), mq, add_of.__getitem__, ce_of.__getitem__)) for k_, rs in rows_by_mol.items()}
    bad = [k for k in set(legacy_rows) | set(new_rows) if legacy_rows.get(k, set()) != new_rows.get(k, set())]
    fails += len(bad); print(f"builder path max_spectra={mq}: {len(new_rows)} molecules, {len(bad)} differ", bad[:5])
    if mq == 8:
        bad2 = [k for k in feat_sel if set(feat_sel[k]) != new_rows.get(k, set())]
        fails += len(bad2); print(f"builder(8) vs evaluator(8) row sets: {len(bad2)} differ", bad2[:5])

# ---- (3) pipeline path on the W7 test file: legacy sort/loop vs shared function, and pipeline(8) == evaluator(8) store rows
if a.test:
    t = pl.read_parquet(a.test).select("molecule_id", "adduct", "collision_energy_ev", "spectrum_row")
    per = {}
    for r in t.iter_rows(named=True):
        ce = r["collision_energy_ev"]; ce = [float(x) for x in ce] if ce is not None and len(ce) else None
        per.setdefault(str(r["molecule_id"]), []).append(dict(adduct=r["adduct"], ce=float(np.mean(ce)) if ce else None, row=int(r["spectrum_row"])))
    MAX_Q = 8; n_bad_order = n_bad_cross = 0
    for mid, spectra in per.items():
        known = [s for s in spectra if s["adduct"] in ADDUCT_SHIFT]
        by_add = {}
        for s in sorted(known, key=lambda s: (s["adduct"] != "[M+H]+", s["adduct"], s["ce"] if s["ce"] is not None else 0.0)):
            by_add.setdefault(s["adduct"], []).append(s)
        old = []
        while len(old) < MAX_Q and any(by_add.values()):
            for ad in list(by_add):
                if by_add[ad] and len(old) < MAX_Q: old.append(by_add[ad].pop(0))
        new = select_queries(known, MAX_Q, lambda s: s["adduct"], lambda s: s["ce"])
        if [s["row"] for s in old] != [s["row"] for s in new]: n_bad_order += 1; print("PIPELINE DIFF", mid)
        if mid in feat_sel and [s["row"] for s in new] != list(feat_sel[mid]): n_bad_cross += 1; print("PIPELINE vs EVALUATOR", mid, [s["row"] for s in new][:8], list(feat_sel[mid])[:8])
    fails += n_bad_order + n_bad_cross
    print(f"pipeline path: {len(per)} molecules; legacy-vs-shared differ {n_bad_order}; pipeline(8) vs evaluator(8) ordered rows differ {n_bad_cross} (molecules in test but not in eval csv: {len(set(per) - set(feat_sel))})")
print("SELECT_QUERIES TEST", "PASS" if fails == 0 else f"FAIL ({fails})")
sys.exit(0 if fails == 0 else 1)
