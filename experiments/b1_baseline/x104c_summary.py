"""104 confirmation reading (104_prereg_t1E.md section 4), written before the development result was read; run ONCE, only if the development gate passed.
Inputs: diag/c104_np096c.csv (np096_conf093: NP_H 200 / NP_N 200, C2), diag/c104_np102d.csv (np102_d0conf: D_np_single 286, C2), diag/c104_c1cost.csv
(c1cost098, C1 view of its usable molecules). d = t1E_rank_e1r_0.5 - main (v8w7a), strict.
Primary = H/4 + N/4 + D/2 (A = np096c NP_H and NP_N, each 1/4; B_D = np102d D, 1/2; not a pooled row mean). Gate: primary >= +0.005 and lower > 0; A and B_D lower >= -0.01;
c1cost C1 lower >= -0.01. Checks first (stop on failure): rows complete vs the selection CSV / c1_usable, values finite in [0, 1], t1E = main where the
truth is not in the E subset, main rank-1 never lost, t1E = main where E is empty."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12; V = "t1E_rank_e1r_0.5"
SRC = {"np096c": ("np096_conf093/p2_molecules.csv", "run_np096_f0conf"), "np102d": ("np102_d0conf/p2_molecules.csv", "run_np102_d0conf"), "c1cost": ("c1cost098/p2_molecules.csv", "run_c1cost098")}
SETS = {"np096c": ["NP_H", "NP_N"], "np102d": ["D_np_single"], "c1cost": ["E_np_negonly"]}


def stop(m): sys.exit(f"STOP (104 confirmation check): {m}")


D = {}
for t, (csv, run) in SRC.items():
    x = pd.read_csv(os.path.join(HERE, f"diag/c104_{t}.csv")); x["molecule"] = x.molecule.astype(str)
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ev = ev[ev.set.isin(SETS[t])]
    exp = set()
    for s, g in ev.groupby("set"):
        M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        for m in g.molecule:
            if m not in M.index: stop(f"{t} {s} {m}: no ledger row")
            exp.add((s, "c2", m))
            if bool(M.loc[m, "c1_usable"]): exp.add((s, "c1", m))
    got = list(zip(x.set, x.view, x.molecule))
    if len(got) != len(set(got)) or set(got) != exp: stop(f"{t}: rows missing {len(exp - set(got))} extra {len(set(got) - exp)} dup {len(got) - len(set(got))}")
    for c in ("main", V):
        v = x[c].values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{t}: {c} not finite in [0, 1]")
    er = x.e_reach.astype(str).isin(["True", "1", "1.0"])
    if int(((x[V] - x.main).abs() > TOL)[~er].sum()) or int(((x.main == 1) != (x[V] == 1)).sum()) or int(((x[V] - x.main).abs() > TOL)[x.nE.fillna(0) == 0].sum()):
        stop(f"{t}: t1E structural check failed")
    D[t] = x


def boot(cells, seed):
    rng = np.random.default_rng(seed); arrs = []
    for t, s, view in cells:
        r = D[t][(D[t].set == s) & (D[t].view == view)]
        if not len(r): stop(f"empty cell {t} {s} {view}")
        arrs.append((r[V] - r.main).values.astype(float))
    pt = float(np.mean([a.mean() for a in arrs]))
    return pt, np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
pa, ba = boot([("np096c", "NP_H", "c2"), ("np096c", "NP_N", "c2")], 104); pb, bb = boot([("np102d", "D_np_single", "c2")], 105)
p, bs = 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb
c1 = D["c1cost"][D["c1cost"].view == "c1"]
pc, bc = boot([("c1cost", "E_np_negonly", "c1")], 106) if len(c1) else (float("nan"), np.array([np.nan]))
gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and len(c1) > 0 and bool(np.isfinite(bc).all()) and ci(bc)[0] >= -0.01   # Codex 104 (2): C1 usable 0 / missing / undetermined = not passed
L = ["# 104 confirmation (t1E_rank_e1r_0.5 - v8w7a)", "", f"- **primary 1/2 A + 1/2 B_D: {fmt(p, bs)}**", f"- A np096_conf093 C2 (H/N): {fmt(pa, ba)}", f"- B_D np102_d0conf C2 (D 286): {fmt(pb, bb)}",
     f"- C1 cost c1cost098 (E, usable {len(c1)}): {fmt(pc, bc) if len(c1) else 'n/a'}", f"- **gate: {'PASS' if gate else 'NO'}**"]
open(os.path.join(HERE, "diag/x104c_summary.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
