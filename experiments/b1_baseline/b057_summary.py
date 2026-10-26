"""057 development summary (registered 057_prereg_blend_np.md + 049b amendment): variants v<a:wg:wp> vs main.
Primary = COCONUT-listed-truth C2: 4 blocks equal weight (053 f1 dev, 053 f2 dev: NP_H/X/N equal weights; f1dev, f2dev: COCONUT-truth molecules
of C/D/E/F pooled). Main protection (eps 0.01, three states, molecule bootstrap within blocks): panel C1; non-listed-truth C2 (f1dev/f2dev, equal).
Stress: COCONUT-listed C1 (053 dev + f1/f2 dev), G C1/C2, panel C2."""
import os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
rng = np.random.default_rng(20261027); NB = 4000
pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"]); PC = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
def coco_map(ev):
    E = pd.read_csv(os.path.join(HERE, ev)); E["molecule"] = E.molecule.astype(str); return dict(zip(E.molecule, E.scorer_key.isin(PC)))
D = {}
for tag, ev in (("f1dev", "eval_set_f1/p2_molecules.csv"), ("f2dev", "eval_set_f2/p2_molecules.csv")):
    R = pd.read_csv(os.path.join(HERE, f"diag/b057_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R["coco"] = R.molecule.map(coco_map(ev)); D[tag] = R
for K in (1, 2):
    p = os.path.join(HERE, f"diag/b057_np053f{K}.csv")
    if os.path.exists(p): R = pd.read_csv(p); R["molecule"] = R.molecule.astype(str); D[f"np{K}"] = R
D["panel"] = pd.read_csv(os.path.join(HERE, "diag/b057_panel.csv"))
VAR = [c for c in D["f1dev"].columns if c[:2] in ("v1", "v2", "v3") and c != "v2:2:0.5"]
def block_stat(frames, var, weights=None):
    """frames: list of (df, stratum column or None); each block = mean over its strata (equal) of (var - main); returns point and bootstrap CI over molecules."""
    pts, boots = [], []
    for df, strat in frames:
        groups = [g for _, g in df.groupby(strat)] if strat else [df]
        d_ = [(g[var] - g["main"]).values for g in groups]
        pts.append(np.mean([x.mean() for x in d_]))
        boots.append(np.array([np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in d_]) for _ in range(NB)]))
    w = np.ones(len(pts)) / len(pts) if weights is None else np.asarray(weights)
    return float(np.dot(w, pts)), np.percentile(np.dot(w, np.vstack(boots)), [2.5, 97.5]), pts
L = ["# 057 development (blend weights), registered reading", "", "| variant | primary COCONUT-listed C2 (4 blocks) [95%] | blocks | panel C1 [95%] | non-listed C2 [95%] | state (eps 0.01) | stress: listed C1 / G C1 / G C2 / panel C2 |", "|---|---|---|---|---|---|---|"]
for v in VAR:
    prim_frames = []
    for K in (1, 2):
        if f"np{K}" in D: prim_frames.append((D[f"np{K}"][D[f"np{K}"].view == "c2"], "set"))
    for tag in ("f1dev", "f2dev"):
        x = D[tag]; prim_frames.append((x[(x.view == "c2") & (x.set != "G_tims_crosslib") & (x.coco == True)], None))
    p, ci, blocks = block_stat(prim_frames, v)
    pc1, ci1, _ = block_stat([(D["panel"][D["panel"].view == "c1"], None)], v)
    nl, cinl, _ = block_stat([(D[t][(D[t].view == "c2") & (D[t].set != "G_tims_crosslib") & (D[t].coco == False)], None) for t in ("f1dev", "f2dev")], v)
    def state(lo, hi, eps=0.01): return "harm" if hi < -eps else ("non-inferior" if lo > -eps else "undetermined")
    st = f"panelC1 {state(*ci1)}, nonlisted {state(*cinl)}"
    lc1 = []
    for K in (1, 2):
        if f"np{K}" in D: lc1.append((D[f"np{K}"][D[f"np{K}"].view == "c1"], None))
    for t in ("f1dev", "f2dev"): lc1.append((D[t][(D[t].view == "c1") & (D[t].set != "G_tims_crosslib") & (D[t].coco == True)], None))
    s1, _, _ = block_stat(lc1, v); g1, _, _ = block_stat([(D[t][(D[t].view == "c1") & (D[t].set == "G_tims_crosslib")], None) for t in ("f1dev", "f2dev")], v)
    g2, _, _ = block_stat([(D[t][(D[t].view == "c2") & (D[t].set == "G_tims_crosslib")], None) for t in ("f1dev", "f2dev")], v)
    pc2, _, _ = block_stat([(D["panel"][D["panel"].view == "c2"], None)], v)
    L.append(f"| {v[1:]} | {p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}] | {' / '.join(f'{b:+.4f}' for b in blocks)} | {pc1:+.4f} [{ci1[0]:+.4f}, {ci1[1]:+.4f}] | {nl:+.4f} [{cinl[0]:+.4f}, {cinl[1]:+.4f}] | {st} | {s1:+.4f} / {g1:+.4f} / {g2:+.4f} / {pc2:+.4f} |")
L.append(""); L.append(f"blocks used for the primary: {[k for k in D if k.startswith('np')] + ['f1dev', 'f2dev']}")
open(os.path.join(HERE, "diag/b057_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
