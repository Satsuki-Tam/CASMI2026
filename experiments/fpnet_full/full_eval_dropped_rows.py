"""Recompute and save the exact train.parquet rows removed by prep_full_eval.py (same rule: every enveda-np-examples row, plus other-library
rows of the same raw key with the same adduct, |dprec| < 5 mDa and entropy similarity >= 0.95 to one of them), so the full_eval training
input can be reproduced from train.parquet. Asserts the count recorded in check_inputs.json.
Usage: python -X utf8 full_eval_dropped_rows.py --train data/raw/train.parquet --run experiments/fpnet_full/full_eval
"""
import argparse, json, os, sys
import numpy as np, pyarrow as pa, pyarrow.parquet as pq
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline"))
from b1_common import clean_peaks, entropy_similarity
ap = argparse.ArgumentParser(); ap.add_argument("--train", required=True); ap.add_argument("--run", required=True); ap.add_argument("--panel_lib", default="enveda-np-examples"); a = ap.parse_args()
meta = pq.read_table(a.train, columns=["inchikey14", "ingest_lib", "adduct", "precursor_mz"]).to_pandas(); meta["row"] = np.arange(len(meta))
panel_keys = set(meta.loc[meta.ingest_lib == a.panel_lib, "inchikey14"]); drop = set(meta.loc[meta.ingest_lib == a.panel_lib, "row"].tolist())
cand = meta[meta.inchikey14.isin(panel_keys)]; need = sorted(cand.row.tolist())
pk = pq.read_table(a.train, columns=["ms2_mzs", "ms2_normalized_intensities"]).take(pa.array(need)).to_pydict()
spec = {r: (np.asarray(m, float), np.asarray(i, float)) for r, m, i in zip(need, pk["ms2_mzs"], pk["ms2_normalized_intensities"])}
for ik, g in cand.groupby("inchikey14"):
    q = g[g.ingest_lib == a.panel_lib]; o = g[g.ingest_lib != a.panel_lib]
    qc = [(r.adduct, r.precursor_mz, clean_peaks(*spec[r.row], r.precursor_mz)) for r in q.itertuples()]
    for r in o.itertuples():
        oc = None
        for ad, pr, (qm, qi) in qc:
            if ad != r.adduct or abs(pr - r.precursor_mz) >= 0.005: continue
            if oc is None: oc = clean_peaks(*spec[r.row], r.precursor_mz)
            if len(qm) and len(oc[0]) and entropy_similarity(qm, qi, oc[0], oc[1]) >= 0.95: drop.add(int(r.row)); break
gate = json.load(open(os.path.join(a.run, "check_inputs.json")))
assert len(drop) == gate["rows_dropped"], (len(drop), gate["rows_dropped"])
json.dump(sorted(int(x) for x in drop), open(os.path.join(a.run, "dropped_train_rows.json"), "w"))
print("dropped rows", len(drop), "-> dropped_train_rows.json (matches check_inputs.json)")
