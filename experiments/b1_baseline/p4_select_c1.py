"""112 (Codex 109 Q1, Codex 110 census refinement): fold-<fold> NP class-1 bank, selected from METADATA ONLY (no candidate, FP, GLACIER or
library-similarity value is read). Population: raw keys of eval_set2/census.parquet whose GLOBAL identity group (identity_folds/structures.parquet)
is in identity fold <fold>. A group is excluded if ANY of its raw keys is an MSG member (in_msg_raw | in_msg_scorer), if any selection CSV
(every p1_/p2_molecules.csv under experiments/, resolved to global groups by scorer_key / raw_key / molecule / inchikey14 -- never by a CSV's own
identity_group column, which is a local index in the panel CSV; an unresolved row is an error) uses it, or if it has a spectrum in the NP-example
(panel) library. Query acquisition = (raw key, NP library L): the shared selector's queries (b1_common.select_queries, max 8, test adducts);
qualifies if the queries are positive with [M+H]+ / [M+Na]+ (pol = pos) or all negative (pol = neg), and the same-polarity OTHER-library spectra
after removing cross-library copies of a query (metadata de-dup on adduct, precursor 3 dp, CE 1 dp, n_peaks; an upper bound of the evaluator's
usable C1 references, recorded as such) number >= 1. Strata: pol x refs (few 1-9 / many >= 10). One acquisition per global group: fixed-seed
choice among the group's qualifying acquisitions (sorted by raw key, library); the group's stratum is that acquisition's. Each stratum's groups are
permuted with the seed and dealt alternately to c1dev (development protection) and c1conf (one-time confirmation of a frozen candidate).
Writes <out>/c1dev/p2_molecules.csv, <out>/c1conf/p2_molecules.csv, <out>/c1bank_manifest.json.
Usage: python -X utf8 p4_select_c1.py --census eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds
         --fold 1 --seed 112 --out c1bank_f1"""
import argparse, glob, hashlib, json, os, sys, time
import numpy as np, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, select_queries
NP_LIBS = ["gnps", "riken", "mona", "massbank", "msdial"]; COVERED = {"[M+H]+", "[M+Na]+"}
ap = argparse.ArgumentParser()
for k in ("census", "store", "folds", "out"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--fold", type=int, required=True); ap.add_argument("--seed", type=int, required=True); ap.add_argument("--max_spectra", type=int, default=8)
ap.add_argument("--ref_many", type=int, default=10); ap.add_argument("--panel_lib", default="enveda-np-examples")
a = ap.parse_args(); t0 = time.time(); rng = np.random.default_rng(a.seed)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
OUT = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
P = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
folds = pl.read_parquet(P(f"{a.folds}/structures.parquet")).select("inchikey14", "scorer_key", "identity_group", "fold_identity").unique("inchikey14")
ik2g = dict(zip(folds["inchikey14"].to_list(), folds["identity_group"].to_list())); sk2g = dict(zip(folds["scorer_key"].cast(pl.Utf8).to_list(), folds["identity_group"].to_list()))
meta = pl.read_parquet(P(f"{a.store}/spec_meta.parquet"))
# ---- used groups: every selection CSV, resolved by keys (zero unresolved rows allowed)
files = sorted(set(glob.glob(os.path.join(ROOT, "experiments", "**", "p1_molecules.csv"), recursive=True) + glob.glob(os.path.join(ROOT, "experiments", "**", "p2_molecules.csv"), recursive=True)
                   + glob.glob(os.path.join(ROOT, "experiments", "**", "p2_dev_molecules.csv"), recursive=True)))
files = [f for f in files if not os.path.abspath(f).startswith(os.path.abspath(OUT) + os.sep)]
used, unresolved, per_file = set(), [], {}
for f in files:
    d = pl.read_csv(f, infer_schema_length=10000); n_ok = 0
    cols = [c for c in ("scorer_key", "raw_key", "molecule", "inchikey14") if c in d.columns]
    if not cols: raise SystemExit(f"selection file without identity columns: {f}")
    for r in d.select(cols).iter_rows(named=True):
        g = None
        if r.get("scorer_key") is not None: g = sk2g.get(str(r["scorer_key"]))
        for c in ("raw_key", "molecule", "inchikey14"):
            if g is None and r.get(c) is not None: g = ik2g.get(str(r[c]), sk2g.get(str(r[c])))
        if g is None: unresolved.append((os.path.relpath(f, ROOT), r)); continue
        used.add(int(g)); n_ok += 1
    per_file[os.path.relpath(f, ROOT)] = n_ok
if unresolved: raise SystemExit(f"{len(unresolved)} selection rows not resolved to a global group, e.g. {unresolved[:3]}")
panel_groups = {int(ik2g[k]) for k in meta.filter(pl.col("ingest_lib") == a.panel_lib)["inchikey14"].unique().to_list() if k in ik2g}
used_all = used | panel_groups
c = pl.read_parquet(P(a.census)).join(folds.select("inchikey14", "scorer_key", "identity_group", "fold_identity"), on="inchikey14", how="left")
msg_groups = set(c.filter(pl.col("in_msg_raw") | pl.col("in_msg_scorer"))["identity_group"].drop_nulls().cast(pl.Int64).to_list())
elig = c.filter((pl.col("fold_identity") == a.fold) & pl.col("identity_group").is_not_null()).with_columns(pl.col("identity_group").cast(pl.Int64))
counts = dict(census_raw_keys=c.height, fold_raw_keys=elig.height, fold_groups=elig["identity_group"].n_unique())
elig = elig.filter(~pl.col("identity_group").is_in(list(used_all))); counts["after_used_and_panel"] = elig["identity_group"].n_unique()
elig = elig.filter(~pl.col("identity_group").is_in(list(msg_groups))); counts["after_msg_any"] = elig["identity_group"].n_unique()
print(f"files {len(files)}, used groups {len(used):,} + panel {len(panel_groups)}; fold {a.fold}: {counts} ({time.time() - t0:.0f}s)", flush=True)
m = meta.filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)) & pl.col("inchikey14").is_in(elig["inchikey14"].to_list())).with_columns(
    pl.col("ce_mean").fill_null(-1.0).round(1).alias("ce_r"), pl.col("precursor_mz").round(3).alias("prec_r"))
