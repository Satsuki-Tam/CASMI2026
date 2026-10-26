"""Codex 016 (b): stratified evaluation molecules p2 v2 -- strata defined by the ACTUAL QUERY (shared selector, max 8) and by the other-library
references that remain after the query library is removed (same polarity as a query, metadata-level de-duplication, before MAX_REF; an upper
bound of the evaluator's usable C1 references, recorded as such). Exclusive strata (priority E, F, C, G, D), one molecule per identity group,
identity groups disjoint from every development set, fold_identity 0, ONE permutation (seed): first n per stratum = dev2, next n = locked2.
  E_np_negonly   NP query library whose selected queries are all negative
  F_np_uncovered NP query library with a positive query but no [M+H]+/[M+Na]+ (sub-label: proxy-capable NH4/water-loss only vs K/other)
  C_np_crosslib  NP query library with an [M+H]+/[M+Na]+ query (native forward usable) and >= REF_MIN remaining same-polarity other-library refs
  G_tims_crosslib enveda-180 (timsTOF) query with >= 1 remaining same-polarity other-library ref (sub-label few 1-9 / many >= REF_MIN)
  D_np_single    NP, single library, <= 2 spectra, [M+H]+/[M+Na]+ query (no independent true reference; forward usable)
Query library among qualifying NP libraries: fixed-seed choice (per-library counts recorded); ties never depend on dict order.
Usage: python -X utf8 p2_select_v2.py --census eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds
         --exclude CSV... --n 100 --seed 5 --out_dir eval_set2/v2 --locked_dir locked_eval2/v2 [--ref_min 10] [--max_spectra 8]
"""
import argparse, hashlib, json, os, sys, time
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import ADDUCT_SHIFT, select_queries
NP_LIBS = ["gnps", "riken", "mona", "massbank", "msdial"]; COVERED = {"[M+H]+", "[M+Na]+"}; PROXY_POS = {"[M+NH4]+", "[M-H2O+H]+", "[M-2H2O+H]+"}
ap = argparse.ArgumentParser(); ap.add_argument("--census", required=True); ap.add_argument("--store", required=True); ap.add_argument("--folds", required=True)
ap.add_argument("--exclude", nargs="*", default=[]); ap.add_argument("--n", type=int, default=100); ap.add_argument("--seed", type=int, default=5)
ap.add_argument("--out_dir", required=True); ap.add_argument("--locked_dir", required=True); ap.add_argument("--panel_lib", default="enveda-np-examples")
ap.add_argument("--ref_min", type=int, default=10); ap.add_argument("--max_spectra", type=int, default=8)
ap.add_argument("--fold", type=int, default=0, help="identity fold of the selection (default 0 = unchanged; 2026-10-26: fold 1 + fold-1 FPNet = fresh sets unseen by FPNet and ranker)")
a = ap.parse_args(); t0 = time.time(); rng = np.random.default_rng(a.seed)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
counts = {}
c = pl.read_parquet(a.census); counts["census_raw_keys"] = c.height
folds = pl.read_parquet(f"{a.folds}/structures.parquet").select("inchikey14", "scorer_key", "identity_group", "fold_identity").unique("inchikey14")
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet").filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
# ---- exclusions: development identities -> identity groups (a read failure is an error, not a skip)
used = set(); excl_sha = {}
for f in a.exclude:
    d = pl.read_csv(f, infer_schema_length=10000); excl_sha[f] = sha(f); found = False
    for col in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if col in d.columns: used |= set(str(x) for x in d[col].drop_nulls().to_list()); found = True
    if not found: raise SystemExit(f"exclusion file without identity columns: {f}")
