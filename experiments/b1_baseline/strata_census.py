"""Codex 015 (b): census of candidate evaluation strata over the spectra store, EXCLUDING MassSpecGym molecules (forward-model training) and all
identities already used for development (dev/locked/eval_c1 sets, panel, E2b lists). Per molecule (raw inchikey14, test adducts only):
reference count across libraries, number of libraries, timsTOF presence, forward coverage ([M+H]+/[M+Na]+ present), NH4-only, negative-only,
PubChem literature count (pubchem_popularity). Prints stratum sizes so a stratified p2 / locked-2 selection can be designed.
Usage: python -X utf8 strata_census.py --store data/processed/spectra_store --msg_dir data/external/massspecgym --pop_dir data/external/pubchem_popularity --exclude CSV... --out census.parquet
"""
import argparse, glob, os
import numpy as np, polars as pl
from b1_common import ADDUCT_SHIFT
ap = argparse.ArgumentParser(); ap.add_argument("--store", required=True); ap.add_argument("--msg_dir", required=True); ap.add_argument("--pop_dir", default="")
ap.add_argument("--exclude", nargs="*", default=[]); ap.add_argument("--panel_lib", default="enveda-np-examples"); ap.add_argument("--out", default="")
a = ap.parse_args()
m = pl.read_parquet(f"{a.store}/spec_meta.parquet").filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
msg_raw = set(open(f"{a.msg_dir}/msg_raw_keys.txt").read().split()); msg_sc = set(open(f"{a.msg_dir}/msg_scorer_keys.txt").read().split())
used = set()
for f in a.exclude:
    try:
        d = pl.read_csv(f, infer_schema_length=10000)
        for c in ("molecule", "scorer_key", "raw_key", "inchikey14"):
            if c in d.columns: used |= set(str(x) for x in d[c].drop_nulls().to_list())
    except Exception as e: print("exclude file skipped", f, e)
panel = set(m.filter(pl.col("ingest_lib") == a.panel_lib)["inchikey14"].to_list()); used |= panel
print(f"spectra (test adducts) {m.height:,}; molecules {m['inchikey14'].n_unique():,}; MSG raw {len(msg_raw):,} / scorer {len(msg_sc):,}; development identities {len(used):,} (panel {len(panel)})")
g = m.group_by("inchikey14").agg(pl.len().alias("n_ref"), pl.col("ingest_lib").n_unique().alias("n_libs"), pl.col("ingest_lib").unique().sort().alias("libs"),
                                 pl.col("instrument_type").fill_null("").str.to_lowercase().str.contains("tims").any().alias("has_timstof"),
                                 (pl.col("instrument_type").fill_null("").str.to_lowercase().str.contains("tims")).sum().alias("n_timstof"),
                                 pl.col("adduct").is_in(["[M+H]+", "[M+Na]+"]).any().alias("has_covered_pos"),
                                 (pl.col("adduct") == "[M+NH4]+").all().alias("nh4_only"), (pl.col("ionization_mode") == "negative").all().alias("neg_only"),
                                 (pl.col("ionization_mode") == "positive").any().alias("has_pos"), pl.col("scorer_ik14").first().alias("scorer_ik14"),
                                 pl.col("adduct").n_unique().alias("n_adducts"))
g = g.with_columns(pl.col("inchikey14").is_in(list(msg_raw)).alias("in_msg_raw"), pl.col("scorer_ik14").is_in(list(msg_sc)).alias("in_msg_scorer"),
                   (pl.col("inchikey14").is_in(list(used)) | pl.col("scorer_ik14").is_in(list(used))).alias("in_dev"),
                   pl.col("libs").list.contains("enveda-180").alias("in_enveda180"), pl.col("libs").list.eval(pl.element().is_in(["gnps", "riken", "mona", "massbank", "msdial"])).list.any().alias("in_nplib"))
pop = None
if a.pop_dir:
    for p in sorted(glob.glob(f"{a.pop_dir}/*.parquet")):
        try:
            d = pl.read_parquet(p); print("popularity file", p, d.height, d.columns[:10])
            key = next((c for c in ("inchikey14", "ik14", "scorer_ik14", "inchikey") if c in d.columns), None)
            cols = [c for c in d.columns if any(k in c.lower() for k in ("pubmed", "patent", "substance", "pop", "synonym", "literature"))]
            if key and cols: pop = d.select([key] + cols).unique(key).rename({key: "pop_key"}); print("  using", key, cols); break
        except Exception as e: print("popularity file skipped", p, e)
if pop is not None:
    g = g.join(pop, left_on="inchikey14", right_on="pop_key", how="left")
free = g.filter(~pl.col("in_msg_raw") & ~pl.col("in_msg_scorer") & ~pl.col("in_dev"))
print(f"molecules: all {g.height:,}; free of MSG + development {free.height:,}")
def cnt(df, name, expr):
    n_all = df.filter(expr).height; n_ts = df.filter(expr & pl.col("has_timstof")).height; n_np = df.filter(expr & pl.col("in_nplib")).height; n_e = df.filter(expr & pl.col("in_enveda180")).height
    print(f"  {name:<44s} free {n_all:>7,} | with timsTOF {n_ts:>6,} | NP libs {n_np:>6,} | enveda-180 {n_e:>6,}")
print("strata (free molecules):")
cnt(free, "refs 1-2", pl.col("n_ref") <= 2); cnt(free, "refs 3-9", (pl.col("n_ref") >= 3) & (pl.col("n_ref") <= 9)); cnt(free, "refs 10-19", (pl.col("n_ref") >= 10) & (pl.col("n_ref") <= 19)); cnt(free, "refs >=20", pl.col("n_ref") >= 20)
cnt(free, "refs >=20 AND >=2 libraries (panel-like)", (pl.col("n_ref") >= 20) & (pl.col("n_libs") >= 2)); cnt(free, ">=2 libraries (class-1 cross-lib possible)", pl.col("n_libs") >= 2)
cnt(free, "single library, 1 spectrum", (pl.col("n_libs") == 1) & (pl.col("n_ref") == 1))
cnt(free, "negative-only", pl.col("neg_only")); cnt(free, "NH4-only", pl.col("nh4_only")); cnt(free, "no covered positive ([M+H]+/[M+Na]+)", ~pl.col("has_covered_pos"))
cnt(free, "no covered positive AND has positive", ~pl.col("has_covered_pos") & pl.col("has_pos")); cnt(free, ">=3 adducts", pl.col("n_adducts") >= 3)
if pop is not None:
    pc = [c for c in g.columns if any(k in c.lower() for k in ("pubmed", "patent", "substance", "synonym", "literature"))]
    for c in pc[:3]:
        q = free[c].drop_nulls(); 
        if q.len(): print(f"  popularity {c}: n {q.len():,}, quantiles 10/50/90 = {q.quantile(0.1):.3g}/{q.quantile(0.5):.3g}/{q.quantile(0.9):.3g}; null {free[c].null_count():,}")
print("library membership of free molecules:", free.explode("libs").group_by("libs").agg(pl.len()).sort("len", descending=True).to_dict(as_series=False))
if a.out: g.drop("libs").with_columns(pl.Series("libs", ["|".join(x) for x in g["libs"].to_list()])).write_parquet(a.out); print("wrote", a.out)
