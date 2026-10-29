"""W135 fold-0 audit (140_decision.md §4; metadata only, no model output): how many fold-0 COCONUT-truth identities remain for a new
confirmation set after removing (a) every identity / identity group used as a TEACHER of P (the v8w7a training runs: p1 fit, eval_set, eval_c1,
train_pool_f3a / f4a), (b) every identity / group of any development table (the census 'used' flag), (c) the W135 batches of folds 1 / 2, (d)
panel and MSG keys (census filters), all mapped by raw key, scorer key and the GLOBAL identity group of identity_folds/structures.parquet;
and how many Butina-0.5 families (fold-0 census labels) and C1-eligible molecules (batch-metadata proxy; the world rule must be re-applied on
any batch built later) remain. Writes experiments/w135/fold0_audit.json.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_fold0_audit.py"""
import glob, hashlib, json, os
import polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
st = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet")).select("inchikey14", "scorer_key", "identity_group")
grp_of = {}
for ik, sk, g in st.iter_rows():
    if g is None: continue
    grp_of[ik] = g
    if sk: grp_of[sk] = g
def ids_of(csv):
    d = pl.read_csv(csv, infer_schema_length=10000); out = set()
    for col in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if col in d.columns: out |= set(str(x) for x in d[col].drop_nulls().to_list())
    return out
TEACH = ["experiments/p1_baseline/run1/p1_molecules.csv", "experiments/b1_baseline/eval_set/p1_molecules.csv", "experiments/b1_baseline/eval_c1/p1_molecules.csv",
         "experiments/b1_baseline/train_pool_f3a/p2_molecules.csv", "experiments/b1_baseline/train_pool_f4a/p2_molecules.csv"]
teach = set().union(*[ids_of(os.path.join(ROOT, f)) for f in TEACH]); teach_g = {grp_of[k] for k in teach if k in grp_of}
w135 = set().union(*[ids_of(f) for f in glob.glob(os.path.join(ROOT, "experiments/w135/batches/*.csv"))]); w135_g = {grp_of[k] for k in w135 if k in grp_of}
P = pl.read_parquet(os.path.join(ROOT, "experiments/w135/census_fold0/population.parquet"))
P = P.with_columns(pl.col("identity_group").cast(pl.Int64))
c = dict(population=P.height)
t_mask = pl.col("inchikey14").is_in(list(teach)) | pl.col("scorer_key").is_in(list(teach)) | pl.col("identity_group").is_in(list(teach_g))
c["teacher_of_P"] = int(P.filter(t_mask).height); c["used_dev"] = int(P.filter(pl.col("used")).height)
c["w135_overlap"] = int(P.filter(pl.col("inchikey14").is_in(list(w135)) | pl.col("identity_group").is_in(list(w135_g))).height)
R = P.filter(~t_mask & ~pl.col("inchikey14").is_in(list(w135)) & ~pl.col("identity_group").is_in(list(w135_g)))
c["after_teacher_and_w135"] = R.height; c["after_teacher_w135_unused"] = int(R.filter(~pl.col("used")).height)
for nm, D in (("clean", R), ("clean_unused", R.filter(~pl.col("used")))):
    fs = D.group_by("fam50").len(); c[f"{nm}_families_ge2"] = int((fs["len"] >= 2).sum()); c[f"{nm}_members_in_fam_ge2"] = int(fs.filter(pl.col("len") >= 2)["len"].sum())
c["teacher_files_sha256"] = {f: sha(os.path.join(ROOT, f)) for f in TEACH}; c["script_sha256"] = sha(os.path.abspath(__file__))
json.dump(c, open(os.path.join(ROOT, "experiments/w135/fold0_audit.json"), "w"), indent=1); print(json.dumps({k: v for k, v in c.items() if not k.endswith("sha256")}, indent=1))
