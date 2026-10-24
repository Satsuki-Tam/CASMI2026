"""E1: replay the natural-product panel benchmark (250 enveda-np-examples molecules) to quantify
(a) ranker-only vs popularity-prior variants per scenario, (b) how often the wrong winner is a same-formula isomer,
(c) honest fingerprint-model isomer discrimination (fold-safe model that never saw the panel vs A+B that did),
(d) how much a documentation prior contributes among same-formula candidates.
Usage: python -I -X utf8 e1_panel_replay.py <panel_benchmark_dir> <out_json>
"""
import json, sys, time
import numpy as np, pandas as pd

D, OUT = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(0)
t0 = time.time()

def rr_from_sorted(is_truth_sorted, k=25):
    idx = np.flatnonzero(is_truth_sorted[:k])
    return 1.0 / (idx[0] + 1) if len(idx) else 0.0

def boot_delta(a, b, n=4000):
    d = np.asarray(a) - np.asarray(b)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return float(d.mean()), [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]

res = {}
# ---------------------------------------------------------------- (a)+(b) main list replay
mc = pd.read_parquet(f"{D}/main_candidates.parquet")
mc["molecule"] = mc["molecule"].astype(str); mc["scenario"] = mc["scenario"].astype(str)
print("main_candidates", mc.shape, "scenarios", mc.scenario.unique().tolist(), "molecules", mc.molecule.nunique())
print("pool_source values", mc.pool_source.value_counts().to_dict())
res["main"] = {}
for sc, g_sc in mc.groupby("scenario"):
    rows = {}
    per_mol = {}
    mols = sorted(g_sc.molecule.unique())
    cov = 0; same_formula_wrong = 0; wrong_total = 0; truth_rank = []
    for m in mols:
        g = g_sc[g_sc.molecule == m].sort_values("rank")
        g = g.drop_duplicates("candidate_key")
        has_truth = bool(g.is_truth.any()); cov += has_truth
        sc_rank = g.is_truth.values
        base_rr = rr_from_sorted(sc_rank)
        variants = {"ranker_only": base_rr}
        # popularity re-order of top60 (generated candidates = pool_source<0 keep position, like the notebook)
        top = g.head(60).copy()
        s = top.ranker_score.values.astype(float); z = (s - s.mean()) / (s.std() + 1e-9)
        isg = top.pool_row.values < 0
        for mu in (0.05, 0.15, 0.4, 1.0):
            f = z + mu * np.where(isg, 0.0, np.nan_to_num(top.popularity.values.astype(float)))
            o = np.empty(len(top), int); pi = np.where(~isg)[0]; o[isg] = np.where(isg)[0]; o[~isg] = pi[np.argsort(-f[pi], kind="stable")]
            variants[f"pop_mu{mu}"] = rr_from_sorted(top.is_truth.values[o])
        per_mol[m] = variants
        if has_truth:
            r = int(np.flatnonzero(sc_rank)[0]) + 1; truth_rank.append(r)
            if r > 1:
                wrong_total += 1
                tf = g[g.is_truth].formula.iloc[0]
                if g.formula.iloc[0] == tf: same_formula_wrong += 1
    names = list(next(iter(per_mol.values())).keys())
    tab = {n: np.array([per_mol[m][n] for m in mols]) for n in names}
    out = {"n_molecules": len(mols), "truth_in_candidates": cov / len(mols),
           "truth_rank_median": float(np.median(truth_rank)) if truth_rank else None,
           "truth_not_rank1": wrong_total, "wrong_winner_same_formula": same_formula_wrong,
           "variants": {}}
    for n in names:
        d, ci = boot_delta(tab[n], tab["ranker_only"])
        out["variants"][n] = {"mrr25": float(tab[n].mean()), "top1": float((tab[n] == 1).mean()), "hit25": float((tab[n] > 0).mean()),
                              "delta_vs_ranker": d, "ci95": ci}
    res["main"][sc] = out
    print(f"\n== scenario {sc}: truth in candidates {out['truth_in_candidates']:.3f} | truth not rank1: {wrong_total}, of which same-formula winner: {same_formula_wrong}")
    for n, v in out["variants"].items():
        print(f"   {n:14s} MRR {v['mrr25']:.4f} top1 {v['top1']:.3f} hit25 {v['hit25']:.3f} delta {v['delta_vs_ranker']:+.4f} CI {v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}")