panel_keys = set(meta.filter(pl.col("ingest_lib") == a.panel_lib)["inchikey14"].to_list()); used |= panel_keys
used_groups = set(folds.filter(pl.col("inchikey14").is_in(list(used)) | pl.col("scorer_key").is_in(list(used)))["identity_group"].to_list())
c = c.join(folds, on="inchikey14", how="left")
s1 = c.filter(~pl.col("in_msg_raw") & ~pl.col("in_msg_scorer")); counts["after_msg_exclusion"] = s1.height
s2 = s1.filter(~pl.col("in_dev") & ~pl.col("identity_group").is_in(list(used_groups)) & pl.col("identity_group").is_not_null()); counts["after_dev_identity_group_exclusion"] = s2.height
elig = s2.filter(pl.col("fold_identity") == a.fold); counts["fold0_eligible_raw_keys"] = elig.height; counts["fold0_eligible_groups"] = elig["identity_group"].n_unique(); counts["fold"] = a.fold
print(f"census {counts['census_raw_keys']:,} -> not MSG {counts['after_msg_exclusion']:,} -> not dev (keys {len(used):,}, groups {len(used_groups):,}) {counts['after_dev_identity_group_exclusion']:,} -> fold 0 {counts['fold0_eligible_raw_keys']:,} raw keys / {counts['fold0_eligible_groups']:,} groups ({time.time()-t0:.0f}s)", flush=True)
# ---- per-molecule spectra rows (eligible molecules only)
m = meta.filter(pl.col("inchikey14").is_in(elig["inchikey14"].to_list())).with_columns(pl.col("ce_mean").fill_null(-1.0).round(1).alias("ce_r"), pl.col("precursor_mz").round(3).alias("prec_r"))
rows_of = {}
for ik, lib, add, mode, ce, pr, npk, row in m.select("inchikey14", "ingest_lib", "adduct", "ionization_mode", "ce_r", "prec_r", "n_peaks", "row").iter_rows():
    rows_of.setdefault(ik, []).append(dict(lib=lib, adduct=add, mode=mode, ce=ce, prec=pr, npk=npk, row=row))
print(f"spectra rows for eligible molecules: {m.height:,} ({time.time()-t0:.0f}s)", flush=True)


def analyse(ik, L):
    """Queries from library L (shared selector) and the remaining other-library references of the same polarity (metadata de-dup; upper bound)."""
    rs = rows_of.get(ik, []); qrows = sorted((r for r in rs if r["lib"] == L), key=lambda r: r["row"])
    if not qrows: return None
    q = select_queries(qrows, a.max_spectra, lambda r: r["adduct"], lambda r: (None if r["ce"] < 0 else r["ce"]))
    modes = {r["mode"] for r in q}; adds = {r["adduct"] for r in q}; qkeys = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in q}
    pos_adds = {r["adduct"] for r in q if r["mode"] == "positive"}
    other = [r for r in rs if r["lib"] != L and r["mode"] in modes]
    dedup = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in other} - qkeys           # cross-library copies of a query spectrum are never usable
    return dict(n_q=len(q), q_adducts="|".join(sorted(adds)), q_has_hna=bool(adds & COVERED), q_all_neg=all(r["mode"] == "negative" for r in q), q_has_pos=any(r["mode"] == "positive" for r in q),
                q_proxy_capable=bool(pos_adds) and pos_adds <= PROXY_POS, n_ref_other_raw=len(other), n_ref_other_samepol_dedup=len(dedup), n_libs_other=len({r["lib"] for r in other}))


def qualifying(ik, fam, cond):
    libs = [L for L in sorted({r["lib"] for r in rows_of.get(ik, [])}) if (fam == "np" and L in NP_LIBS) or (fam == "tims" and L == "enveda-180")]
    out = []
    for L in libs:
        A = analyse(ik, L)
        if A and cond(A): out.append((L, A))
    return out


S = [("E_np_negonly", "np", lambda A: A["q_all_neg"]),
     ("F_np_uncovered", "np", lambda A: A["q_has_pos"] and not A["q_has_hna"]),
     ("C_np_crosslib", "np", lambda A: A["q_has_hna"] and A["n_ref_other_samepol_dedup"] >= a.ref_min),
     ("G_tims_crosslib", "tims", lambda A: A["n_ref_other_samepol_dedup"] >= 1),
     ("D_np_single", "np", lambda A: A["q_has_hna"] and A["n_libs_other"] == 0)]