rows_of = {}
for ik, lib, add, mode, ce, pr, npk, row in m.select("inchikey14", "ingest_lib", "adduct", "ionization_mode", "ce_r", "prec_r", "n_peaks", "row").iter_rows():
    rows_of.setdefault(ik, []).append(dict(lib=lib, adduct=add, mode=mode, ce=ce, prec=pr, npk=npk, row=row))


def analyse(ik, L):
    rs = rows_of.get(ik, []); qrows = sorted((r for r in rs if r["lib"] == L), key=lambda r: r["row"])
    if not qrows: return None
    q = select_queries(qrows, a.max_spectra, lambda r: r["adduct"], lambda r: (None if r["ce"] < 0 else r["ce"]))
    modes = {r["mode"] for r in q}; adds = {r["adduct"] for r in q}; qkeys = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in q}
    other = [r for r in rs if r["lib"] != L and r["mode"] in modes]
    dedup = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in other} - qkeys
    pol = "pos" if (adds & COVERED and all(r["mode"] == "positive" for r in q)) else ("neg" if all(r["mode"] == "negative" for r in q) else None)
    return dict(n_q=len(q), q_adducts="|".join(sorted(adds)), pol=pol, n_ref_other_samepol_dedup=len(dedup), n_libs_other=len({r["lib"] for r in other}))


acq = {}
for r in elig.select("inchikey14", "scorer_key", "scorer_ik14", "identity_group").iter_rows(named=True):
    ik = r["inchikey14"]
    for L in sorted({x["lib"] for x in rows_of.get(ik, []) if x["lib"] in NP_LIBS}):
        A = analyse(ik, L)
        if A and A["pol"] and A["n_ref_other_samepol_dedup"] >= 1:
            st = f"{A['pol']}_{'many' if A['n_ref_other_samepol_dedup'] >= a.ref_many else 'few'}"
            acq.setdefault(int(r["identity_group"]), []).append((ik, L, A, st, r["scorer_key"] or r["scorer_ik14"]))
groups = sorted(acq); chosen = {}
for g in groups:
    lst = sorted(acq[g], key=lambda t: (t[0], t[1])); chosen[g] = lst[int(rng.integers(len(lst)))] if len(lst) > 1 else lst[0]
out = []; strata = {}
for st in ("pos_few", "pos_many", "neg_few", "neg_many"):
    gs = [g for g in groups if chosen[g][3] == st]; perm = rng.permutation(len(gs))
    for k, i in enumerate(perm):
        g = gs[i]; ik, L, A, _, sk = chosen[g]
        out.append(dict(set=f"C1_{st}", group="eval", molecule=ik, scorer_key=sk, raw_key=ik, lib=L, identity_group=g, n_acq_group=len(acq[g]), role="c1dev" if k % 2 == 0 else "c1conf",
                        **{kk: vv for kk, vv in A.items() if kk != "pol"}))
    strata[st] = dict(groups=len(gs), c1dev=(len(gs) + 1) // 2, c1conf=len(gs) // 2)
    print(f"C1_{st}: {len(gs)} groups (c1dev {(len(gs) + 1) // 2} / c1conf {len(gs) // 2}); query libs {pl.DataFrame([o for o in out if o['set'] == 'C1_' + st])['lib'].value_counts().sort('count', descending=True).to_dict(as_series=False) if gs else {}}", flush=True)
df = pl.DataFrame(out)
checks = dict(one_per_group=int(df["identity_group"].n_unique() == df.height), vs_used=len(set(df["identity_group"]) & used_all), vs_msg=len(set(df["identity_group"]) & msg_groups),
              halves_disjoint=len(set(df.filter(pl.col("role") == "c1dev")["identity_group"]) & set(df.filter(pl.col("role") == "c1conf")["identity_group"])),
              fold_ok=int(all(r == a.fold for r in folds.filter(pl.col("identity_group").is_in(df["identity_group"].to_list()))["fold_identity"].unique().to_list())))
assert checks["one_per_group"] == 1 and checks["vs_used"] == 0 and checks["vs_msg"] == 0 and checks["halves_disjoint"] == 0 and checks["fold_ok"] == 1, checks
for role in ("c1dev", "c1conf"):
    os.makedirs(os.path.join(OUT, role), exist_ok=True); df.filter(pl.col("role") == role).drop("role").write_csv(os.path.join(OUT, role, "p2_molecules.csv"))
man = dict(seed=a.seed, fold=a.fold, max_spectra=a.max_spectra, ref_many=a.ref_many, counts=counts, strata=strata, checks=checks, used_groups=len(used), panel_groups=len(panel_groups),
           msg_groups=len(msg_groups), selection_files=per_file, reference_count_definition="same-polarity other-library spectra minus cross-library copies of a query (metadata de-dup); before the evaluator's spectral duplicate rule and MAX_REF; upper bound",
           inputs_sha256=dict(census=sha(P(a.census)), structures=sha(P(f"{a.folds}/structures.parquet")), selector=sha(os.path.abspath(__file__)), b1_common=sha(os.path.join(HERE, "b1_common.py"))))
json.dump(man, open(os.path.join(OUT, "c1bank_manifest.json"), "w"), indent=1)
print("checks", checks, "rows", df.height, f"({time.time() - t0:.0f}s)")
