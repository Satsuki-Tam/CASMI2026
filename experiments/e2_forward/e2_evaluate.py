"""E2 evaluation: fuse forward-model scores (ICEBERG and/or GLACIER) with the fold-safe fingerprint ranking of
same-formula PubChem candidates on the natural-product panel, for several rescoring windows and weights.

Usage: python -I -X utf8 e2_evaluate.py <e2_dir> <out_json> [--ice ice_out.json] [--gl gl_out.json] [--n N_MAX]

Ranking protocol per molecule (honest: fold0_full never saw the panel):
  base order   : fold0_full descending (optionally + w_doc * doc as a second base)
  window N     : the top-N of the base order are rescored by fused = z(base) + lam * z(forward), z within the window
                 (candidates with no forward score get z 0), candidates beyond N keep their base order below.
  metric       : MRR@25 / top-1 / hit@25 of the truth over the 246 molecules with a truth among same-formula
                 candidates (molecules without covered spectra keep the base order); bootstrap 95% CI of the delta
                 vs. the base order, resampling molecules.
"""
import argparse, json, math, os
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("e2_dir"); ap.add_argument("out_json")
ap.add_argument("--ice", default=None); ap.add_argument("--gl", default=None)
ap.add_argument("--n", type=int, default=200)
a = ap.parse_args()
rng = np.random.default_rng(0)

cand = pd.read_parquet(os.path.join(a.e2_dir, f"candidates_top{a.n}.parquet"))
fw = {}
for name, path in (("ice", a.ice), ("gl", a.gl)):
    if path and os.path.exists(path):
        d = json.load(open(path))
        fw[name] = {(mid, smi): v for mid, dd in d.items() for smi, v in (dd or {}).items() if v is not None and math.isfinite(v)}
        print(f"{name}: {len(fw[name]):,} finite scores over {len(d)} molecules")
for name in fw:
    cand[name] = [fw[name].get((m, s), np.nan) for m, s in zip(cand.molecule, cand.smiles)]
print("candidates", cand.shape, "| molecules", cand.molecule.nunique(), "| truths inside top-N", int(cand.is_truth.sum()))


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x)
    if ok.sum() < 2: return np.zeros_like(x)
    mu, sd = x[ok].mean(), x[ok].std(ddof=1)
    out = np.zeros_like(x)
    if sd > 0: out[ok] = (x[ok] - mu) / sd
    return out


def rr(is_truth_sorted, k=25):
    idx = np.flatnonzero(is_truth_sorted[:k])
    return 1.0 / (idx[0] + 1) if len(idx) else 0.0


truth_ranks = pd.read_csv(os.path.join(a.e2_dir, "truth_ranks.csv"), index_col=0)
mols = sorted(cand.molecule.unique())
groups = {m: g.sort_values("rank_fold0").reset_index(drop=True) for m, g in cand.groupby("molecule")}


def evaluate(base_col, window, lams, fw_names, w_doc=0.0):
    """returns per-molecule reciprocal ranks (len = len(mols))"""
    out = []
    for m in mols:
        g = groups[m]
        base = z(g[base_col].values) + w_doc * g.doc.values if w_doc else g[base_col].values.astype(float)
        order = np.argsort(-base, kind="stable")
        g = g.iloc[order].reset_index(drop=True)
        base = base[order]
        n = min(window, len(g))
        if n >= 2 and fw_names:
            fused = z(base[:n])
            for name, lam in zip(fw_names, lams):
                fused = fused + lam * z(g[name].values[:n])
            o = np.argsort(-fused, kind="stable")
            is_t = np.concatenate([g.is_truth.values[:n][o], g.is_truth.values[n:]])
        else:
            is_t = g.is_truth.values
        # candidates beyond N_MAX (not in file) can only lower nothing: truth outside top-N_MAX counts as 0 (rank > N_MAX >= 25)
        out.append(rr(is_t))
    return np.array(out)


def boot(a_, b_, n=4000):
    d = a_ - b_
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return float(d.mean()), [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]


res = {"n_molecules": len(mols), "forward_models": list(fw)}
configs = []
for w_doc in (0.0, 0.25):
    base = evaluate("fold0_full", 0, [], [], w_doc)
    tag = "fold0" if w_doc == 0 else f"fold0+{w_doc}doc"
    configs.append((f"{tag} | base", base, base))
    for window in (40, 100, 200):
        for names in ([n] for n in fw) if len(fw) == 1 else ([[n] for n in fw] + [list(fw)]):
            for lam in (0.5, 1.0, 2.0):
                v = evaluate("fold0_full", window, [lam] * len(names), names, w_doc)
                configs.append((f"{tag} | top{window} +{'+'.join(names)} lam={lam}", v, base))
            v = evaluate("fold0_full", window, [100.0] * len(names), names, w_doc)
            configs.append((f"{tag} | top{window} {'+'.join(names)} only", v, base))
res["configs"] = []
for name, v, base in configs:
    d, ci = boot(v, base)
    row = dict(name=name, mrr25=float(v.mean()), top1=float((v == 1).mean()), hit25=float((v > 0).mean()), delta=d, ci95=ci)
    res["configs"].append(row)
    print(f"{name:48s} MRR {row['mrr25']:.4f} top1 {row['top1']:.3f} hit25 {row['hit25']:.3f} delta {d:+.4f} CI [{ci[0]:+.4f},{ci[1]:+.4f}]")
json.dump(res, open(a.out_json, "w"), indent=1)
print("saved", a.out_json)
