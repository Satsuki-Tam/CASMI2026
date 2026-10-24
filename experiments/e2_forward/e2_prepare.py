"""E2 prep: for each natural-product panel molecule, take its same-formula PubChem candidates ranked by the
fold-safe fingerprint model (fold0_full, never saw the panel), keep the top N_MAX, attach SMILES from the PubChem tier
and the molecule's covered timsTOF spectra ([M+H]+/[M+Na]+ positive) from train (enveda-np-examples), and write the
ICEBERG/GLACIER runner input. Also records the truth's rank under fold0 and fold0+doc for later evaluation.
Usage: python -I -X utf8 e2_prepare.py <panel_dir> <pubchem_tier_dir> <raw_dir> <processed_dir> <out_dir> [N_MAX]
"""
import json, sys, time
import numpy as np, pandas as pd, polars as pl

D, T, RAW, PROC, OUT = sys.argv[1:6]
N_MAX = int(sys.argv[6]) if len(sys.argv) > 6 else 200
t0 = time.time()

pc = pd.read_parquet(f"{D}/pubchem_candidates.parquet", columns=["molecule", "tier_row", "connectivity", "scorer_key", "is_truth", "in_pool", "log_substances", "log_pubmed"])
fs = pd.read_parquet(f"{D}/panel_fpnet_scores.parquet", columns=["molecule", "tier_row", "ab_full", "fold0_full"])
sf = pd.read_parquet(f"{D}/panel_same_formula.parquet")
pc["molecule"] = pc["molecule"].astype(str); fs["molecule"] = fs["molecule"].astype(str)
df = pc.merge(fs, on=["molecule", "tier_row"]).merge(sf, on=["molecule", "tier_row"])
df = df[(df.same_formula == True) & np.isfinite(df.fold0_full)].copy()
df["ident"] = np.where(df.scorer_key.fillna("") != "", df.scorer_key, df.connectivity)
df["doc"] = df.log_substances.fillna(0).astype(float) + df.log_pubmed.fillna(0).astype(float)
# one row per identity: keep the best fold0 score
df = df.sort_values(["molecule", "fold0_full"], ascending=[True, False]).drop_duplicates(["molecule", "ident"])
df["rank_fold0"] = df.groupby("molecule").cumcount() + 1
z = df.groupby("molecule").fold0_full.transform(lambda x: (x - x.mean()) / (x.std() + 1e-9))
df["fold0_doc"] = z + 0.25 * df.doc
df["rank_fold0_doc"] = df.groupby("molecule").fold0_doc.rank(ascending=False, method="first").astype(int)
print(f"same-formula identities: {len(df):,} over {df.molecule.nunique()} molecules; median per molecule {df.groupby('molecule').size().median():.0f}")
tr = df[df.is_truth].groupby("molecule").agg(rank_fold0=("rank_fold0", "min"), rank_fold0_doc=("rank_fold0_doc", "min"), n_ident=("ident", "size"))
n_id = df.groupby("molecule").size().rename("n_identities")
summary = n_id.to_frame().join(tr[["rank_fold0", "rank_fold0_doc"]])
for col in ("rank_fold0", "rank_fold0_doc"):
    r = summary[col]
    print(f"truth {col}: present {r.notna().sum()}/250 | rank1 {(r==1).sum()} | <=25 {(r<=25).sum()} | <=40 {(r<=40).sum()} | <=100 {(r<=100).sum()} | <=200 {(r<=200).sum()} | median {r.median()}")
summary.to_csv(f"{OUT}/truth_ranks.csv")

# SMILES from the PubChem tier
off = np.load(f"{T}/pc_off.npy", mmap_mode="r"); buf = np.load(f"{T}/pc_smiles.npy", mmap_mode="r")
def smiles_of(i):
    i = int(i); return bytes(buf[off[i]:off[i + 1]]).decode("ascii")
top = df[df.rank_fold0 <= N_MAX].copy()
top["smiles"] = [smiles_of(i) for i in top.tier_row.values]
print(f"top-{N_MAX} candidates: {len(top):,} rows; truths inside: {int(top.is_truth.sum())}; sample smiles: {top.smiles.iloc[0]}")
top.to_parquet(f"{OUT}/candidates_top{N_MAX}.parquet", index=False)

# spectra: enveda-np-examples rows, molecule = scorer key
keys = pl.read_parquet(f"{PROC}/train_scorer_keys.parquet").select("normalized_smiles", "scorer_ik14")
sp = (pl.scan_parquet(f"{RAW}/train.parquet").filter(pl.col("ingest_lib") == "enveda-np-examples")
      .select("normalized_smiles", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type",
              "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units").collect()
      .join(keys, on="normalized_smiles", how="left"))
panel = set(df.molecule.unique())
sp = sp.filter(pl.col("scorer_ik14").is_in(list(panel)))
print(f"np-examples spectra for panel molecules: {sp.height} over {sp['scorer_ik14'].n_unique()} molecules")
cov = sp.filter((pl.col("ionization_mode") == "positive") & pl.col("adduct").is_in(["[M+H]+", "[M+Na]+"]))
print(f"covered spectra ([M+H]+/[M+Na]+ positive): {cov.height} over {cov['scorer_ik14'].n_unique()} molecules")
items = []
for mid, g in cov.group_by("scorer_ik14"):
    mid = mid[0] if isinstance(mid, tuple) else mid
    cands = top[top.molecule == mid].sort_values("rank_fold0").smiles.tolist()
    if not cands: continue
    spectra = []
    for r in g.iter_rows(named=True):
        spectra.append(dict(mz=[float(x) for x in r["ms2_mzs"]], it=[float(x) for x in r["ms2_normalized_intensities"]], prec=float(r["precursor_mz"]),
                            adduct=r["adduct"], mode=r["ionization_mode"], instrument=r["instrument_type"],
                            ce_ev=[float(x) for x in r["collision_energy_ev"]] if r["collision_energy_ev"] is not None else None,
                            ce_orig=r["collision_energy_orig"], ce_units=r["collision_energy_orig_units"]))
    items.append(dict(mid=mid, spectra=spectra, cands=cands))
items.sort(key=lambda it: it["mid"])
json.dump(items, open(f"{OUT}/ice_in_top{N_MAX}.json", "w"))
n_pred = sum(len(it["cands"]) * len({(s["adduct"], tuple(s["ce_ev"] or [])) for s in it["spectra"]}) for it in items)
print(f"runner items: {len(items)} molecules, {sum(len(it['cands']) for it in items):,} candidate rows, ~{n_pred:,} (candidate x condition) predictions upper bound; {time.time()-t0:.0f}s")
