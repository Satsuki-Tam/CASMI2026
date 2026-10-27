"""095 reading (095_prereg_bspec.md): diag/r095_<tag>.csv (gen_eval2fd --v7f --bmodel rank_b095, base rank_v7a): main (v7f) vs bpp (B-position-preserving reorder).
Primary: 053 dev NP C2 (NP_H / NP_N equal within a fold, folds equal), strict, bpp - main. Checks: rows whose truth is not B and every C1 row must have
d == 0 exactly. Gate: primary >= +0.005 and lower > 0, f1/f2 NP C2 (C-F) non-inferior (L >= -0.01), checks pass. Also B-in-rank MRR (truth-B rows)."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
TAGS = ["np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel", "p2dev"]
D = {}
for t in TAGS:
    p = os.path.join(HERE, f"diag/r095_{t}.csv")
    if os.path.exists(p):
        x = pd.read_csv(p); x["d"] = x.bpp - x.main
        x["truth_B"] = x.truth_B.astype(str).isin(["True", "1", "1.0"])   # empty-candidate rows store 0.0 -> object dtype; parse explicitly
        D[t] = x
miss = [t for t in TAGS if t not in D]
if any(t in miss for t in ("np053f1dev", "np053f2dev", "f1dev", "f2dev")): sys.exit(f"missing: {miss}")
def stat(frames):
    pts, bts = [], []
    for df, strata in frames:
        gs = [df[df.set == s].d.values for s in strata] if strata else [df.d.values]
        gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs])); bts.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(bts), axis=0), [2.5, 97.5])
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
c2 = lambda t: D[t][D[t].view == "c2"]
prim = stat([(c2("np053f1dev"), ["NP_H", "NP_N"]), (c2("np053f2dev"), ["NP_H", "NP_N"])])
npf = stat([(c2(t), ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")])
A = pd.concat([D[t].assign(tag=t) for t in D])
chk_nonB = float(np.abs(A[~A.truth_B.astype(bool)].d).max()); chk_c1 = float(np.abs(A[A.view == "c1"].d).max())
gate = prim[0] >= 0.005 and prim[1][0] > 0 and npf[1][0] >= -0.01 and chk_nonB == 0 and chk_c1 == 0
def rr(r): r = np.asarray(r, float); return np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
L = ["# 095 reading: B-group specialist, B-position-preserving reorder (v7f base)", "", f"missing (stress/report only): {miss}",
     f"- **Primary 053 NP C2 (H,N) bpp - main: {fmt(*prim)}**", f"- f1/f2 NP C2 (C-F): {fmt(*npf)}",
     f"- checks: max |d| on rows whose truth is not B = {chk_nonB:.6f}; on C1 rows = {chk_c1:.6f}",
     f"- **GATE to a new confirmation set: {'GO' if gate else 'NO'}**", "", "| table | view | truth-B rows | main | bpp | d (truth-B rows) | B-in-rank MRR main -> spec |", "|---|---|---:|---:|---:|---:|---|"]
for t in D:
    for v in ("c2", "c1"):
        x = D[t][(D[t].view == v)]; b = x[x.truth_B.astype(bool)]
        if not len(x): continue
        L.append(f"| {t} | {v} | {len(b)} | {x.main.mean():.4f} | {x.bpp.mean():.4f} | {b.d.mean() if len(b) else 0:+.4f} | {rr(b.rB_main).mean() if len(b) else 0:.4f} -> {rr(b.rB_spec).mean() if len(b) else 0:.4f} |")
if "panel" in D: L.append(f"- panel C2: {fmt(*stat([(c2('panel'), None)]))}")
if "p2dev" in D: L.append(f"- dev2 NP C2 (stress): {fmt(*stat([(c2('p2dev'), ['C_np_crosslib', 'D_np_single', 'E_np_negonly', 'F_np_uncovered'])]))}")
open(os.path.join(HERE, "diag/x095_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
