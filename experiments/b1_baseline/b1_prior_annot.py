"""Codex 016: official-identity-aligned prior annotation table for evaluation molecules (no 'literature count' label: the columns are the
public PubChem-derived quantities used by the B1 prior, kept separate, with missing distinguished from true zero).
Source: data/external/v2_pool/pool_meta.parquet (key = raw InChIKey14, pid = row of pubchem_popularity/pool_*.npy): lsid (log substance ids),
lpmid (log PubMed ids), lsynonyms (log synonyms), np (NP flag class), src_mask (source bitmask), lotus_refs (LOTUS reference count), and the
composite pop_public exactly as b1_features computes it. Molecules without a pool row get null columns (not 0) and has_pool_row = False.
Quantile boundaries for post-stratification are fixed on the development set (--bins_from) and written to the manifest.
Usage: python -X utf8 b1_prior_annot.py --pool data/external/v2_pool/pool_meta.parquet --pop data/external/pubchem_popularity --keys data/processed/train_scorer_keys.parquet
         --eval CSV... --bins_from eval_set/p1_molecules.csv --out eval_set2/prior_annot.parquet
"""
import argparse, json, os
import numpy as np, polars as pl
ap = argparse.ArgumentParser(); ap.add_argument("--pool", required=True); ap.add_argument("--pop", required=True); ap.add_argument("--keys", required=True)
ap.add_argument("--eval", nargs="+", required=True); ap.add_argument("--bins_from", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
pm = pl.read_parquet(a.pool).select("key", "pid", "src", "train_sid", "np_likeness")
PL = {n: np.load(f"{a.pop}/pool_{n}.npy") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
pid = pm["pid"].to_numpy()
pm = pm.with_columns(*[pl.Series(n, np.asarray(PL[n][pid], dtype=np.float64)) for n in PL])
pm = pm.with_columns((pl.col("lsid") + pl.col("lpmid") + 0.5 * pl.col("lsynonyms") + 1.0 * (pl.col("np") != 0).cast(pl.Float64)
                      + 0.5 * ((pl.col("src_mask").cast(pl.Int64) & 1) != 0).cast(pl.Float64) + 0.5 * (pl.col("lotus_refs").clip(0, None) + 1.0).log()).alias("pop_public"))
# one row per raw key (several pool rows can share a key: keep the max pop_public, record the count)
pm1 = pm.group_by("key").agg(pl.len().alias("n_pool_rows"), *[pl.col(n).max() for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs", "pop_public")], pl.col("src").min().alias("src_min"))
keys = None   # scorer keys are carried by the evaluation CSVs themselves
frames = []
for f in a.eval:
    d = pl.read_csv(f, infer_schema_length=10000).select("set", "molecule", *(["scorer_key"] if "scorer_key" in pl.read_csv(f, n_rows=1).columns else [])).with_columns(pl.lit(os.path.relpath(f)).alias("eval_csv"))
    frames.append(d)
ev = pl.concat(frames, how="diagonal").join(pm1, left_on="molecule", right_on="key", how="left").with_columns(pl.col("n_pool_rows").is_not_null().alias("has_pool_row"))
cov = ev.group_by("eval_csv", "set").agg(pl.len().alias("n"), pl.col("has_pool_row").mean().round(3).alias("pool_coverage")).sort("eval_csv", "set")
print(cov)
# quantile boundaries fixed on the development set molecules (bins_from), applied to every set; missing stays null
dev = ev.filter(pl.col("eval_csv") == os.path.relpath(a.bins_from))
bounds = {}
for col in ("lsid", "lpmid", "lsynonyms", "lotus_refs", "pop_public"):
    q = dev[col].drop_nulls()
    bounds[col] = [float(q.quantile(x)) for x in (0.25, 0.5, 0.75)] if q.len() else None
    if bounds[col]:
        b = bounds[col]
        ev = ev.with_columns(pl.when(pl.col(col).is_null()).then(pl.lit(None)).when(pl.col(col) <= b[0]).then(pl.lit("q1")).when(pl.col(col) <= b[1]).then(pl.lit("q2")).when(pl.col(col) <= b[2]).then(pl.lit("q3")).otherwise(pl.lit("q4")).alias(f"{col}_bin"))
    print(col, "dev quartile boundaries", bounds[col], "| zero share (dev)", round(float((dev[col] == 0).mean()), 3) if q.len() else None)
ev.write_parquet(a.out)
json.dump(dict(bins_from=a.bins_from, boundaries=bounds, eval_csvs=a.eval, coverage=cov.to_dicts(), pop_public_formula="lsid + lpmid + 0.5*lsynonyms + 1[np!=0] + 0.5*1[src_mask&1] + 0.5*log1p(max(lotus_refs,0)) (b1_features)"),
          open(a.out.replace(".parquet", "_manifest.json"), "w"), indent=1)
print("wrote", a.out, ev.height, "rows")
