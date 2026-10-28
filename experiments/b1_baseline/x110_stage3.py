"""110 stage 3 (110_prereg_fpseed.md sections 3-4, amendments after Codex 110 / 112), written before any stage-1 or stage-3 result exists; run only if
stage 1 passed. End-to-end, fold 1 only: the v8w7a main (gen_eval2fd --v7f, rank_v8w7a frozen, --parents 0, views c1,c2) on
  control = run_f1dev_s0rep / run_np053f1dev_s0rep (seed 0 alone rebuilt on the same system)            -> diag/r110_s0rep_<tag>.csv
  FPavg   = run_f1dev_fpavg / run_np053f1dev_fpavg (1:1 logit average with the checked seed-1 final)   -> diag/r110_fpavg_<tag>.csv
GLACIER comes from ONE candidate-level cache (gl_share.py: existing run -> control -> FPavg), so a (molecule, SMILES) pair has the same value in
both arms and only uncovered candidates were computed. d = main(FPavg) - main(control) per (set, view, molecule).
Checks before any number (STOP): (1) GLACIER audit of every arm / set (gl_audit.py: no missing key, non-finite value or unscheduled null);
(2) completeness of both arms (expected rows from the selection CSV and c1_usable; c1_usable equal in both arms; values finite in [0, 1]);
(3) one identity group per row within a cell (so the row bootstrap is the identity-level paired bootstrap); (4) the control reproduces the
existing main (diag/r102_<tag>.csv) on EVERY row; otherwise STOP and report per cell the rows that differ, the signed mean, the mean absolute
and the maximum difference -- continuing requires --allow_repro <audit.md> (an existing file that records the cause, the rows and the meaning
of the changed control; Codex 112: no automatic tolerance).
Primary = 1/4 dMRR(np053f1dev NP_H C2) + 1/4 dMRR(np053f1dev NP_N C2) + 1/2 dMRR(f1dev D_np_single C2).
Gate: primary >= +0.005 and 95% lower > 0; block A (NP_H / NP_N C2, equal) and block D lower >= -0.01; protections lower >= -0.01:
  old B = f1dev C/D/E/F C2 (4 cells, equal weight), G C1 = f1dev G_tims_crosslib C1, NP C1 = np053f1dev NP_H / NP_N C1 (equal weight).
NP_X and the other cells are descriptive. Bootstrap: 4000 replicates, rows resampled within cells, seeds 1101 (A), 1102 (D), 1107 (protections).
An empty cell or an undetermined protection (lower < -0.01) is a failure. A pass is a development result for fold 1 only: fold 2 must pass the
same gate on its own (two fold-2-held-out models), with no pooling across folds; neither is an unopened confirmation or a submission decision.
Diagnostics (view-specific, Codex 112): C2 window reach = reach_external_b1, C2 list reach = reach_external_b1 & truth_in_short_c2, C1 list
reach = truth_in_short_c1; main MRR among rows reached in the list; rescued / lost rows; the difference to the existing main is also shown.
Usage (Spark, experiments/b1_baseline): python -X utf8 x110_stage3.py [--allow_repro AUDIT.md]"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12
ALLOW = sys.argv[sys.argv.index("--allow_repro") + 1] if "--allow_repro" in sys.argv else None
if ALLOW and not os.path.isfile(ALLOW): sys.exit(f"STOP (110 stage 3): --allow_repro needs an existing audit file, got {ALLOW}")
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv"}
SETS = {"f1dev": ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"], "np053f1dev": ["NP_H", "NP_X", "NP_N"]}
RUN = {(arm, t): f"run_{t}_{arm}" for arm in ("s0rep", "fpavg") for t in EVAL_CSV}
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N")]; CELLS_D = [("f1dev", "D_np_single")]


def stop(msg): sys.exit(f"STOP (110 stage 3): {msg}")


for (arm, t), run in RUN.items():   # (1) GLACIER audit gate
    for s in SETS[t]:
        p = os.path.join(HERE, run, "work", f"gl_{s}.json.audit.json")
        if not os.path.isfile(p): stop(f"missing GLACIER audit {p}")
        au = json.load(open(p))
        if au.get("failure", 1) != 0: stop(f"GLACIER audit failures {au.get('failure')} in {p}")
D, CHK, LED = {}, [], {}
for t, csv in EVAL_CSV.items():
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ig = dict(zip(ev.molecule, ev.identity_group.astype(int)))
    X = {}
    for arm in ("s0rep", "fpavg"):
        p = os.path.join(HERE, f"diag/r110_{arm}_{t}.csv")
        if not os.path.exists(p): stop(f"missing {p}")
        x = pd.read_csv(p, usecols=["set", "view", "molecule", "main"]); x["molecule"] = x.molecule.astype(str)
        exp, c1u = set(), {}
        for s, g in ev.groupby("set"):
            M = pd.read_csv(os.path.join(HERE, RUN[(arm, t)], f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule"); LED[(arm, t, s)] = M
            for m in g.molecule:
                if m not in M.index: stop(f"{arm} {t} {s} {m}: selected molecule without a ledger row")
                exp.add((s, "c2", m)); c1u[(s, m)] = bool(M.loc[m, "c1_usable"])
                if c1u[(s, m)]: exp.add((s, "c1", m))
        got = list(zip(x.set, x.view, x.molecule))
        if len(got) != len(set(got)): stop(f"{arm} {t}: duplicate rows")
        if set(got) != exp: stop(f"{arm} {t}: rows missing {len(exp - set(got))} / extra {len(set(got) - exp)}")
        v = x.main.values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{arm} {t}: main not finite in [0, 1]")
        X[arm] = (x, c1u)
    if X["s0rep"][1] != X["fpavg"][1]: stop(f"{t}: c1_usable differs between the arms")
    z = X["s0rep"][0].merge(X["fpavg"][0], on=["set", "view", "molecule"], suffixes=("_0", "_1"), validate="one_to_one")
    z["ig"] = z.molecule.map(ig)
    if z.ig.isna().any() or z.duplicated(["set", "view", "ig"]).any(): stop(f"{t}: identity group missing or repeated within a cell")
    y = pd.read_csv(os.path.join(HERE, f"diag/r102_{t}.csv"), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
    q = z.merge(y, on=["set", "view", "molecule"], how="left", validate="one_to_one")
    if q.main.isna().any(): stop(f"{t}: rows without an existing main")
    q["dr"] = q.main_0 - q.main
    for (s, vw), r in q.groupby(["set", "view"], sort=True):
        nd = int((r.dr.abs() > TOL).sum())
        CHK.append(f"| {t} {s} {vw} | {len(r)} | {nd} | {r.dr.mean():+.5f} | {r.dr.abs().mean():.5f} | {r.dr.abs().max():.4f} |")
    z["tag"] = t; z["d"] = z.main_1 - z.main_0; z["d_old"] = z.main_1 - q.main.values; D[t] = z
HDR = ["## Reproduction of the existing main by the control (control - r102)", "", "| cell | rows | rows differing | signed mean | mean abs | max abs |", "|---|---:|---:|---:|---:|---:|"]
if any(int(c.split("|")[3]) > 0 for c in CHK) and not ALLOW:
    open(os.path.join(HERE, "diag/x110_stage3_repro.md"), "w", encoding="utf-8").write(chr(10).join(HDR + CHK) + chr(10))
    stop("the control does not reproduce the existing main on every row; see diag/x110_stage3_repro.md (no candidate difference was computed)")


def cell(t, s, view):
    r = D[t]; r = r[(r.set == s) & (r.view == view)]
    if not len(r): stop(f"empty cell {t} {s} {view}")
    return r


def boot(cells, view, seed, col="d"):
    rng = np.random.default_rng(seed); arrs = [cell(t, s, view)[col].values.astype(float) for t, s in cells]
    return float(np.mean([a.mean() for a in arrs])), np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
pa, ba = boot(CELLS_A, "c2", 1101); pd_, bd = boot(CELLS_D, "c2", 1102); prim, bp = 0.5 * pa + 0.5 * pd_, 0.5 * ba + 0.5 * bd
PROT = {"old B f1dev C-F C2": ([("f1dev", s) for s in NPS], "c2"), "G C1 f1dev": ([("f1dev", "G_tims_crosslib")], "c1"), "NP C1 np053f1dev H/N": (CELLS_A, "c1")}
pr = {k: boot(c, v, 1107) for k, (c, v) in PROT.items()}
gate = prim >= 0.005 and ci(bp)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
po, bo = boot(CELLS_A, "c2", 1101, "d_old"); qo, bqo = boot(CELLS_D, "c2", 1102, "d_old")
L = ["# 110 stage 3: v8w7a main on FPavg tables vs the rebuilt seed-0 control (fold 1)", ""] + HDR + CHK + (["", f"- continued with --allow_repro {ALLOW}"] if ALLOW else [])
L += ["", "## Decision", "", f"| primary | block A | block D | " + " | ".join(PROT) + " | gate |", "|---|---|---|" + "---|" * len(PROT) + "---|",
      f"| **{fmt(prim, bp)}** | {fmt(pa, ba)} | {fmt(pd_, bd)} | " + " | ".join(fmt(*pr[k]) for k in PROT) + f" | {'PASS (fold 1) -> fold 2 replication' if gate else 'NO'} |", "",
      f"- FPavg vs the EXISTING main (r102, stored GLACIER; descriptive): primary {fmt(0.5 * po + 0.5 * qo, 0.5 * bo + 0.5 * bqo)}", ""]
L += ["## Diagnostics (row means, view-specific reach; not used for the decision)", "",
      "| cell | n | main control | main FPavg | rescued | lost | new rank-1 | lost rank-1 | window reach 0 / avg | list reach 0 / avg | MRR after list reach 0 / avg |", "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
for t, z in D.items():
    for (s, view), r in z.groupby(["set", "view"], sort=True):
        ms = r.molecule.values; out = []
        for arm, col in (("s0rep", "main_0"), ("fpavg", "main_1")):
            M = LED[(arm, t, s)].loc[ms]
            if view == "c2": w = M.reach_external_b1.astype(bool).values; l = w & M.truth_in_short_c2.astype(bool).values
            else: w = M.truth_in_window.astype(bool).values; l = M.truth_in_short_c1.astype(bool).values
            out.append((w.mean(), l.mean(), r[col].values[l].mean() if l.any() else float("nan")))
        L.append(f"| {t} {s} {view} | {len(r)} | {r.main_0.mean():.4f} | {r.main_1.mean():.4f} | {int((r.d > TOL).sum())} | {int((r.d < -TOL).sum())} | {int(((r.main_1 == 1) & (r.main_0 < 1)).sum())} | "
                 f"{int(((r.main_0 == 1) & (r.main_1 < 1)).sum())} | {out[0][0]:.3f} / {out[1][0]:.3f} | {out[0][1]:.3f} / {out[1][1]:.3f} | {out[0][2]:.4f} / {out[1][2]:.4f} |")
pd.concat(D.values(), ignore_index=True).to_csv(os.path.join(HERE, "diag/x110_stage3.csv"), index=False)
open(os.path.join(HERE, "diag/x110_stage3.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
