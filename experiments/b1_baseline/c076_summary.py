"""076 confirmation reading (076_prereg_ea.md): ea0.5w1 - main (0.379 main, rank_v4b) read ONCE.
PASS = 073 NP C2 (NP_H and NP_N equal, fold 3 / 4 blocks equal, all molecules incl. unreached = 0) point >= +0.005 AND lower > -0.01
       AND f3b/f4b G_tims_crosslib C1 (2 blocks equal) lower > -0.01. Reported: per block / stratum, improved / worsened counts, reach-conditional,
       073 NP_H C1 (stress)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000; V = "ea0.5w1"
def load(p):
    d = pd.read_csv(os.path.join(HERE, p)); d["molecule"] = d.molecule.astype(str); d["d"] = d[V] - d.main; assert not d[[V, "main"]].isna().any().any(); return d
C = {k: load(f"diag/c076_np073f{k}conf.csv") for k in (3, 4)}; G = {k: load(f"diag/k076_tpf{k}b_G.csv") for k in (3, 4)}
def stat(frames):
    pts, bts = [], []
    for df, strata in frames:
        gs = [df[df.set == s].d.values for s in strata] if strata else [df.d.values]; gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs])); bts.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(bts), axis=0), [2.5, 97.5]), pts
out = ["# 076 confirmation (073 opened once; ea0.5w1 - 0.379 main)", ""]
for k, d in C.items(): out.append(f"- 073 fold {k}: rows {len(d)}, molecules {d.molecule.nunique()}, views {d.view.value_counts().to_dict()}")
p, ci, bl = stat([(C[k][C[k].view == "c2"], ["NP_H", "NP_N"]) for k in (3, 4)])
out.append(f"- **073 NP C2 (H, N equal; blocks equal): {p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]** | blocks f3 / f4 {bl[0]:+.4f} / {bl[1]:+.4f}")
for k in (3, 4):
    for s in ("NP_H", "NP_N", "NP_X"):
        for v in ("c2", "c1"):
            g = C[k][(C[k].set == s) & (C[k].view == v)]
            if len(g): out.append(f"    f{k} {s} {v}: n {len(g)} main {g.main.mean():.4f} -> {g[V].mean():.4f} ({g.d.mean():+.4f}; up {int((g.d > 0).sum())} / down {int((g.d < 0).sum())})")
pr = [C[k][(C[k].view == "c2") & C[k].pos] for k in (3, 4)]
pp, cip, _ = stat([(x, ["NP_H", "NP_N"]) for x in pr])
out.append(f"- reach-conditional (truth in the view shortlist) NP C2: {pp:+.4f} [{cip[0]:+.4f}, {cip[1]:+.4f}]")
gc, cig, gbl = stat([(G[k][G[k].view == "c1"], None) for k in (3, 4)])
out.append(f"- **f3b/f4b G C1 (2 blocks equal): {gc:+.4f} [{cig[0]:+.4f}, {cig[1]:+.4f}]** | blocks {gbl[0]:+.4f} / {gbl[1]:+.4f} | n {[int((G[k].view == 'c1').sum()) for k in (3, 4)]} | "
           f"worsened {[int(((G[k].view == 'c1') & (G[k].d < 0)).sum()) for k in (3, 4)]} improved {[int(((G[k].view == 'c1') & (G[k].d > 0)).sum()) for k in (3, 4)]}")
g2 = np.mean([G[k][G[k].view == "c2"].d.mean() for k in (3, 4)]); out.append(f"- f3b/f4b G C2 (C2 is non-worsening by construction): {g2:+.4f}")
h1, cih1, _ = stat([(C[k][(C[k].view == "c1") & (C[k].set == "NP_H")], None) for k in (3, 4)])
out.append(f"- stress: 073 NP_H C1 (non-timsTOF, new identities): {h1:+.4f} [{cih1[0]:+.4f}, {cih1[1]:+.4f}]")
ok = (p >= 0.005) and (ci[0] > -0.01) and (cig[0] > -0.01)
out.append(f"- REGISTERED VERDICT: {'PASS' if ok else 'FAIL'} (073 point >= +0.005: {p >= 0.005}; 073 lower > -0.01: {ci[0] > -0.01}; G C1 lower > -0.01: {cig[0] > -0.01})")
open(os.path.join(HERE, "diag/c076_summary.md"), "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
