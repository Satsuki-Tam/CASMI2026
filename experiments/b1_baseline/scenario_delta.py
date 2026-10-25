"""Codex 024 (draft): expected change of a list variant on a hypothetical hidden-test class mixture, from per-molecule RR of the development cells.
Cells (fixed before Public results): C1 representatives = panel C1 (timsTOF NP, identity unseen by fold-0) and G C1 (timsTOF query, references from other
instruments); C2 representatives = panel C2 (truth in COCONUT, 249/250) and dev2 C2 pooled over C/D/E/F (truth mostly PubChem-only). Class 3 contributes 0
to every variant. Scenario: p1, p2 (p3 = 1 - p1 - p2), C1 mix a (share of panel vs G), C2 mix b (share of panel-type vs dev2-type).
Expected delta = p1 * [a * d(panel C1) + (1-a) * d(G C1)] + p2 * [b * d(panel C2) + (1-b) * d(dev2 C2)], with a molecule-level bootstrap within cells.
Usage: python -X utf8 scenario_delta.py --panel DIR --p2dev DIR --variants pcd0.5 pcd1 gdN0.7w1 ... [--cand M2x] [--out md]
"""
import argparse, os
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--panel", required=True); ap.add_argument("--p2dev", required=True, nargs="+"); ap.add_argument("--variants", nargs="+", required=True)
ap.add_argument("--cand", default="M2x"); ap.add_argument("--out", default=""); ap.add_argument("--boot", type=int, default=4000); a = ap.parse_args()
rng = np.random.default_rng(20261025)
def load(dirs, s, view, out):
    for d in (dirs if isinstance(dirs, list) else [dirs]):
        p = os.path.join(d, f"pred_{s}_{view}_{a.cand}_{out}.csv")
        if os.path.exists(p): return pd.read_csv(p).set_index("molecule_id").rr
    return None
def cell(dirs, sets, view, v):
    ds = []
    for s in sets:
        b = load(dirs, s, view, "blend21"); x = load(dirs, s, view, f"blend21_{v}")
        if b is None or x is None: continue
        ds.append((x - b.loc[x.index]).values)
    return np.concatenate(ds) if ds else None
SC = [(p1, p2, a_, b_) for p1 in (0.2, 0.35, 0.5) for p2 in (0.2, 0.35) if p1 + p2 <= 1 for a_ in (1.0, 0.5, 0.0) for b_ in (1.0, 0.5, 0.0)]
md = ["| variant | cell means: panel C1 / G C1 / panel C2 / dev2 C2 (C-F) | scenarios with expected Δ > 0 (of %d) | worst scenario Δ | best scenario Δ |" % len(SC), "|---|---|---:|---:|---:|"]
detail = ["", "| variant | p1 | p2 | C1 panel share | C2 panel-type share | expected Δ [95% CI] |", "|---|---:|---:|---:|---:|---|"]
for v in a.variants:
    c = {"pC1": cell(a.panel, ["P_np250"], "c1", v), "gC1": cell(a.p2dev, ["G_tims_crosslib"], "c1", v), "pC2": cell(a.panel, ["P_np250"], "c2", v),
         "dC2": cell(a.p2dev, ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"], "c2", v)}
    if any(x is None for x in c.values()): md.append(f"| {v} | missing cells | | | |"); continue
    bm = {k: np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(a.boot)]) for k, x in c.items()}
    res = []
    for p1, p2, a_, b_ in SC:
        e = p1 * (a_ * c["pC1"].mean() + (1 - a_) * c["gC1"].mean()) + p2 * (b_ * c["pC2"].mean() + (1 - b_) * c["dC2"].mean())
        eb = p1 * (a_ * bm["pC1"] + (1 - a_) * bm["gC1"]) + p2 * (b_ * bm["pC2"] + (1 - b_) * bm["dC2"])
        res.append((p1, p2, a_, b_, e, np.percentile(eb, 2.5), np.percentile(eb, 97.5)))
        detail.append(f"| {v} | {p1} | {p2} | {a_} | {b_} | {e:+.4f} [{np.percentile(eb, 2.5):+.4f}, {np.percentile(eb, 97.5):+.4f}] |")
    es = [r[4] for r in res]
    md.append(f"| {v} | {c['pC1'].mean():+.3f} / {c['gC1'].mean():+.3f} / {c['pC2'].mean():+.3f} / {c['dC2'].mean():+.3f} | {sum(e > 0 for e in es)} | {min(es):+.4f} | {max(es):+.4f} |")
text = "\n".join(md + detail); print("\n".join(md))
if a.out: open(a.out, "w", encoding="utf-8").write(text + "\n"); print("wrote", a.out)