attrs = {r["inchikey14"]: r for r in elig.select("inchikey14", "scorer_key", "scorer_ik14", "identity_group", "n_ref", "n_libs", "has_timstof", "in_nplib", "in_enveda180").iter_rows(named=True)}
taken = set(); out = []; strata_counts = {}
for name, fam, cond in S:
    cand = []
    for ik, r in attrs.items():
        if name == "D_np_single" and not (r["n_libs"] == 1 and r["n_ref"] <= 2): continue
        if fam == "np" and not r["in_nplib"]: continue
        if fam == "tims" and not r["in_enveda180"]: continue
        qual = qualifying(ik, fam, cond)
        if qual: cand.append((ik, qual))
    groups_before = len({attrs[ik]["identity_group"] for ik, _ in cand})
    cand = [(ik, qual) for ik, qual in cand if attrs[ik]["identity_group"] not in taken]
    groups_after = len({attrs[ik]["identity_group"] for ik, _ in cand})
    cand.sort(key=lambda t: t[0]); perm = rng.permutation(len(cand)); seen = set(); picked = []
    for i in perm:
        ik, qual = cand[i]; g = attrs[ik]["identity_group"]
        if g in seen: continue
        seen.add(g); L, A = qual[int(rng.integers(len(qual)))] if len(qual) > 1 else qual[0]
        r = attrs[ik]
        sub = ""
        if name == "F_np_uncovered": sub = "proxy_capable" if A["q_proxy_capable"] else "other_positive"
        if name == "G_tims_crosslib": sub = "many_refs" if A["n_ref_other_samepol_dedup"] >= a.ref_min else "few_refs"
        picked.append(dict(set=name, group="eval", molecule=ik, scorer_key=r["scorer_key"] or r["scorer_ik14"], raw_key=ik, lib=L, identity_group=int(g), sublabel=sub, n_qualifying_libs=len(qual),
                           n_ref_total=int(r["n_ref"]), n_libs_total=int(r["n_libs"]), has_timstof=bool(r["has_timstof"]), in_nplib=bool(r["in_nplib"]), in_enveda180=bool(r["in_enveda180"]), **A))
        if len(picked) >= 2 * a.n: break
    for i, p in enumerate(picked): p["role"] = "dev2" if i < a.n else "locked2"; taken.add(p["identity_group"]); out.append(p)
    strata_counts[name] = dict(qualifying_groups_before_allocation=groups_before, qualifying_groups_after_allocation=groups_after, dev2=min(a.n, len(picked)), locked2=max(0, len(picked) - a.n))
    libs = pl.DataFrame(picked)["lib"].value_counts().sort("count", descending=True).to_dict(as_series=False) if picked else {}
    subs = pl.DataFrame(picked)["sublabel"].value_counts().to_dict(as_series=False) if picked else {}
    print(f"{name:<16s} groups before/after allocation {groups_before:>5}/{groups_after:>5} -> dev2 {strata_counts[name]['dev2']:>3} / locked2 {strata_counts[name]['locked2']:>3}; query libs {libs}; sublabels {subs}", flush=True)
df = pl.DataFrame(out)
for role, d_ in (("dev2", a.out_dir), ("locked2", a.locked_dir)):
    os.makedirs(d_, exist_ok=True); part = df.filter(pl.col("role") == role).drop("role"); part.write_csv(f"{d_}/p2_molecules.csv"); print(role, part.height, "->", f"{d_}/p2_molecules.csv")
dev_g = set(df.filter(pl.col("role") == "dev2")["identity_group"]); loc_g = set(df.filter(pl.col("role") == "locked2")["identity_group"])
checks = dict(dev2_locked2_group_intersection=len(dev_g & loc_g), selected_vs_used_groups=len((dev_g | loc_g) & used_groups), selected_vs_used_keys=len(set(df["molecule"]) & used), one_per_group=int(df["identity_group"].n_unique() == df.height))
man = dict(version="v2", seed=a.seed, n_per_stratum=a.n, split_method="one permutation per stratum: first n = dev2, next n = locked2", max_spectra=a.max_spectra, ref_min=a.ref_min, fold_identity=0,
           strata=[s[0] for s in S], stratum_priority="E, F, C, G, D (exclusive by identity group)", query_library_policy="fixed-seed choice among qualifying libraries of the stratum family; enveda-180 fixed for G",
           reference_count_definition="other-library spectra whose polarity matches a selected query, metadata de-dup on (adduct, precursor 3dp, CE 1dp, n_peaks) minus cross-library copies of a query; before MAX_REF; upper bound of usable C1 refs",
           counts=counts, strata_counts=strata_counts, checks=checks, used_identities=len(used), used_groups=len(used_groups), exclude=a.exclude, exclude_sha256=excl_sha,
           inputs_sha256=dict(census=sha(a.census), structures=sha(f"{a.folds}/structures.parquet"), selector=sha(os.path.abspath(__file__)), b1_common=sha(os.path.join(os.path.dirname(os.path.abspath(__file__)), "b1_common.py"))))
for d_ in (a.out_dir, a.locked_dir): json.dump(man, open(f"{d_}/p2_select_manifest.json", "w"), indent=1)
print("checks", checks, f"({time.time()-t0:.0f}s)")
