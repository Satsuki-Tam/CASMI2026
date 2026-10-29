"""EXPLORATORY, label-using description (not a gate, not a selection): source groups of the truth and of the rank-1 in the frozen v8w7a main
lists (diag/top102_<tag>.parquet, top-25 dumps of the 102 evaluation), and the top-25-only effect of an E0-like window policy that drops
PubChem-only candidates outside PubChemLite and ChEBI / LIPID MAPS = outside E0's window (official keys from diag/e_window_keys_v2.parquet). Groups by official key: T = train structure
(pool src 1/3; in C2 the truth itself is treated as not train, as in the view), B = COCONUT not train (pool src 2), L = PubChem-only in PubChemLite or ChEBI / LIPID MAPS (BIO),
O = PubChem-only outside both (outside E0's window). The policy column removes O candidates from the top 25 and re-ranks the rest (candidates beyond rank 25
are unknown here, so a truth below 25 cannot be rescued: a LOWER bound on gains; a truth in O is lost).
Usage (Spark, experiments/b1_baseline): python -X utf8 x_srcmix.py"""
import os
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__))
pool = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "v2_pool", "pool_meta.parquet"), columns=["key", "src"]).to_pandas()
SRC = pool.groupby("key").src.agg(lambda s: set(int(x) for x in s)).to_dict()
K = pd.read_parquet(os.path.join(HERE, "diag/e_window_keys_v2.parquet")); PCL = set(K.key[K.in_pcl.astype(bool)].astype(str)); BIO = set(K.key[K.in_bio.astype(bool)].astype(str))
def grp(k, truth_c2=False):
    s = SRC.get(k, set())
    if not truth_c2 and (1 in s or 3 in s): return "T"
    if 2 in s or 3 in s: return "B"
    return "L" if (k in PCL or k in BIO) else "O"
L = ["# Source groups of the truth / rank-1 in the frozen v8w7a lists (exploratory; top-25 dumps of the 102 evaluation)", "",
     "| tag | set view | n | truth T / B / L / O / not in top25 | MRR | wrong rank-1: T / B / L / O | drop-O policy: MRR (top-25 lower bound) | rescued / lost |", "|---|---|---:|---|---:|---|---:|---|"]
for tag in ("np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel"):
    p = os.path.join(HERE, f"diag/top102_{tag}.parquet")
    if not os.path.exists(p): continue
    t = pd.read_parquet(p); t["okey"] = t.okey.astype(str)
    for (s, v), g in t.groupby(["set", "view"], sort=True):
        tg, wr, rr, rr2, res, lost = [], [], [], [], 0, 0
        for m, x in g.groupby("molecule", sort=False):
            x = x.sort_values("rank"); tr = x[x.is_truth.astype(bool)]
            cg = [grp(k, truth_c2=(v == "c2" and bool(it))) for k, it in zip(x.okey, x.is_truth)]
            if len(tr): tg.append(cg[int(np.flatnonzero(x.is_truth.values)[0])])
            else: tg.append("-")
            r0 = 1.0 / int(tr["rank"].iloc[0]) if len(tr) else 0.0; rr.append(r0)
            if r0 < 1 and len(x): wr.append(cg[0])
            keep = [i for i, c in enumerate(cg) if c != "O"]; pos = [i for i in keep if bool(x.is_truth.values[i])]
            r1 = 1.0 / (keep.index(pos[0]) + 1) if pos else 0.0; rr2.append(r1); res += r1 > r0 + 1e-12; lost += r1 < r0 - 1e-12
        n = len(rr); c = pd.Series(tg).value_counts(); w = pd.Series(wr).value_counts()
        L.append(f"| {tag} | {s} {v} | {n} | {c.get('T', 0)} / {c.get('B', 0)} / {c.get('L', 0)} / {c.get('O', 0)} / {c.get('-', 0)} | {np.mean(rr):.4f} | "
                 f"{w.get('T', 0)} / {w.get('B', 0)} / {w.get('L', 0)} / {w.get('O', 0)} | {np.mean(rr2):.4f} ({np.mean(rr2) - np.mean(rr):+.4f}) | {res} / {lost} |")
out = chr(10).join(L) + chr(10); open(os.path.join(HERE, "diag/x_srcmix.md"), "w", encoding="utf-8").write(out); print(out)
