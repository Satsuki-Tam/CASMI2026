"""052 diagnostic sets: timsTOF-vs-other-instrument domain gap of the spectrum->fingerprint model on the SAME natural products.
Panel molecules (enveda-np-examples, timsTOF) split by identity fold k; for each fold the fold-k FPNet never saw these identities.
Versions: T = timsTOF queries (enveda-np-examples), riken / gnps = the same molecules queried with that library's spectra.
Writes panel_dg/p1_f<k>.csv (sets DG_T, DG_riken, DG_gnps; only molecules with test-adduct spectra in the version's library).
"""
import os, sys
import pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
P = pd.read_csv(os.path.join(HERE, "panel_np250/p1_molecules.csv"))
F = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet"), columns=["inchikey14", "fold_identity"]).to_pandas().drop_duplicates("inchikey14")
P = P.merge(F, left_on="molecule", right_on="inchikey14", how="left").drop(columns=["inchikey14"])
sys.path.insert(0, HERE); from b1_common import ADDUCT_SHIFT
M = pl.read_parquet(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet"), columns=["inchikey14", "ingest_lib", "adduct"]).to_pandas()
M = M[M.inchikey14.isin(set(P.molecule)) & M.adduct.isin(set(ADDUCT_SHIFT))]
have = M.groupby("ingest_lib").inchikey14.agg(set).to_dict()
os.makedirs(os.path.join(HERE, "panel_dg"), exist_ok=True)
for k in range(5):
    Pk = P[P.fold_identity == k]; parts = []
    for v, lib in (("T", "enveda-np-examples"), ("riken", "riken"), ("gnps", "gnps")):
        x = Pk[Pk.molecule.isin(have.get(lib, set()))].copy(); x["set"] = f"DG_{v}"; x["group"] = "diag"; x["lib"] = lib; parts.append(x)
    out = pd.concat(parts, ignore_index=True).drop(columns=["fold_identity"])
    out.to_csv(os.path.join(HERE, f"panel_dg/p1_f{k}.csv"), index=False)
    print(k, out.groupby("set").size().to_dict())
