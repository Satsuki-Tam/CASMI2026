"""053: NP-truth evaluation molecules (the hidden test is Enveda natural products: panel truths 99.6% COCONUT). Fold-safe, MSG-free.
Eligible: raw keys of identity fold k (unseen by the public fpnet_fold<k>), not in MassSpecGym (raw or scorer key), identity group disjoint from
every exclusion file and from the panel, truth = a COCONUT structure (scorer key in the v2 pool with the COCONUT bit, or raw key in the COCONUT
store). Query library = any non-timsTOF library (enveda-180 and the panel library excluded); strata by the ACTUAL selected queries (shared
selector, max 8), exclusive with priority N, X, H:
  NP_N  all selected queries negative
  NP_X  a positive query but no [M+H]+ / [M+Na]+ (sub-label proxy_capable = only NH4 / water-loss positive adducts)
  NP_H  an [M+H]+ / [M+Na]+ query (forward models usable)
One molecule per identity group; per stratum one fixed-seed permutation: first n_dev = dev, next n_conf = conf (conf stays closed).
Usage: python -X utf8 p3_select_np.py --census eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds
         --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold 1 --n H:200,X:60,N:60 --seed 31 --exclude CSV... --out_dir DIR --conf_dir DIR
"""
import argparse, hashlib, json, os, pickle, sys, time
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import ADDUCT_SHIFT, select_queries
COVERED = {"[M+H]+", "[M+Na]+"}; PROXY_POS = {"[M+NH4]+", "[M-H2O+H]+", "[M-2H2O+H]+"}; NO_QUERY_LIBS = {"enveda-180", "enveda-np-examples"}
ap = argparse.ArgumentParser(); ap.add_argument("--census", required=True); ap.add_argument("--store", required=True); ap.add_argument("--folds", required=True)
ap.add_argument("--pool", required=True); ap.add_argument("--coco", required=True); ap.add_argument("--fold", type=int, required=True)
ap.add_argument("--n", default="H:200,X:60,N:60"); ap.add_argument("--seed", type=int, default=31); ap.add_argument("--exclude", nargs="*", default=[])
ap.add_argument("--out_dir", required=True); ap.add_argument("--conf_dir", required=True); ap.add_argument("--max_spectra", type=int, default=8); ap.add_argument("--panel_lib", default="enveda-np-examples")
a = ap.parse_args(); t0 = time.time(); rng = np.random.default_rng(a.seed); NN = {k: int(v) for k, v in (x.split(":") for x in a.n.split(","))}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
counts = {}
c = pl.read_parquet(a.census); counts["census_raw_keys"] = c.height
folds = pl.read_parquet(f"{a.folds}/structures.parquet").select("inchikey14", "scorer_key", "identity_group", "fold_identity").unique("inchikey14")
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet").filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
used = set(); excl_sha = {}
for f in a.exclude:
    d = pl.read_csv(f, infer_schema_length=10000); excl_sha[f] = sha(f); found = False
    for col in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if col in d.columns: used |= set(str(x) for x in d[col].drop_nulls().to_list()); found = True
    if not found: raise SystemExit(f"exclusion file without identity columns: {f}")
panel_keys = set(meta.filter(pl.col("ingest_lib") == a.panel_lib)["inchikey14"].to_list()); used |= panel_keys
used_groups = set(folds.filter(pl.col("inchikey14").is_in(list(used)) | pl.col("scorer_key").is_in(list(used)))["identity_group"].to_list())
pool = pl.read_parquet(a.pool, columns=["key", "src"]); POOL_COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
COCO_RAW = set(str(x) for x in pickle.load(open(f"{a.coco}/coco_meta.pkl", "rb"))["keys"])
c = c.join(folds, on="inchikey14", how="left")
s1 = c.filter(~pl.col("in_msg_raw") & ~pl.col("in_msg_scorer")); counts["not_msg"] = s1.height
s2 = s1.filter(~pl.col("in_dev") & ~pl.col("identity_group").is_in(list(used_groups)) & pl.col("identity_group").is_not_null()); counts["not_used"] = s2.height
s3 = s2.filter(pl.col("fold_identity") == a.fold); counts["fold"] = s3.height
elig = s3.filter(pl.col("scorer_key").is_in(list(POOL_COCO)) | pl.col("inchikey14").is_in(list(COCO_RAW))); counts["coconut_truth"] = elig.height
counts["coconut_truth_groups"] = elig["identity_group"].n_unique()
print(counts, flush=True)
m = meta.filter(pl.col("inchikey14").is_in(elig["inchikey14"].to_list())).with_columns(pl.col("ce_mean").fill_null(-1.0).round(1).alias("ce_r"), pl.col("precursor_mz").round(3).alias("prec_r"))
rows_of = {}
for ik, lib, add, mode, ce, pr, npk, row in m.select("inchikey14", "ingest_lib", "adduct", "ionization_mode", "ce_r", "prec_r", "n_peaks", "row").iter_rows():
    rows_of.setdefault(ik, []).append(dict(lib=lib, adduct=add, mode=mode, ce=ce, prec=pr, npk=npk, row=row))


