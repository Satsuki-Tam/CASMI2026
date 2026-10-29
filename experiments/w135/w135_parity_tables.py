"""W135 parity (135_decision.md §3 (c)): b1_world.py --parity_c2 must reproduce b1_features.py on an existing run (same molecules).
Compares, per (molecule, official_key), every column present in both tables (exact for flags / keys / counts / smiles, |diff| <= 1e-6 for
floats, NaN == NaN), and the per-molecule key sets. Prints PARITY_TABLES PASS / FAIL with the first mismatches.
Usage: python -X utf8 w135_parity_tables.py --ref RUN/b1_features_SET.parquet --new OUT/b1_features_SET.parquet"""
import argparse, sys
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--ref", required=True); ap.add_argument("--new", required=True); a = ap.parse_args()
N = pd.read_parquet(a.new); R = pd.read_parquet(a.ref)
for d in (N, R): d["molecule"] = d.molecule.astype(str); d["official_key"] = d.official_key.astype(str)
R = R[R.molecule.isin(set(N.molecule))]
bad = []
for m in sorted(set(N.molecule)):
    kn, kr = set(N[N.molecule == m].official_key), set(R[R.molecule == m].official_key)
    if kn != kr: bad.append(f"{m}: key sets differ (new-only {len(kn - kr)}, ref-only {len(kr - kn)})")
J = N.merge(R, on=["molecule", "official_key"], suffixes=("_n", "_r"))
cols = [c for c in N.columns if c in R.columns and c not in ("molecule", "official_key", "set")]
for c in cols:
    x, y = J[c + "_n"], J[c + "_r"]
    if pd.api.types.is_float_dtype(x) or pd.api.types.is_float_dtype(y):
        xv, yv = x.astype(float).values, y.astype(float).values; ok = (np.isnan(xv) & np.isnan(yv)) | (np.abs(xv - yv) <= 1e-6)
    else: ok = (x.astype(str).values == y.astype(str).values)
    if not ok.all(): bad.append(f"column {c}: {int((~ok).sum())} rows differ, e.g. {J.loc[~ok, ['molecule', 'official_key', c + '_n', c + '_r']].head(3).values.tolist()}")
print(f"molecules {N.molecule.nunique()}, rows new {len(N)} / ref {len(R)}, merged {len(J)}, columns compared {len(cols)}")
print("PARITY_TABLES " + ("PASS" if not bad else "FAIL")); [print(" ", b) for b in bad[:20]]
sys.exit(0 if not bad else 1)
