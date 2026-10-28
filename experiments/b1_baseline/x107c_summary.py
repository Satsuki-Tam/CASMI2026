"""107 confirmation reading (107_prereg_data.md section 3), written before the development result was read; run ONCE, only if the development gate passed.
Inputs: diag/cf107/c107_<model>_<tag>.csv for model in v8w7a, cfall and tag in np096c (np096_conf093: NP_H 200 / NP_N 200), np102d (np102_d0conf:
D_np_single 286), c1cost (c1cost098: E, C1 view of its usable molecules). d = cfall main - v8w7a main (one gen_eval2fd pass, two models), strict.
Primary = H/4 + N/4 + D/2 (C2). Gate: primary >= +0.005 and lower > 0; A (H/N) and B_D (D) lower >= -0.01; c1cost C1 lower >= -0.01 with usable > 0
(usable 0 / missing / undetermined = not passed). Checks first: identical rows for both models, complete vs the selection CSV / c1_usable, finite in [0, 1]."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, "diag", "cf107"); NB = 4000
SRC = {"np096c": ("np096_conf093/p2_molecules.csv", "run_np096_f0conf", ["NP_H", "NP_N"]), "np102d": ("np102_d0conf/p2_molecules.csv", "run_np102_d0conf", ["D_np_single"]),
       "c1cost": ("c1cost098/p2_molecules.csv", "run_c1cost098", ["E_np_negonly"])}


def stop(m): sys.exit(f"STOP (107 confirmation check): {m}")


D = {}
for t, (csv, run, sets) in SRC.items():
    X = {}
    for m in ("v8w7a", "cfall"):
        p = os.path.join(C, f"c107_{m}_{t}.csv")
        if not os.path.exists(p): stop(f"missing {p}")
        x = pd.read_csv(p); x["molecule"] = x.molecule.astype(str); X[m] = x.set_index(["set", "view", "molecule"]).main
    if set(X["v8w7a"].index) != set(X["cfall"].index) or X["v8w7a"].index.duplicated().any(): stop(f"{t}: row sets differ")
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ev = ev[ev.set.isin(sets)]; exp = set()
    for s, g in ev.groupby("set"):
        M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        for mm in g.molecule:
            if mm not in M.index: stop(f"{t} {s} {mm}: no ledger row")
            exp.add((s, "c2", mm))
            if bool(M.loc[mm, "c1_usable"]): exp.add((s, "c1", mm))
    if set(X["v8w7a"].index) != exp: stop(f"{t}: rows vs expected differ")
    F = pd.DataFrame(X).reset_index(); v = F[["v8w7a", "cfall"]].values
    if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{t}: values")
    F["d"] = F.cfall - F.v8w7a; D[t] = F


def boot(cells, seed):
    rng = np.random.default_rng(seed); arrs = []
    for t, s, view in cells:
        r = D[t][(D[t].set == s) & (D[t].view == view)]
        if not len(r): stop(f"empty cell {t} {s} {view}")
        arrs.append(r.d.values.astype(float))
    pt = float(np.mean([a.mean() for a in arrs]))
    return pt, np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
pa, ba = boot([("np096c", "NP_H", "c2"), ("np096c", "NP_N", "c2")], 1071); pb, bb = boot([("np102d", "D_np_single", "c2")], 1072)
p, bs = 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb
c1 = D["c1cost"][D["c1cost"].view == "c1"]
pc, bc = boot([("c1cost", "E_np_negonly", "c1")], 1073) if len(c1) else (float("nan"), np.array([np.nan]))
gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and len(c1) > 0 and bool(np.isfinite(bc).all()) and ci(bc)[0] >= -0.01
L = ["# 107 confirmation (cfall - v8w7a)", "", f"- **primary H/4 + N/4 + D/2: {fmt(p, bs)}**", f"- A np096_conf093 C2 (H/N): {fmt(pa, ba)}", f"- B_D np102_d0conf C2 (D 286): {fmt(pb, bb)}",
     f"- C1 cost c1cost098 (E, usable {len(c1)}): {fmt(pc, bc) if len(c1) else 'n/a'}", f"- **gate: {'PASS' if gate else 'NO'}**"]
open(os.path.join(C, "x107c_summary.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
