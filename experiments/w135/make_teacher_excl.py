"""W135 fold-0 confirmation prep (140_decision §4): the fold-0 census identities that were TEACHERS of P (v8w7a training runs; mapped by raw key,
scorer key and global identity group, as w135_fold0_audit.py) written as an exclusion CSV for w135_batches_add.py (fam = -1: identity-level
exclusion only, their structural families stay eligible). Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/make_teacher_excl.py"""
import os
import polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
st = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet")).select("inchikey14", "scorer_key", "identity_group")
grp_of = {}
for ik, sk, g in st.iter_rows():
    if g is None: continue
    grp_of[ik] = g
    if sk: grp_of[sk] = g
TEACH = ["experiments/p1_baseline/run1/p1_molecules.csv", "experiments/b1_baseline/eval_set/p1_molecules.csv", "experiments/b1_baseline/eval_c1/p1_molecules.csv",
         "experiments/b1_baseline/train_pool_f3a/p2_molecules.csv", "experiments/b1_baseline/train_pool_f4a/p2_molecules.csv"]
teach = set()
for f in TEACH:
    d = pl.read_csv(os.path.join(ROOT, f), infer_schema_length=10000)
    for col in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if col in d.columns: teach |= set(str(x) for x in d[col].drop_nulls().to_list())
tg = {grp_of[k] for k in teach if k in grp_of}
P = pl.read_parquet(os.path.join(ROOT, "experiments/w135/census_fold0/population.parquet")).with_columns(pl.col("identity_group").cast(pl.Int64))
E = P.filter(pl.col("inchikey14").is_in(list(teach)) | pl.col("scorer_key").is_in(list(teach)) | pl.col("identity_group").is_in(list(tg)))
E.select(pl.col("inchikey14").alias("molecule"), "identity_group", pl.lit(-1).alias("fam")).write_csv(os.path.join(ROOT, "experiments/w135/batches/excl_teachers_fold0.csv"))
print(f"teacher identities in the fold-0 census: {E.height}")
