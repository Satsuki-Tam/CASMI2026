"""108 reading (108_prereg_c1w.md), written before any result was read; derived from x107_summary.py v2. Models: v8w7a, cfAw, cfBw, cfallw
(C1 nominal group-weight share restored to cf0's). Decision vs v8w7a with the 107 gates; mechanism = weighted CF - 107 unweighted CF (same rows)."""
"""107 reading v2 (107_prereg_data.md + section 4 after Codex 107), written before any result was read.
v2 additions: fit-roster checks (each scored row's identity group is absent from the actual fit roster of the model that scored it; panel /
dev2 groups absent from the cfall roster), A-side / B-side primaries with fit-group counts, 102 key checks; cfall values of the development
tables (in-fit) are not shown.
Original docstring: Inputs: diag/cf107/r107_<model>_<tag>.csv for model in v8w7a, cf0, cfA, cfB,
cfall; diag/cf107/split.csv; diag/r102_<tag>.csv (main comparison). CF = cross-fitted main RR (development tables: fold A molecules scored by cfB,
fold B by cfA; panel and dev2 scored by cfall). d = CF - v8w7a.
Checks first (stop on failure): identical row sets across models and complete vs the selection CSVs / c1_usable; values finite in [0, 1];
v8w7a main = 102 main on every row; cf0 (same runs as v8w7a, --filter_to_csv, merged analog parquet) reproduces v8w7a on every row; every
development molecule has a fold label. Primary = 1/2 A (053 NP C2: 4 cells, each 1/8) + 1/2 B_D (f1/f2 D C2: 2 cells, each 1/4). Gate: primary
>= +0.005 and lower > 0; A and B_D lower >= -0.01; protections lower >= -0.01: old B (f1/f2 NP C2 C-F), G C1 (f1/f2), panel C1 clean (cfall),
053 NP C1 (4 cells). dev2 NP C2 (cfall) = stress, reported only."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, "diag", "cf108"); C7 = os.path.join(HERE, "diag", "cf107"); NB = 4000; TOL = 1e-12
TAGS = ["np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel", "p2dev"]; DEV = ["np053f1dev", "np053f2dev", "f1dev", "f2dev"]
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv",
            "p2dev": "eval_set2/v2/p2_molecules.csv", "panel": "panel_np250/p1_molecules.csv"}
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
SPLIT = pd.read_csv(os.path.join(C7, "split.csv")); SPLIT["molecule"] = SPLIT.molecule.astype(str)
assert not SPLIT.duplicated(["tag", "molecule"]).any() and SPLIT.identity_group.notna().all()
FOLD = {(t, m): f for t, m, f in zip(SPLIT.tag, SPLIT.molecule, SPLIT.cf)}; GRP = {(t, m): int(g) for t, m, g in zip(SPLIT.tag, SPLIT.molecule, SPLIT.identity_group)}
ROS = {m: set(pd.read_csv(os.path.join(HERE, f"rank_{m}w", "fit_roster.csv")).identity_group.astype(int)) for m in ("cfA", "cfB", "cfall")}
_ST = pd.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "identity_folds", "structures.parquet"), columns=["inchikey14", "scorer_key", "identity_group"])
K2G = dict(zip(_ST.scorer_key.astype(str), _ST.identity_group.astype(int))); R2G = dict(zip(_ST.inchikey14.astype(str), _ST.identity_group.astype(int)))


def stop(m): sys.exit(f"STOP (107 check): {m}")


D, CHK = {}, []
for t in TAGS:
    X = {}
    for m in ("v8w7a", "cfA", "cfB", "cfall"):
        p = os.path.join(C, f"r108_{m if m == 'v8w7a' else m + 'w'}_{t}.csv")
        if not os.path.exists(p): stop(f"missing {p}")
        x = pd.read_csv(p); x["molecule"] = x.molecule.astype(str); X[m] = x.set_index(["set", "view", "molecule"]).main
    keys = set(X["v8w7a"].index)
    if any(set(v.index) != keys or v.index.duplicated().any() for v in X.values()): stop(f"{t}: row sets differ between models")
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[t])); ev["molecule"] = ev.molecule.astype(str); exp = set()
    for s, g in ev.groupby("set"):
        M = pd.read_csv(os.path.join(HERE, RUN_OF[t], f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        for mm in g.molecule:
            exp.add((s, "c2", mm))
            if bool(M.loc[mm, "c1_usable"]): exp.add((s, "c1", mm))
    if keys != exp: stop(f"{t}: rows vs expected: missing {len(exp - keys)} extra {len(keys - exp)}")
    F = pd.DataFrame({m: v for m, v in X.items()}).reset_index()
    if not np.isfinite(F[["v8w7a", "cfA", "cfB", "cfall"]].values).all() or (F[["v8w7a", "cfA", "cfB", "cfall"]].values < 0).any() or (F[["v8w7a", "cfA", "cfB", "cfall"]].values > 1).any(): stop(f"{t}: values")
    r102 = pd.read_csv(os.path.join(HERE, f"diag/r102_{t}.csv")); r102["molecule"] = r102.molecule.astype(str); r102 = r102.set_index(["set", "view", "molecule"]).main
    if r102.index.duplicated().any() or not np.isfinite(r102.values).all(): stop(f"{t}: 102 keys / values")
    if set(r102.index) != keys: stop(f"{t}: 102 rows differ")
    n102 = int((np.abs(X["v8w7a"].reindex(r102.index) - r102) > TOL).sum()); n0 = 0   # (cf0 = v8w7a established in 107)
    CHK.append(f"| {t} | {len(F)} | {n102} | {n0} |")
    if n102: stop(f"{t}: v8w7a main differs from 102 on {n102} rows")
    if t in DEV:
        fl = [FOLD.get((t, mm)) for mm in F.molecule]
        if any(f not in ("A", "B") for f in fl): stop(f"{t}: molecule without a fold label")
        F["CF"] = np.where(np.array(fl) == "A", F.cfB, F.cfA); F["side"] = fl
        bad = sum(1 for mm, f in zip(F.molecule, fl) if GRP[(t, mm)] in ROS["cfB" if f == "A" else "cfA"])
        if bad: stop(f"{t}: {bad} rows scored by a model whose fit roster contains their identity group")
    else:
        F["CF"] = F.cfall; F["side"] = "all"   # GLOBAL identity groups (the panel CSV's identity_group column is a local 0..249 index, not the global id)
        gmap = {mm: (K2G.get(str(k), R2G.get(mm))) for mm, k in zip(ev.molecule, ev.scorer_key)}
        if any(v is None for v in gmap.values()): stop(f"{t}: molecule without a global identity group")
        bad = sum(1 for mm in F.molecule if gmap[mm] in ROS["cfall"])
        if bad: stop(f"{t}: {bad} rows whose identity group is in the cfall fit roster")
    U = {m: pd.read_csv(os.path.join(C7, f"r107_{m}_{t}.csv")).assign(molecule=lambda d_: d_.molecule.astype(str)).set_index(["set", "view", "molecule"]).main for m in ("cfA", "cfB", "cfall")}
    k_ = list(zip(F.set, F.view, F.molecule))
    F["CFu"] = [U["cfB"][k] if sd == "A" else (U["cfA"][k] if sd == "B" else U["cfall"][k]) for k, sd in zip(k_, F.side)]
    F["d"] = F.CF - F.v8w7a; F["dm"] = F.CF - F.CFu; D[t] = F


def boot(cells, view, seed, extra=None):
    rng = np.random.default_rng(seed); arrs = []
    for t, s in cells:
        r = D[t][(D[t].set == s) & (D[t].view == view)]
        if extra is not None: r = r[extra(r)]
        if not len(r): stop(f"empty cell {t} {s} {view}")
        arrs.append(r.d.values.astype(float))
    pt = float(np.mean([a.mean() for a in arrs]))
    return pt, np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
st = lambda bs, e=0.01: "harm" if ci(bs)[1] < -e else ("non-inferior" if ci(bs)[0] >= -e else "undetermined")
CA = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N"), ("np053f2dev", "NP_H"), ("np053f2dev", "NP_N")]; CBD = [("f1dev", "D_np_single"), ("f2dev", "D_np_single")]
pa, ba = boot(CA, "c2", 102); pb, bb = boot(CBD, "c2", 103); p, bs = 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb
SIDES = {sd: (0.5 * boot(CA, "c2", 102, lambda r, sd=sd: r.side == sd)[0] + 0.5 * boot(CBD, "c2", 103, lambda r, sd=sd: r.side == sd)[0]) for sd in ("A", "B")}
PROT = {"old B f1/f2 NP C2 (C-F)": ([(t, s) for t in ("f1dev", "f2dev") for s in NP], "c2", None), "G C1 (f1/f2)": ([("f1dev", "G_tims_crosslib"), ("f2dev", "G_tims_crosslib")], "c1", None),
        "panel C1 clean (cfall)": ([("panel", "P_np250")], "c1", lambda r: r.molecule.isin(CLEAN)), "053 NP C1 (4 cells)": (CA, "c1", None)}
pr = {k: boot(c_, v_, 7, e_) for k, (c_, v_, e_) in PROT.items()}
gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and all(ci(b_)[0] >= -0.01 for _, b_ in pr.values())
L = ["# 108 reading: 107 data + C1 weight-share restoration (decision: CF_w - v8w7a; mechanism: CF_w - CF_unweighted)", "", "## Checks", "", "| tag | rows | v8w7a vs 102 diff | (cf0 check in 107) |", "|---|---:|---:|---:|"] + CHK
L += ["", "## Decision", "", f"- **primary 1/2 A + 1/2 B_D: {fmt(p, bs)}**", f"- A 053 NP C2: {fmt(pa, ba)}", f"- B_D f1/f2 D C2: {fmt(pb, bb)}",
      f"- by side (point estimates; fold-A rows scored by cfB, fold-B rows by cfA): A-side {SIDES['A']:+.4f}, B-side {SIDES['B']:+.4f}; fit identity groups cfA {len(ROS['cfA'])}, cfB {len(ROS['cfB'])}, cfall {len(ROS['cfall'])}"]
def mech(cells, view, extra=None):
    r = pd.concat([D[t][(D[t].set == s_) & (D[t].view == view)] for t, s_ in cells]); r = r[extra(r)] if extra is not None else r; return f"{r.dm.mean():+.4f} (row mean, n {len(r)})"
L += ["", "## Mechanism (weighted - 107 unweighted, same rows and scoring direction; descriptive)", f"- A 053 NP C2: {mech(CA, 'c2')}", f"- B_D f1/f2 D C2: {mech(CBD, 'c2')}",
      f"- G C1: {mech([('f1dev', 'G_tims_crosslib'), ('f2dev', 'G_tims_crosslib')], 'c1')}", f"- panel C1 clean: {mech([('panel', 'P_np250')], 'c1', lambda r: r.molecule.isin(CLEAN))}", f"- 053 NP C1: {mech(CA, 'c1')}"]
L += [f"- {k}: {fmt(*pr[k])} ({st(pr[k][1])})" for k in PROT]
L += [f"- dev2 NP C2 (cfall, stress): {fmt(*boot([('p2dev', s) for s in NP], 'c2', 21))}", f"- **gate: {'PASS -> confirmation (107 section 3)' if gate else 'NO'}**", "",
      "## Diagnostics (row means; cfall on the development tables is in-fit and not shown)", "", "| layer | n | v8w7a | CF | rescued / lost (CF vs v8w7a) |", "|---|---:|---:|---:|---|"]
for lab, cells, vw, ex in [("A 053 NP C2", CA, "c2", None), ("B_D f1/f2 D C2", CBD, "c2", None)] + [(k, c_, v_, e_) for k, (c_, v_, e_) in PROT.items()]:
    r = pd.concat([D[t][(D[t].set == s) & (D[t].view == vw)] for t, s in cells]); r = r[ex(r)] if ex is not None else r
    L.append(f"| {lab} | {len(r)} | {r.v8w7a.mean():.4f} | {r.CF.mean():.4f} | {int((r.d > TOL).sum())} / {int((r.d < -TOL).sum())} |")
open(os.path.join(C, "x108_summary.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
