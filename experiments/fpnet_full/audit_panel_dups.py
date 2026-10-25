"""019b audit for the full_eval FPNet training data: for every panel query acquisition (enveda-np-examples row), the most similar spectrum that
REMAINS in the training data within the molecule's whole identity group (all keys of the group, not only the raw panel key), same polarity.
Rows removed by prep_full_eval.py (all panel rows + same-key duplicates: same adduct, |dprec| < 5 mDa, entropy similarity >= 0.95) are
recomputed here with the same rule and excluded. Output: one row per panel query (nearest remaining row, its key / library / adduct,
precursor difference, similarity) + a summary of how many queries still have a near copy in training under looser criteria.
Usage: python -X utf8 audit_panel_dups.py --train data/raw/train.parquet --folds data/external/identity_folds/structures.parquet --out DIR
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline"))
from b1_common import clean_peaks, entropy_similarity
ap = argparse.ArgumentParser(); ap.add_argument("--train", required=True); ap.add_argument("--folds", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--panel_lib", default="enveda-np-examples"); ap.add_argument("--dup_sim", type=float, default=0.95); a = ap.parse_args(); t0 = time.time()
os.makedirs(a.out, exist_ok=True)
meta = pq.read_table(a.train, columns=["inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "instrument_type"]).to_pandas(); meta["row"] = np.arange(len(meta))
st = pd.read_parquet(a.folds, columns=["inchikey14", "identity_group"]).drop_duplicates("inchikey14")
meta = meta.merge(st, on="inchikey14", how="left")
panel_rows = meta[meta.ingest_lib == a.panel_lib]; panel_keys = set(panel_rows.inchikey14)
groups = set(panel_rows.identity_group.dropna().astype(int))
grp_rows = meta[meta.identity_group.isin(groups)]
print(f"panel keys {len(panel_keys)}; identity groups {len(groups)}; keys in those groups {grp_rows.inchikey14.nunique()}; rows {len(grp_rows):,} ({time.time()-t0:.0f}s)", flush=True)
need = sorted(grp_rows.row.tolist())
pk = pq.read_table(a.train, columns=["ms2_mzs", "ms2_normalized_intensities"]).take(pa.array(need)).to_pydict()
clean = {}
for r, m, i in zip(need, pk["ms2_mzs"], pk["ms2_normalized_intensities"]):
    pr = float(meta.precursor_mz.iat[r]); clean[r] = clean_peaks(np.asarray(m, float), np.asarray(i, float), pr)
# rows removed by prep_full_eval.py (same rule: same raw key, same adduct, |dprec| < 5 mDa, sim >= dup_sim)
removed = set(panel_rows.row)
for ik, g in grp_rows[grp_rows.inchikey14.isin(panel_keys)].groupby("inchikey14"):
    q = g[g.ingest_lib == a.panel_lib]; o = g[g.ingest_lib != a.panel_lib]
    for r in o.itertuples():
        for qq in q.itertuples():
            if qq.adduct != r.adduct or abs(qq.precursor_mz - r.precursor_mz) >= 0.005: continue
            qm, qi = clean[qq.row]; om, oi = clean[r.row]
            if len(qm) and len(om) and entropy_similarity(qm, qi, om, oi) >= a.dup_sim: removed.add(int(r.row)); break
remain = grp_rows[~grp_rows.row.isin(removed)]
print(f"rows removed (recomputed) {len(removed)}; remaining rows in panel identity groups {len(remain):,} ({time.time()-t0:.0f}s)", flush=True)
out = []
for qq in panel_rows.itertuples():
    cand = remain[(remain.identity_group == qq.identity_group) & (remain.ionization_mode == qq.ionization_mode)]
    qm, qi = clean[qq.row]; best = (-1.0, None)
    for r in cand.itertuples():
        om, oi = clean[r.row]
        if not len(qm) or not len(om): continue
        sim = entropy_similarity(qm, qi, om, oi)
        if sim > best[0]: best = (sim, r)
    sim, r = best
    out.append(dict(query_row=int(qq.row), query_key=qq.inchikey14, identity_group=int(qq.identity_group) if qq.identity_group == qq.identity_group else -1, query_adduct=qq.adduct,
                    n_remaining_same_polarity=len(cand), nearest_sim=float(sim) if r is not None else np.nan,
                    nearest_row=int(r.row) if r is not None else -1, nearest_key=r.inchikey14 if r is not None else None, nearest_same_key=bool(r is not None and r.inchikey14 == qq.inchikey14),
                    nearest_lib=r.ingest_lib if r is not None else None, nearest_adduct=r.adduct if r is not None else None, nearest_instrument=r.instrument_type if r is not None else None,
                    nearest_dprec=float(abs(r.precursor_mz - qq.precursor_mz)) if r is not None else np.nan))
o = pd.DataFrame(out); o.to_csv(os.path.join(a.out, "panel_query_nearest_remaining.csv"), index=False)
summ = dict(panel_queries=len(o), panel_molecules=int(o.query_key.nunique()), identity_groups=len(groups), group_keys=int(grp_rows.inchikey14.nunique()),
            extra_keys_beyond_panel=int(grp_rows.inchikey14.nunique() - len(panel_keys)), rows_removed=len(removed), remaining_rows=len(remain),
            queries_with_no_remaining_same_polarity=int((o.n_remaining_same_polarity == 0).sum()))
for thr in (0.99, 0.95, 0.90, 0.80):
    hit = o[(o.nearest_sim >= thr)]
    summ[f"queries_nearest_sim_ge_{thr}"] = len(hit); summ[f"molecules_with_query_nearest_sim_ge_{thr}"] = int(hit.query_key.nunique())
    summ[f"queries_nearest_sim_ge_{thr}_and_dprec_lt_5mDa_same_adduct"] = int(((o.nearest_sim >= thr) & (o.nearest_dprec < 0.005) & (o.nearest_adduct == o.query_adduct)).sum())
summ["queries_nearest_from_other_key_in_group"] = int((~o.nearest_same_key & o.nearest_row.ge(0)).sum())
json.dump(summ, open(os.path.join(a.out, "panel_dup_audit_summary.json"), "w"), indent=1)
print(json.dumps(summ, indent=1), f"({time.time()-t0:.0f}s)")
