"""E2b v2 evaluation: forward-model (ICEBERG / GLACIER) and optional FPNet ranking of same-formula isomer panels.

Usage: python -X utf8 e2b_evaluate_v2.py <in.json> <molecules.csv> <out_json> [--ice ice.json] [--gl gl.json] [--fp fp_scores.json]

Candidates are already deduplicated on the official scorer key with the truth at index 0 (prepare_v2). Ranks use worst-case ties
(decoys with a score >= the truth's are counted as above it). The random baseline is the analytic E[RR@25] = H_min(n,25) / n.
Reports MRR@25 / top-1 / hit@25 with molecule-level bootstrap 95% CIs and paired-delta CIs vs. each single scorer, stratified by
truth_in_retrieval_window.
"""
import argparse, json, math
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("mols"); ap.add_argument("out")
ap.add_argument("--ice"); ap.add_argument("--gl"); ap.add_argument("--fp")
a = ap.parse_args()
rng = np.random.default_rng(20261024)
items = json.load(open(a.inp)); mols = pd.read_csv(a.mols).set_index("molecule")
src = {k: json.load(open(p)) for k, p in (("ice", a.ice), ("gl", a.gl), ("fp", a.fp)) if p}


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.zeros_like(x)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    return out


def rr(scores):
    s = np.asarray(scores, float); t = s[0]
    if not np.isfinite(t): return 0.0
    rank = 1 + int(np.sum(s[1:] >= t)); return 1.0 / rank if rank <= 25 else 0.0


def analytic_random(n):
    return sum(1.0 / r for r in range(1, min(n, 25) + 1)) / n


rows = {}
for it in items:
    mid, cands = it["mid"], it["cands"]; n = len(cands)
    rec = {"n": n, "random": analytic_random(n), "random_top1": 1.0 / n, "random_hit25": min(25, n) / n}
    sc = {}
    for k, d in src.items():
        dd = d.get(mid, {}) or {}
        sc[k] = np.array([dd.get(s) if dd.get(s) is not None else np.nan for s in cands], float)
        rec[k] = rr(np.nan_to_num(sc[k], nan=-1e9)); rec[f"{k}_finite"] = float(np.isfinite(sc[k]).mean())
    if {"fp", "gl"} <= sc.keys(): rec["fp+gl"] = rr(z(sc["fp"]) + z(sc["gl"])); rec["fp+2gl"] = rr(z(sc["fp"]) + 2 * z(sc["gl"]))
    if {"ice", "gl"} <= sc.keys(): rec["ice+gl"] = rr(z(sc["ice"]) + z(sc["gl"]))
    if {"fp", "ice", "gl"} <= sc.keys(): rec["fp+ice+gl"] = rr(z(sc["fp"]) + z(sc["ice"]) + z(sc["gl"]))
    rows[mid] = rec
df = pd.DataFrame(rows).T.join(mols[["lib", "truth_in_retrieval_window", "n_window_same_formula", "instruments"]], how="left")
rules = [c for c in ("random", "fp", "ice", "gl", "fp+gl", "fp+2gl", "ice+gl", "fp+ice+gl") if c in df.columns]
res = {"n_molecules": len(df), "median_candidates": float(df.n.median()), "rules": {}, "paired_deltas": {}}
print(f"molecules {len(df)} | median candidates {df.n.median():.0f} | truth in retrieval window {int(df.truth_in_retrieval_window.sum())} | instruments {df.instruments.value_counts().to_dict()}")


def boot_mean(v, n=20000):
    idx = rng.integers(0, len(v), (n, len(v))); return np.quantile(v[idx].mean(1), [.025, .975]).tolist()


for rule in rules:
    v = df[rule].values.astype(float); r = {"mrr25": float(v.mean()), "ci95": boot_mean(v), "top1": float((v == 1).mean()), "hit25": float((v > 0).mean())}
    for flag in (True, False):
        sub = df[df.truth_in_retrieval_window == flag][rule].values.astype(float)
        if len(sub): r[f"mrr25_in_window={flag}"] = float(sub.mean()); r[f"n_in_window={flag}"] = int(len(sub))
    if rule.endswith("_finite"): continue
    if rule == "random":
        r["top1"] = float(df["random_top1"].astype(float).mean()); r["hit25"] = float(df["random_hit25"].astype(float).mean())
    res["rules"][rule] = r
    fin = f" finite {df[rule.split('+')[0] + '_finite'].mean():.3f}" if f"{rule}_finite" in df.columns else ""
    print(f"  {rule:10s} MRR {r['mrr25']:.4f} CI [{r['ci95'][0]:.3f},{r['ci95'][1]:.3f}] top1 {r['top1']:.3f} hit25 {r['hit25']:.3f}" +
          "".join(f" | window={flag}: {r.get(f'mrr25_in_window={flag}', float('nan')):.3f} (n={r.get(f'n_in_window={flag}', 0)})" for flag in (True, False)) + fin)
for a_, b_ in (("fp+gl", "fp"), ("fp+gl", "gl"), ("fp+ice+gl", "fp+gl"), ("fp+2gl", "fp+gl"), ("ice+gl", "gl")):
    if a_ in df.columns and b_ in df.columns:
        d = df[a_].values.astype(float) - df[b_].values.astype(float)
        res["paired_deltas"][f"{a_} - {b_}"] = {"delta": float(d.mean()), "ci95": boot_mean(d)}
        print(f"  Δ {a_} − {b_}: {d.mean():+.4f} CI [{boot_mean(d)[0]:+.4f}, {boot_mean(d)[1]:+.4f}]")
json.dump(res, open(a.out, "w"), indent=1); df.to_csv(a.out.replace(".json", "_per_molecule.csv")); print("saved", a.out)
