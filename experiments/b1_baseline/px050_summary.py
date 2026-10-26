"""050 development summary (registered reading, 050_prereg_proxy.md): per set x arm x stratum x view, paired delta vs the same-code base."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(0)
L = ["# 050 development (proxy GLACIER), paired vs the same-code base (diag/px050_<set>_base)", "", "| set | arm | stratum | view | n | base | arm | delta [95% CI] | up / down |", "|---|---|---|---|---:|---:|---:|---|---|"]
prim = {}
for tag in ("f1dev", "f2dev", "p2dev", "panel"):
    b = pd.read_csv(os.path.join(HERE, f"diag/px050_{tag}_base.csv"))
    for arm in ("a", "n"):
        x = pd.read_csv(os.path.join(HERE, f"diag/px050_{tag}_{arm}.csv"))
        m = b.merge(x, on=["set", "view", "molecule"], suffixes=("_b", "_x"))
        assert len(m) == len(b) == len(x), (tag, arm, len(m), len(b), len(x))
        for (s, v), g in m.groupby(["set", "view"]):
            d = (g.main_x - g.main_b).values; n = len(d); bs = np.array([d[rng.integers(0, n, n)].mean() for _ in range(4000)]); lo, hi = np.percentile(bs, [2.5, 97.5])
            L.append(f"| {tag} | {arm} | {s} | {v} | {n} | {g.main_b.mean():.4f} | {g.main_x.mean():.4f} | {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] | {(d > 0).sum()} / {(d < 0).sum()} |")
            prim[(tag, arm, s, v)] = d.mean()
L.append("")
for arm, s in (("a", "F_np_uncovered"), ("n", "E_np_negonly"), ("n", "F_np_uncovered")):
    vals = [prim.get((t, arm, s, "c2")) for t in ("f1dev", "f2dev")]
    if None not in vals: L.append(f"- primary {arm} {s} C2 (fold-1/2 mean): {np.mean(vals):+.4f} (f1 {vals[0]:+.4f}, f2 {vals[1]:+.4f}); dev2 {prim.get(('p2dev', arm, s, 'c2'), float('nan')):+.4f}")
for arm in ("a", "n"):
    worst = min((prim[(t, arm, s, 'c1')], t, s) for t in ("f1dev", "f2dev") for s in ("E_np_negonly", "F_np_uncovered") if (t, arm, s, "c1") in prim)
    L.append(f"- protection {arm}: worst C1 E/F delta {worst[0]:+.4f} ({worst[1]} {worst[2]}); arm a E unchanged: {all(abs(prim.get((t, 'a', 'E_np_negonly', v), 0)) < 1e-12 for t in ('f1dev', 'f2dev', 'p2dev') for v in ('c1', 'c2'))}")
open(os.path.join(HERE, "diag/px050_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
