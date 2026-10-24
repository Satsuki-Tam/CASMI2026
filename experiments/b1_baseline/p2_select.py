"""Codex 015/016 (b): stratified evaluation molecules (p2) from the strata census. Exclusive strata, one molecule per identity group, identity
groups disjoint from every development set (CSV list) and between the two roles (dev2 = first n per stratum, locked2 = next n), fold_identity 0.
Strata: C_np_crosslib (NP lib, >=20 refs, >=2 libs), D_np_single (NP, single lib, <=2 refs), E_np_negonly (NP, negative-only),
F_np_uncovered (NP, positive present but no [M+H]+/[M+Na]+), G_tims_crosslib (enveda-180 query, >=2 libs). Query library = the library of the
stratum family with the most test-adduct spectra for the molecule. Output schema = p1_molecules.csv subset (set, group, molecule, scorer_key,
raw_key, lib, identity_group, ...), group = eval.
Usage: python -X utf8 p2_select.py --census eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds
                                   --exclude CSV... --n 100 --seed 5 --out_dev eval_set2/p2_dev_molecules.csv --out_locked locked_eval2/p2_locked_molecules.csv
"""
import argparse, json, os, time
import numpy as np, polars as pl
from b1_common import ADDUCT_SHIFT
NP_LIBS = ["gnps", "riken", "mona", "massbank", "msdial"]
ap = argparse.ArgumentParser(); ap.add_argument("--census", required=True); ap.add_argument("--store", required=True); ap.add_argument("--folds", required=True)
ap.add_argument("--exclude", nargs="*", default=[]); ap.add_argument("--n", type=int, default=100); ap.add_argument("--seed", type=int, default=5)
ap.add_argument("--out_dev", required=True); ap.add_argument("--out_locked", required=True); ap.add_argument("--panel_lib", default="enveda-np-examples")
a = ap.parse_args(); t0 = time.time()
c = pl.read_parquet(a.census)
folds = pl.read_parquet(f"{a.folds}/structures.parquet").select("inchikey14", "scorer_key", "identity_group", "fold_identity").unique("inchikey14")
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet").filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
# development identities -> identity groups (exclude whole groups)
used = set()
for f in a.exclude:
    d = pl.read_csv(f, infer_schema_length=10000)
    for col in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if col in d.columns: used |= set(str(x) for x in d[col].drop_nulls().to_list())
used |= set(meta.filter(pl.col("ingest_lib") == a.panel_lib)["inchikey14"].to_list())
used_groups = set(folds.filter(pl.col("inchikey14").is_in(list(used)) | pl.col("scorer_key").is_in(list(used)))["identity_group"].to_list())
c = c.join(folds, on="inchikey14", how="left")
elig = c.filter(~pl.col("in_msg_raw") & ~pl.col("in_msg_scorer") & ~pl.col("in_dev") & pl.col("identity_group").is_not_null() & ~pl.col("identity_group").is_in(list(used_groups)) & (pl.col("fold_identity") == 0))
print(f"census {c.height:,}; development identities {len(used):,} -> groups {len(used_groups):,}; eligible (not MSG/dev, fold 0) {elig.height:,} ({time.time()-t0:.0f}s)")
# per-molecule spectra count per library (query library choice)
per_lib = meta.group_by("inchikey14", "ingest_lib").agg(pl.len().alias("n")).sort("n", descending=True)
best_lib = {}
for ik, lib, n in per_lib.iter_rows():
    best_lib.setdefault(ik, []).append((lib, n))
def query_lib(ik, family):
    for lib, n in best_lib.get(ik, []):
        if (family == "np" and lib in NP_LIBS) or (family == "tims" and lib == "enveda-180"): return lib
    return None
S = [("E_np_negonly", pl.col("in_nplib") & pl.col("neg_only"), "np"),
     ("F_np_uncovered", pl.col("in_nplib") & pl.col("has_pos") & ~pl.col("has_covered_pos"), "np"),
     ("C_np_crosslib", pl.col("in_nplib") & (pl.col("n_ref") >= 20) & (pl.col("n_libs") >= 2), "np"),
     ("G_tims_crosslib", pl.col("in_enveda180") & (pl.col("n_libs") >= 2), "tims"),
     ("D_np_single", pl.col("in_nplib") & (pl.col("n_libs") == 1) & (pl.col("n_ref") <= 2), "np")]
rng = np.random.default_rng(a.seed); taken_groups = set(); out = []
for name, expr, fam in S:
    d = elig.filter(expr & ~pl.col("identity_group").is_in(list(taken_groups))).sort("inchikey14")
    idx = rng.permutation(d.height); d = d[idx.tolist()].unique("identity_group", keep="first", maintain_order=True)
    rows = []
    for r in d.iter_rows(named=True):
        lib = query_lib(r["inchikey14"], fam)
        if lib is None: continue
        rows.append(dict(set=name, group="eval", molecule=r["inchikey14"], scorer_key=r["scorer_key"] or r["scorer_ik14"], raw_key=r["inchikey14"], lib=lib, identity_group=int(r["identity_group"]),
                         n_ref=int(r["n_ref"]), n_libs=int(r["n_libs"]), libs=r["libs"], has_timstof=bool(r["has_timstof"]), neg_only=bool(r["neg_only"]), nh4_only=bool(r["nh4_only"]),
                         has_covered_pos=bool(r["has_covered_pos"]), n_adducts=int(r["n_adducts"])))
        if len(rows) >= 2 * a.n: break
    for i, r in enumerate(rows): r["role"] = "dev2" if i < a.n else "locked2"; taken_groups.add(r["identity_group"]); out.append(r)
    print(f"{name:<16s} eligible groups {d.height:>6,} -> dev2 {min(a.n, len(rows)):>3} / locked2 {max(0, len(rows) - a.n):>3}; query libs {pl.DataFrame(rows)['lib'].value_counts().sort('count', descending=True).to_dict(as_series=False) if rows else {}}")
df = pl.DataFrame(out)
for role, path in (("dev2", a.out_dev), ("locked2", a.out_locked)):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True); d = df.filter(pl.col("role") == role).drop("role"); d.write_csv(path); print(role, d.height, "->", path)
json.dump(dict(seed=a.seed, n_per_stratum=a.n, strata=[s[0] for s in S], exclude=a.exclude, census=a.census, eligible=elig.height, used_identities=len(used), used_groups=len(used_groups), fold_identity=0),
          open(os.path.join(os.path.dirname(a.out_dev) or ".", "p2_select_manifest.json"), "w"), indent=1)
