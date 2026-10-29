"""128 v2 reading (128_prereg_wf.md section v2, Codex 128), written before any 128 result. Inputs: diag/r128v2[f2]_<tag>.csv = gen_eval2fd_n128v2.py
(gen_eval2fd.py --wf / --wf_mist, v2 semantics) with rank_v8w7a on the fold tables and the MIST v2 scores (experiments/mist/scores_v2).
Checks (STOP): the row manifest written by the job matches the files; the MIST v2 manifests of every tag (aug checkpoint sha, code hashes,
each set's output sha = the file read by the evaluator); completeness against the selection CSV + c1_usable; no duplicate rows; one identity
group per cell row (the pooled bank: globally unique); main equal to the frozen P (r102 / r111_base) on every expected row (one-to-one); every wf
column finite in [0, 1]; wf_<x>_0.0 == main; wf_ub >= wf_ub_<x> >= main.
Readings (fixed):
  1. screen: primary(wf_ub - main) < +0.005 -> both families stop (the coverage-free bound cannot reach the gate); otherwise "not excluded".
  2. fold 1: gate per (family, alpha in {0.5, 2.0}) = primary >= +0.005 and 95% lower > 0; block A and block D lower >= -0.01; protections lower
     >= -0.01: old B f1dev C-F C2, G C1, NP C1 H/N, c1dev C1 pooled, and (v2) c1dev POSITIVE-ion C1 (C1_pos_* strata) pooled. Selection: the largest
     primary among the passing (ties: GL, then the smaller alpha) -> written to diag/x128v2_selection.json.
  3. fold 2 (--fold 2 --pick <the fold-1 selection>, required and checked): primary > 0 AND block A / D, old B, G C1, NP C1 lower >= -0.01.
Diagnostics (not for the decision): per cell rows up / down, movable truths, reorderable groups, truth within-formula ranks (only rows where the
truth is movable under X), coverage-aware bounds.
Usage (Spark, experiments/b1_baseline): python -X utf8 x128v2_summary.py   |   python -X utf8 x128v2_summary.py --fold 2 --pick mist_2.0"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12; ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, default=1, choices=[1, 2]); ap.add_argument("--pick", default=""); A = ap.parse_args(); K_ = A.fold
def stop(msg): sys.exit(f"STOP (128 v2 check): {msg}")
if K_ == 1 and A.pick: stop("--pick is not allowed on fold 1")
SELF = os.path.join(HERE, "diag", "x128v2_selection.json")
if K_ == 2:
    if not os.path.exists(SELF): stop("fold-1 selection file missing")
    sel1 = json.load(open(SELF)).get("selection")
    if not A.pick or A.pick != sel1: stop(f"--pick must be the fold-1 selection ({sel1})")
SUF = "" if K_ == 1 else "f2"
TAGF, TAGN = f"f{K_}dev", f"np053f{K_}dev"; TAGB = "c1bankdev" if K_ == 1 else None
EVAL_CSV = {TAGF: f"eval_set_f{K_}/p2_molecules.csv", TAGN: f"np053_f{K_}dev/p2_molecules.csv"}
RUN_OF = {TAGF: f"run_f{K_}dev", TAGN: f"run_np053_f{K_}dev"}
BASE_OF = {TAGF: f"diag/r102_{TAGF}.csv", TAGN: f"diag/r102_{TAGN}.csv"}
if TAGB: EVAL_CSV[TAGB] = "c1bank_f1/c1dev/p2_molecules.csv"; RUN_OF[TAGB] = "run_c1bankdev_f1"; BASE_OF[TAGB] = "diag/r111_base_c1bankdev.csv"
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [(TAGN, "NP_H"), (TAGN, "NP_N")]; CELLS_D = [(TAGF, "D_np_single")]
PROT = {f"old B {TAGF} C-F C2": ([(TAGF, s) for s in NPS], "c2"), f"G C1 {TAGF}": ([(TAGF, "G_tims_crosslib")], "c1"), f"NP C1 {TAGN} H/N": (CELLS_A, "c1")}
FAMS = ["gl", "mist"]; ALS = ["0.5", "2.0"]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
man = os.path.join(HERE, f"diag/x128v2{SUF}_rows_manifest.txt")
if not os.path.exists(man): stop("row manifest missing")
for ln in open(man):
    h, f = ln.split()
    if sha(os.path.join(HERE, f)) != h: stop(f"{f} differs from the row manifest")
for t in EVAL_CSV:
    mf = json.load(open(os.path.join(ROOT, "experiments", "mist", "scores_v2", f"mist_{t}_manifest.json")))
    if mf.get("ckpt_sha256") != "9f251d772f68315ba6fe2dc75a3b2e1ec477d3f41ffbeaf5143749157b67b177": stop(f"MIST scores of {t} not from the aug checkpoint")
    for s_, rec in mf["sets"].items():
        if rec.get("output_sha256") != sha(os.path.join(ROOT, "experiments", "mist", "scores_v2", f"mist_{t}_{s_}.parquet")): stop(f"MIST output {t} {s_} differs from its manifest")
    print(f"{t}: MIST v2 manifest ok (code {mf.get('code')}, commit {mf.get('mist_commit', '?')[:12]})")
MSGK = set(open(os.path.join(ROOT, "data", "external", "massspecgym", "msg_scorer_keys.txt")).read().split())
D = {}
for t, csv in EVAL_CSV.items():
    p = os.path.join(HERE, f"diag/r128v2{SUF}_{t}.csv")
    x = pd.read_csv(p); x["molecule"] = x.molecule.astype(str)
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ig = dict(zip(ev.molecule, ev.identity_group.astype(int)))
    print(f"{t}: selected molecules whose scorer key is in MSG: {int(ev.scorer_key.astype(str).isin(MSGK).sum())} / {len(ev)}")
    exp = set()
    for s, g in ev.groupby("set"):
        M = pd.read_csv(os.path.join(HERE, RUN_OF[t], f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        for m in g.molecule:
            if m not in M.index: stop(f"{t} {s} {m}: selected molecule without a ledger row")
            exp.add((s, "c2", m)); cu = str(M.loc[m, "c1_usable"])
            if cu not in ("True", "False"): stop(f"{t} {s} {m}: c1_usable is not a boolean")
            if cu == "True": exp.add((s, "c1", m))
    got = list(zip(x.set, x.view, x.molecule))
    if len(got) != len(set(got)): stop(f"{t}: duplicate rows")
    if set(got) != exp: stop(f"{t}: rows missing {len(exp - set(got))} / extra {len(set(got) - exp)}")
    cols = ["main", "wf_ub"] + [f"wf_ub_{f}" for f in FAMS] + [f"wf_{f}_{a}" for f in FAMS for a in ("0.0",) + tuple(ALS)]
    for c in cols:
        v = x[c].values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{t}: {c} not finite in [0, 1]")
    for f in FAMS:
        if ((x[f"wf_{f}_0.0"] - x.main).abs() > TOL).any(): stop(f"{t}: wf_{f}_0.0 differs from main")
        if ((x.wf_ub < x[f"wf_ub_{f}"] - TOL) | (x[f"wf_ub_{f}"] < x.main - TOL)).any(): stop(f"{t}: bounds out of order for {f}")
    y = pd.read_csv(os.path.join(HERE, BASE_OF[t]), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
    yk = set(zip(y.set, y.view, y.molecule))
    if not exp <= yk: stop(f"{t}: the frozen P lacks {len(exp - yk)} expected rows")
    z = x.merge(y, on=["set", "view", "molecule"], how="left", suffixes=("", "_base"), validate="one_to_one")
    if z.main_base.isna().any() or ((z.main - z.main_base).abs() > TOL).any(): stop(f"{t}: main differs from {BASE_OF[t]}")
    x["ig"] = x.molecule.map(ig)
    if x.ig.isna().any() or x.duplicated(["set", "view", "ig"]).any(): stop(f"{t}: identity group missing or repeated within a cell")
    if t == TAGB and x[x.view == "c1"].ig.duplicated().any(): stop("bank: identity group repeated across the pooled C1 rows")
    D[t] = x.sort_values(["set", "view", "molecule"]).reset_index(drop=True)
def cellrows(t, s, view):
    r = D[t]; r = r[(r.set == s) & (r.view == view)]
    if not len(r): stop(f"empty cell {t} {s} {view}")
    return r
def boot(cells, view, var, seed):
    rng = np.random.default_rng(seed); arrs = [(cellrows(t, s, view)[var] - cellrows(t, s, view)["main"]).values.astype(float) for t, s in cells]
    return float(np.mean([a.mean() for a in arrs])), np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])
def boot_pooled(r, var, seed):
    if not len(r): stop("empty pooled set")
    rng = np.random.default_rng(seed); a = (r[var] - r["main"]).values.astype(float); return float(a.mean()), np.array([a[rng.integers(0, len(a), len(a))].mean() for _ in range(NB)])
ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
def primary(var):
    pa, ba = boot(CELLS_A, "c2", var, 1111); pd_, bd = boot(CELLS_D, "c2", var, 1112); return 0.5 * pa + 0.5 * pd_, 0.5 * ba + 0.5 * bd, (pa, ba), (pd_, bd)
L = [f"# 128 v2 reading (fold {K_}): within-formula rerank of P (128_prereg_wf.md v2)", ""]
ub, bub, _, _ = primary("wf_ub")
L += [f"- coverage-free upper bound primary(wf_ub - main) = {fmt(ub, bub)} -> " + ("not excluded by this bound" if ub >= 0.005 else "**below +0.005: both families stop**")]
for f in FAMS:
    u_, b_, _, _ = primary(f"wf_ub_{f}"); L.append(f"- coverage-aware bound {f}: {fmt(u_, b_)} (descriptive)")
L += ["", "| variant | primary | block A | block D | " + " | ".join(PROT) + (" | c1dev C1 pooled | c1dev positive-ion C1" if TAGB else "") + " | gate |", "|---|---|---|---|" + "---|" * len(PROT) + ("---|---|" if TAGB else "") + "---|"]
RES = {}
for f in FAMS:
    for al in ALS:
        v = f"wf_{f}_{al}"
        if A.pick and v != f"wf_{A.pick}": continue
        p, bs, (pa, ba), (pd_, bd) = primary(v); pr = {k: boot(c, w, v, 1117) for k, (c, w) in PROT.items()}
        gate = ub >= 0.005 and p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
        cell = ""
        if TAGB:
            bank = D[TAGB]; c1 = bank[bank.view == "c1"]; pb, bb = boot_pooled(c1, v, 1118); pos = c1[c1.set.astype(str).str.startswith("C1_pos")]; pp, bp = boot_pooled(pos, v, 1119)
            gate = gate and ci(bb)[0] >= -0.01 and ci(bp)[0] >= -0.01; cell = f" | {fmt(pb, bb)} (n {len(c1)}) | {fmt(pp, bp)} (n {len(pos)})"
        stab = p > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
        RES[v] = (p, gate, stab)
        L.append(f"| {v} | **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pd_, bd)} | " + " | ".join(fmt(*pr[k]) for k in PROT) + cell + f" | {'PASS' if gate else 'no'} |")
if K_ == 1:
    passing = [v for v in RES if RES[v][1]]
    sel = max(passing, key=lambda v: (RES[v][0], v.startswith("wf_gl"), -float(v.rsplit("_", 1)[1]))) if passing else None
    json.dump(dict(selection=(sel[3:] if sel else None), primary=(RES[sel][0] if sel else None)), open(SELF, "w"), indent=1)
    L += ["", f"- **Selection (fold 1): {sel if sel else 'none'}**" + (f" -> fold-2 stability with --fold 2 --pick {sel[3:]}" if sel else "")]
else:
    v = f"wf_{A.pick}"; L += ["", f"- fold-2 stability of {v}: primary {RES[v][0]:+.4f}, protections / blocks lower >= -0.01: {RES[v][2]} -> " + ("go to the confirmation" if RES[v][2] else "**no confirmation**")]
SHOW = [A.pick] if A.pick else [f"{f}_{al}" for f in FAMS for al in ALS]
L += ["", "## Diagnostics (not used for the decision)", "", "| tag | set | view | n | main | wf_ub | up / down (" + ", ".join(SHOW) + ") | movable truths gl / mist | reorderable groups gl / mist (mean) | truth in-formula rank P / X (median over movable rows) |", "|---|---|---|---:|---:|---:|---|---|---|---|"]
for t, x in D.items():
    for (s, w), r in x.groupby(["set", "view"], sort=True):
        ch = " ; ".join(f"{k}: {int((r[f'wf_{k}'] > r.main + TOL).sum())}/{int((r[f'wf_{k}'] < r.main - TOL).sum())}" for k in SHOW)
        rk = []
        for f in FAMS:
            mv = r[r[f"wf_move_{f}"] == 1]
            rk.append(f"{f} {mv.wf_rP_form.median() if len(mv) else float('nan'):.0f}/{mv[f'wf_r{f}_form_pess'].median() if len(mv) else float('nan'):.0f}")
        L.append(f"| {t} | {s} | {w} | {len(r)} | {r.main.mean():.4f} | {r.wf_ub.mean():.4f} | {ch} | {int(r.wf_move_gl.sum())} / {int(r.wf_move_mist.sum())} | "
                 f"{r.wf_ngrp_gl.mean():.2f} / {r.wf_ngrp_mist.mean():.2f} | {'; '.join(rk)} |")
out = chr(10).join(L) + chr(10); open(os.path.join(HERE, f"diag/x128v2{SUF}_summary.md"), "w", encoding="utf-8").write(out); print(out)