def analyse(ik, L):
    rs = rows_of.get(ik, []); qrows = sorted((r for r in rs if r["lib"] == L), key=lambda r: r["row"])
    if not qrows: return None
    q = select_queries(qrows, a.max_spectra, lambda r: r["adduct"], lambda r: (None if r["ce"] < 0 else r["ce"]))
    modes = {r["mode"] for r in q}; adds = {r["adduct"] for r in q}; qkeys = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in q}
    pos_adds = {r["adduct"] for r in q if r["mode"] == "positive"}
    other = [r for r in rs if r["lib"] != L and r["mode"] in modes]
    dedup = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in other} - qkeys
    return dict(n_q=len(q), q_adducts="|".join(sorted(adds)), q_has_hna=bool(adds & COVERED), q_all_neg=all(r["mode"] == "negative" for r in q), q_has_pos=any(r["mode"] == "positive" for r in q),
                q_proxy_capable=bool(pos_adds) and pos_adds <= PROXY_POS, n_ref_other_raw=len(other), n_ref_other_samepol_dedup=len(dedup), n_libs_other=len({r["lib"] for r in other}))


S = [("NP_N", lambda A: A["q_all_neg"]), ("NP_X", lambda A: A["q_has_pos"] and not A["q_has_hna"]), ("NP_H", lambda A: A["q_has_hna"])]
attrs = {r["inchikey14"]: r for r in elig.select("inchikey14", "scorer_key", "scorer_ik14", "identity_group", "n_ref", "n_libs").iter_rows(named=True)}
taken = set(); out = []; strata_counts = {}
for name, cond in S:
    n_need = NN[name.split("_")[1]]; cand = []
    for ik, r in attrs.items():
        libs = sorted({x["lib"] for x in rows_of.get(ik, [])} - NO_QUERY_LIBS); qual = []
        for L in libs:
            A = analyse(ik, L)
            if A and cond(A): qual.append((L, A))
        if qual: cand.append((ik, qual))
    cand = [(ik, q) for ik, q in cand if attrs[ik]["identity_group"] not in taken]
    cand.sort(key=lambda t: t[0]); perm = rng.permutation(len(cand)); seen = set(); picked = []
    for i in perm:
        ik, qual = cand[i]; g = attrs[ik]["identity_group"]
        if g in seen: continue
        seen.add(g); L, A = qual[int(rng.integers(len(qual)))] if len(qual) > 1 else qual[0]; r = attrs[ik]
        sub = ("proxy_capable" if A["q_proxy_capable"] else "other_positive") if name == "NP_X" else ""
        picked.append(dict(set=name, group="eval", molecule=ik, scorer_key=r["scorer_key"] or r["scorer_ik14"], raw_key=ik, lib=L, identity_group=int(g), sublabel=sub,
                           n_qualifying_libs=len(qual), n_ref_total=int(r["n_ref"]), n_libs_total=int(r["n_libs"]), **A))
        if len(picked) >= 2 * n_need: break
    for i, p in enumerate(picked): p["role"] = "dev" if i < n_need else "conf"; taken.add(p["identity_group"]); out.append(p)
    strata_counts[name] = dict(candidates=len(cand), dev=min(n_need, len(picked)), conf=max(0, len(picked) - n_need))
    libs_ = pl.DataFrame(picked)["lib"].value_counts().sort("count", descending=True).to_dict(as_series=False) if picked else {}
    print(f"{name}: candidates {len(cand)} -> dev {strata_counts[name]['dev']} conf {strata_counts[name]['conf']}; libs {libs_}", flush=True)
df = pl.DataFrame(out)
for role, d_ in (("dev", a.out_dir), ("conf", a.conf_dir)):
    os.makedirs(d_, exist_ok=True); part = df.filter(pl.col("role") == role).drop("role"); part.write_csv(f"{d_}/p2_molecules.csv"); print(role, part.height, "->", f"{d_}/p2_molecules.csv")
dev_g = set(df.filter(pl.col("role") == "dev")["identity_group"]); con_g = set(df.filter(pl.col("role") == "conf")["identity_group"])
checks = dict(dev_conf_group_intersection=len(dev_g & con_g), selected_vs_used_groups=len((dev_g | con_g) & used_groups), selected_vs_used_keys=len(set(df["molecule"]) & used),
              one_per_group=int(df["identity_group"].n_unique() == df.height))
man = dict(version="p3np", seed=a.seed, n=NN, fold_identity=a.fold, strata=[s[0] for s in S], counts=counts, strata_counts=strata_counts, checks=checks, exclude=a.exclude, exclude_sha256=excl_sha,
           inputs_sha256=dict(census=sha(a.census), structures=sha(f"{a.folds}/structures.parquet"), selector=sha(os.path.abspath(__file__)), pool=sha(a.pool)))
for d_ in (a.out_dir, a.conf_dir): json.dump(man, open(f"{d_}/p2_select_manifest.json", "w"), indent=1)
print("checks", checks, f"({time.time()-t0:.0f}s)")
assert all(v == 0 for k, v in checks.items() if k != "one_per_group") and checks["one_per_group"] == 1, checks