# ---------------------------------------------------------------- (c)+(d) PubChem same-formula isomer discrimination
pc = pd.read_parquet(f"{D}/pubchem_candidates.parquet", columns=["molecule", "tier_row", "fpnet_score", "partial_score", "connectivity", "scorer_key", "is_truth", "in_pool", "log_substances", "log_pubmed"])
fs = pd.read_parquet(f"{D}/panel_fpnet_scores.parquet", columns=["molecule", "tier_row", "ab_full", "fold0_full"])
sf = pd.read_parquet(f"{D}/panel_same_formula.parquet")
pc["molecule"] = pc["molecule"].astype(str); fs["molecule"] = fs["molecule"].astype(str)
df = pc.merge(fs, on=["molecule", "tier_row"], how="left").merge(sf, on=["molecule", "tier_row"], how="left")
df["ident"] = np.where(df.scorer_key.fillna("") != "", df.scorer_key, df.connectivity)
df["doc"] = df.log_substances.fillna(0).astype(float) + df.log_pubmed.fillna(0).astype(float)
print("\npubchem candidates", df.shape, "| same_formula rows", int(df.same_formula.sum()), "| truth rows", int(df.is_truth.sum()))
res["pubchem_same_formula"] = {}
scores = {"ab_full (saw panel)": "ab_full", "fold0_full (never saw panel)": "fold0_full", "fpnet_score (notebook)": "fpnet_score"}
mols = sorted(df.molecule.unique())
def eval_rule(colfun, restrict_same_formula=True):
    out = []
    n_truth_present = 0; n_cand = []
    for m in mols:
        g = df[df.molecule == m]
        if restrict_same_formula: g = g[g.same_formula == True]
        g = g[np.isfinite(g[colfun[0]].astype(float))] if isinstance(colfun, tuple) else g
        sc = colfun[1](g) if isinstance(colfun, tuple) else colfun(g)
        g = g.assign(_s=sc).sort_values("_s", ascending=False)
        g = g[~g.ident.duplicated()]
        n_cand.append(len(g))
        if g.is_truth.any(): n_truth_present += 1
        out.append(rr_from_sorted(g.is_truth.values))
    return np.array(out), n_truth_present, n_cand
rules = {}
for name, col in scores.items():
    rules[name] = (col, lambda g, c=col: g[c].astype(float).values)
def zdoc(g, c, w):
    s = g[c].astype(float).values; z = (s - np.nanmean(s)) / (np.nanstd(s) + 1e-9)
    return z + w * g.doc.values
for w in (0.1, 0.25, 0.5):
    rules[f"fold0_full + {w}*doc"] = ("fold0_full", lambda g, w=w: zdoc(g, "fold0_full", w))
    rules[f"ab_full + {w}*doc"] = ("ab_full", lambda g, w=w: zdoc(g, "ab_full", w))
rules["doc only"] = ("fold0_full", lambda g: g.doc.values + 1e-6 * rng.random(len(g)))
rules["random"] = ("fold0_full", lambda g: rng.random(len(g)))
base = None
for name, rule in rules.items():
    v, ntp, ncand = eval_rule(rule)
    if base is None: base = v
    d, ci = boot_delta(v, base)
    res["pubchem_same_formula"][name] = {"mrr25": float(v.mean()), "top1": float((v == 1).mean()), "hit25": float((v > 0).mean()),
                                         "truth_present": ntp, "median_candidates": float(np.median(ncand)), "delta_vs_first": d, "ci95": ci}
    print(f"   {name:32s} MRR {v.mean():.4f} top1 {(v==1).mean():.3f} hit25 {(v>0).mean():.3f} | truth present {ntp}/250 | median same-formula identities {np.median(ncand):.0f}")
json.dump(res, open(OUT, "w"), indent=1)
print(f"\nsaved {OUT} in {time.time()-t0:.0f}s")
