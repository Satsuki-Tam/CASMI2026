"""056 development summary (056_prereg_ranker_weight.md + 049b amendment): rank_v8w / rank_v8n vs rank_v4b (r047 base), registered main.
Primary: C2 C/D/E/F equal weights per block (f1dev, f2dev), blocks equal; tau +0.005. Main protection (eps 0.01, three states):
panel C1 (full_eval tables, seen regime) and the primary aggregate. Stress: f1/f2 C1 C/E/F, G C1/C2, dev2 (p2dev)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
def load(m, tag):
    a = pd.read_csv(os.path.join(HERE, f"diag/r047_rank_v4b_{tag}.csv")); b = pd.read_csv(os.path.join(HERE, f"diag/r056_{m}_{tag}.csv"))
    x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_a", "_b")); assert len(x) == len(a) == len(b), (m, tag, len(x), len(a), len(b)); x["d"] = x.main_b - x.main_a; return x
def stat(frames):
    pts, boots = [], []
    for df, strata in frames:
        gs = [df[df.set == s].d.values for s in strata] if strata else [df.d.values]
        gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs])); boots.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(boots), axis=0), [2.5, 97.5]), pts
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo > -e else "undetermined")
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
L = ["# 056 development (ranker weight controls), registered reading", "", "| model | primary NP C2 (f1,f2) [95%] | blocks | panel C1 [95%] (state) | dev2 NP C2 | stress: f1/f2 C1 C/E/F, G C1, G C2 |", "|---|---|---|---|---|---|"]
for m in ("rank_v8w", "rank_v8n"):
    try: X = {t: load(m, t) for t in ("f1dev", "f2dev", "p2dev", "panel")}
    except FileNotFoundError as e: L.append(f"| {m} | missing {e} |"); continue
    p, ci, bl = stat([(X[t][X[t].view == "c2"], NP) for t in ("f1dev", "f2dev")])
    pc, cic, _ = stat([(X["panel"][X["panel"].view == "c1"], None)])
    d2, _, _ = stat([(X["p2dev"][X["p2dev"].view == "c2"], NP)])
    c1s = [f"{X[t][(X[t].view == 'c1') & (X[t].set == s)].d.mean():+.4f}" for t in ("f1dev", "f2dev") for s in ("C_np_crosslib", "E_np_negonly", "F_np_uncovered")]
    g1 = np.mean([X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")].d.mean() for t in ("f1dev", "f2dev")]); g2 = np.mean([X[t][(X[t].view == "c2") & (X[t].set == "G_tims_crosslib")].d.mean() for t in ("f1dev", "f2dev")])
    L.append(f"| {m} | {p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}] | {' / '.join(f'{b:+.4f}' for b in bl)} | {pc:+.4f} [{cic[0]:+.4f}, {cic[1]:+.4f}] ({st(*cic)}) | {d2:+.4f} | {' '.join(c1s)} / {g1:+.4f} / {g2:+.4f} |")
open(os.path.join(HERE, "diag/r056_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
