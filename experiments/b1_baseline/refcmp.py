"""Post-hoc reference comparability per (molecule, candidate, view) for an existing b1_features run (Codex 072 Q2/Q3; exploratory until registered).
b1_features counts every kept reference of a train-structure candidate (lib_nref) but computes similarities only against references of the SAME
POLARITY as a query; lib_sim = 0 can therefore mean 'not compared'. This adds, from the store metadata and the run's query adducts:
  n_cmp_pol : references (not query rows; view masks as b1_features: C1 = the truth's query-library references removed, C2 = all truth references)
              whose polarity matches a query polarity of the molecule
  n_cmp_add : the subset whose adduct equals a query adduct
Approximation: the exact-duplicate exclusion and the MAX_REF cap of b1_features are not replayed (they remove few references).
Usage: python -X utf8 refcmp.py --run run_np053_f1dev --eval_csv np053_f1dev/p2_molecules.csv --sets NP_H [--out diag/refcmp_<run>.parquet]"""
import argparse, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
from b1_common import ADDUCT_SHIFT
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--out", default="")
a = ap.parse_args()
meta = pl.read_parquet(f"{ROOT}/data/processed/spectra_store/spec_meta.parquet", columns=["row", "inchikey14", "scorer_ik14", "ingest_lib", "adduct", "ionization_mode"])
meta = meta.filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
pol = dict(zip(meta["row"].to_list(), meta["ionization_mode"].to_list())); add = dict(zip(meta["row"].to_list(), meta["adduct"].to_list())); lib_ = dict(zip(meta["row"].to_list(), meta["ingest_lib"].to_list()))
key_rows = {k: list(r) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
ik_rows = {k: list(r) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
ev = pd.read_csv(os.path.join(HERE, a.eval_csv)); ev["molecule"] = ev.molecule.astype(str); ev = ev.set_index("molecule")
out = []
for s in a.sets:
    F = pd.read_parquet(os.path.join(HERE, a.run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
    M = pd.read_csv(os.path.join(HERE, a.run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    for mid, g in F.groupby("molecule", sort=False):
        if mid not in M.index or mid not in ev.index: continue
        qlib = ev.loc[mid, "lib"]; qadds = set(str(M.loc[mid, "adducts"]).split("|")); qpols = {"positive" if x.endswith("+") else "negative" for x in qadds}
        qrows = {r for r in ik_rows.get(mid, []) if lib_[r] == qlib}
        for r in g.itertuples(index=False):
            if not (bool(r.in_train_c1) or bool(r.in_train_c2) or bool(r.is_truth)): continue
            rows_ = [x for x in key_rows.get(str(r.official_key), []) if x not in qrows]
            for view in ("c1", "c2"):
                if bool(r.is_truth): rr = [] if view == "c2" else [x for x in rows_ if lib_[x] != qlib]
                else: rr = rows_
                out.append(dict(set=s, molecule=mid, official_key=str(r.official_key), view=view, n_ref_all=len(rr),
                                n_cmp_pol=sum(pol[x] in qpols for x in rr), n_cmp_add=sum(add[x] in qadds for x in rr)))
D = pd.DataFrame(out); p = a.out or os.path.join(HERE, f"diag/refcmp_{os.path.basename(a.run)}.parquet"); D.to_parquet(p, index=False)
print(p, len(D), "rows | share n_ref_all>0 & n_cmp_pol==0:", round(float(((D.n_ref_all > 0) & (D.n_cmp_pol == 0)).mean()), 4))
