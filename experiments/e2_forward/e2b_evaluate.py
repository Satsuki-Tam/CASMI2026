"""E2b evaluation: forward-model-only isomer discrimination on uncontaminated molecules.

Usage: python -I -X utf8 e2b_evaluate.py <in.json> <molecules.csv> <out_json> [--ice ice_out.json] [--gl gl_out.json]

Each molecule's candidate list has the truth first followed by same-formula PubChem isomers (random, capped).
Ranking rules: random (expected RR analytically via 1000 shuffles), ice only, gl only, ice+gl (z-sum).
Reports MRR@25 / top-1 / hit@25 with molecule-level bootstrap 95% CIs, and stratifies by truth_in_pubchem.
"""
import argparse, json, math
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("mols"); ap.add_argument("out")
ap.add_argument("--ice", default=None); ap.add_argument("--gl", default=None)
a = ap.parse_args()
rng = np.random.default_rng(0)
items = json.load(open(a.inp))
mols = pd.read_csv(a.mols).set_index("molecule")
fw = {}
for name, path in (("ice", a.ice), ("gl", a.gl)):
    if path:
        d = json.load(open(path)); fw[name] = d
        fin = sum(1 for dd in d.values() for v in (dd or {}).values() if v is not None and math.isfinite(v))
        print(f"{name}: {fin:,} finite scores over {len(d)} molecules")


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x)
    out = np.zeros_like(x)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0:
        out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    return out


def rr_of_truth(scores):
    """truth is index 0; rank = 1 + number of candidates strictly above it (ties broken against the truth, i.e. worst case)."""
    s = np.asarray(scores, float); t = s[0]
    if not np.isfinite(t): return 0.0
    rank = 1 + int(np.sum(s[1:] >= t))
    return 1.0 / rank if rank <= 25 else 0.0


def boot(v, n=4000):
    bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]


rows = {}
for it in items:
    mid, cands = it["mid"], it["cands"]
    n = len(cands)
    rec = {"n": n, "random": float(np.mean([1.0 / r if r <= 25 else 0.0 for r in rng.integers(1, n + 1, 1000)]))}
    scores = {}
    for name, d in fw.items():
        dd = d.get(mid, {}) or {}
        scores[name] = np.array([dd.get(s) if dd.get(s) is not None else np.nan for s in cands], float)
        rec[name] = rr_of_truth(np.nan_to_num(scores[name], nan=-1e9))
    if len(scores) == 2:
        rec["ice+gl"] = rr_of_truth(z(scores["ice"]) + z(scores["gl"]))
    rows[mid] = rec
df = pd.DataFrame(rows).T
df = df.join(mols[["lib", "truth_in_pubchem", "n_window_same_formula"]], how="left")
res = {"n_molecules": len(df), "median_candidates": float(df.n.median()), "rules": {}}
print(f"molecules {len(df)} | median candidates {df.n.median():.0f} | truth in PubChem {int(df.truth_in_pubchem.sum())}")
for rule in [c for c in ("random", "ice", "gl", "ice+gl") if c in df.columns]:
    v = df[rule].values.astype(float)
    r = {"mrr25": float(v.mean()), "ci95": boot(v), "top1": float((v == 1).mean()), "hit25": float((v > 0).mean())}
    for flag in (True, False):
        sub = df[df.truth_in_pubchem == flag][rule].values.astype(float)
        if len(sub): r[f"mrr25_truth_in_pubchem={flag}"] = float(sub.mean()); r[f"n_truth_in_pubchem={flag}"] = int(len(sub))
    res["rules"][rule] = r
    print(f"  {rule:8s} MRR {r['mrr25']:.4f} CI [{r['ci95'][0]:.3f},{r['ci95'][1]:.3f}] top1 {r['top1']:.3f} hit25 {r['hit25']:.3f}"
          + "".join(f" | inPC={flag}: {r.get(f'mrr25_truth_in_pubchem={flag}', float('nan')):.3f} (n={r.get(f'n_truth_in_pubchem={flag}', 0)})" for flag in (True, False)))
json.dump(res, open(a.out, "w"), indent=1)
df.to_csv(a.out.replace(".json", "_per_molecule.csv"))
print("saved", a.out)
