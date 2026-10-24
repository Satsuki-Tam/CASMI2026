"""E2c evaluation: end-to-end funnel MRR@25 on the top-K FPNet shortlist with GLACIER/ICEBERG rescoring.

Usage: python -X utf8 e2c_evaluate.py <funnel_dir> <set_name> [--gl gl.json] [--ice ice.json]
Lists are the top-K window candidates in FPNet order (e2c_<set>_in.json); the truth is located by raw InChIKey14 match
(truth_rank_fp from the funnel). Variants: FP order; z(FP)+z(GL) over the top-40 / top-K; z(FP)+z(ICE)+z(GL).
Molecules whose truth is outside the shortlist score 0 (they are the recall loss of stages 1-2).
"""
import argparse, json
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")

ap = argparse.ArgumentParser(); ap.add_argument("funnel_dir"); ap.add_argument("set_name"); ap.add_argument("--gl"); ap.add_argument("--ice")
a = ap.parse_args()
rng = np.random.default_rng(20261024)
items = json.load(open(f"{a.funnel_dir}/e2c_{a.set_name}_in.json"))
fun = pd.read_csv(f"{a.funnel_dir}/funnel_{a.set_name}.csv").set_index("molecule")
src = {k: json.load(open(p)) for k, p in (("gl", a.gl), ("ice", a.ice)) if p}


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.zeros_like(x)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    return out


def rr_at(order_idx, truth_pos):
    if truth_pos is None: return 0.0
    r = int(np.where(order_idx == truth_pos)[0][0]) + 1
    return 1.0 / r if r <= 25 else 0.0


rows = {}
for it in items:
    mid, cands = it["mid"], it["cands"]; n = len(cands)
    truth_raw = Chem.MolToInchiKey(Chem.MolFromSmiles(it["truth_smiles"]))[:14]
    keys = [Chem.MolToInchiKey(Chem.MolFromSmiles(s))[:14] if Chem.MolFromSmiles(s) else "" for s in cands]
    tpos = keys.index(truth_raw) if truth_raw in keys else None
    fp_order = np.arange(n)
    rec = {"n": n, "truth_in_shortlist": tpos is not None, "fp": rr_at(fp_order, tpos)}
    fp_rank_score = -np.arange(n, dtype=float)            # FP order as a score (rank-based)
    for k, d in src.items():
        dd = d.get(mid, {}) or {}
        sc = np.array([dd.get(s) if dd.get(s) is not None else np.nan for s in cands], float)
        for w in (40, n):
            fused = fp_rank_score.copy().astype(float)
            # fuse only inside the top-w: z over the window, candidates beyond keep their FP order below
            f = z(fp_rank_score[:w]) + z(sc[:w])
            idx = np.argsort(-f, kind="stable")
            order = np.concatenate([idx, np.arange(w, n)])
            rec[f"fp+{k}@{w if w < n else 'K'}"] = rr_at(order, tpos)
        rec[f"{k}_only@K"] = rr_at(np.argsort(-np.nan_to_num(sc, nan=-1e9), kind="stable"), tpos)
    if {"gl", "ice"} <= src.keys():
        g = np.array([(src["gl"].get(mid, {}) or {}).get(s) if (src["gl"].get(mid, {}) or {}).get(s) is not None else np.nan for s in cands], float)
        i_ = np.array([(src["ice"].get(mid, {}) or {}).get(s) if (src["ice"].get(mid, {}) or {}).get(s) is not None else np.nan for s in cands], float)
        f = z(fp_rank_score) + z(g) + z(i_); rec["fp+ice+gl@K"] = rr_at(np.argsort(-f, kind="stable"), tpos)
    rows[mid] = rec
df = pd.DataFrame(rows).T.join(fun[["n_window", "truth_in_window", "fp_rank", "lib"]], how="left")
print(f"{a.set_name}: {len(df)} molecules | truth in window {int(df.truth_in_window.sum())} | truth in shortlist(K) {int(df.truth_in_shortlist.sum())} | window median {df.n_window.median():.0f}")
cols = [c for c in df.columns if c not in ("n", "truth_in_shortlist", "n_window", "truth_in_window", "fp_rank", "lib")]
for c in cols:
    v = df[c].values.astype(float); idx = rng.integers(0, len(v), (20000, len(v))); ci = np.quantile(v[idx].mean(1), [.025, .975])
    print(f"  {c:16s} MRR@25 {v.mean():.4f} CI [{ci[0]:.3f},{ci[1]:.3f}] top1 {(v==1).mean():.3f} hit25 {(v>0).mean():.3f}")
for a_, b_ in (("fp+gl@40", "fp"), ("fp+gl@K", "fp"), ("fp+gl@K", "fp+gl@40"), ("fp+ice+gl@K", "fp+gl@K")):
    if a_ in df.columns and b_ in df.columns:
        d = df[a_].values.astype(float) - df[b_].values.astype(float); idx = rng.integers(0, len(d), (20000, len(d))); ci = np.quantile(d[idx].mean(1), [.025, .975])
        print(f"  Δ {a_} − {b_}: {d.mean():+.4f} CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
df.to_csv(f"{a.funnel_dir}/e2c_results_{a.set_name}.csv")
