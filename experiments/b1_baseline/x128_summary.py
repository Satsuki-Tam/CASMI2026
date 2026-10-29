"""128 reading (128_prereg_wf.md, Codex 127 Q2), written before any 128 result. Inputs: diag/r128_<tag>.csv = gen_eval2fd_n128.py (= gen_eval2fd.py
with --wf / --wf_mist) on the fold-<k> tables with rank_v8w7a (main = P), columns wf_<x>_<alpha> for x in {gl, mist}, alpha in {0.0, 0.5, 2.0},
wf_ub and the per-row diagnostics.
Checks (STOP): completeness against the selection CSV + c1_usable (as 111); no duplicate rows; one identity group per cell row; main equal to the
frozen P (diag/r102_<tag>.csv; bank: diag/r111_base_c1bankdev.csv) on every row; every wf column finite in [0, 1]; wf_<x>_0.0 == main on every row
(alpha 0 = P); wf_ub >= main on every row; the MIST score manifest = the aug checkpoint sha256; the MSG-overlap record (msg_scorer_keys.txt) printed.
Readings (fixed):
  1. upper-bound screen: primary(wf_ub - main) < +0.005 -> the position-preserving family cannot pass (stop it; not a judgement on X).
  2. gate per (family, alpha in {0.5, 2.0}) = 111's gate: primary >= +0.005 and 95% lower > 0; block A and block D lower >= -0.01; protections lower
     >= -0.01 (old B f1dev C-F C2, G C1, NP C1 H/N, c1dev C1 pooled). Selection: the largest primary among the passing (ties: GL, then the smaller alpha).
  3. fold 2 (--fold 2 --pick <family>_<alpha>): the picked one's primary must be > 0 to go to confirmation (stability, not an independent check).
Diagnostics (not used for the decision): per cell rows changed up / down, coverage, truth's within-formula ranks under P and X (pessimistic ties).
Usage (Spark, experiments/b1_baseline): python -X utf8 x128_summary.py [--fold 2 --pick mist_2.0]"""
import argparse, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12; ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, default=1, choices=[1, 2]); ap.add_argument("--pick", default=""); A = ap.parse_args(); K_ = A.fold
TAGF, TAGN = f"f{K_}dev", f"np053f{K_}dev"; TAGB = "c1bankdev" if K_ == 1 else None
EVAL_CSV = {TAGF: f"eval_set_f{K_}/p2_molecules.csv", TAGN: f"np053_f{K_}dev/p2_molecules.csv"}
RUN_OF = {TAGF: f"run_f{K_}dev", TAGN: f"run_np053_f{K_}dev"}
BASE_OF = {TAGF: f"diag/r102_{TAGF}.csv", TAGN: f"diag/r102_{TAGN}.csv"}
if TAGB: EVAL_CSV[TAGB] = "c1bank_f1/c1dev/p2_molecules.csv"; RUN_OF[TAGB] = "run_c1bankdev_f1"; BASE_OF[TAGB] = "diag/r111_base_c1bankdev.csv"
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [(TAGN, "NP_H"), (TAGN, "NP_N")]; CELLS_D = [(TAGF, "D_np_single")]
PROT = {f"old B {TAGF} C-F C2": ([(TAGF, s) for s in NPS], "c2"), f"G C1 {TAGF}": ([(TAGF, "G_tims_crosslib")], "c1"), f"NP C1 {TAGN} H/N": (CELLS_A, "c1")}
FAMS = ["gl", "mist"]; ALS = ["0.5", "2.0"]
def stop(msg): sys.exit(f"STOP (128 check): {msg}")
mf = json.load(open(os.path.join(ROOT, "experiments", "mist", "scores", f"mist_{TAGF}_manifest.json")))
if mf.get("ckpt_sha256") != "9f251d772f68315ba6fe2dc75a3b2e1ec477d3f41ffbeaf5143749157b67b177": stop("MIST scores not from the aug checkpoint")
MSGK = set(open(os.path.join(ROOT, "data", "external", "massspecgym", "msg_scorer_keys.txt")).read().split())
D = {}
for t, csv in EVAL_CSV.items():
    p = os.path.join(HERE, f"diag/r128{'' if K_ == 1 else 'f2'}_{t}.csv")
    if not os.path.exists(p): stop(f"missing {p}")
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
    cols = ["main", "wf_ub"] + [f"wf_{f}_{a}" for f in FAMS for a in ("0.0",) + tuple(ALS)]
    for c in cols:
        v = x[c].values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{t}: {c} not finite in [0, 1]")
    for f in FAMS:
        if ((x[f"wf_{f}_0.0"] - x.main).abs() > TOL).any(): stop(f"{t}: wf_{f}_0.0 differs from main")
    if (x.wf_ub < x.main - TOL).any(): stop(f"{t}: wf_ub below main")
    y = pd.read_csv(os.path.join(HERE, BASE_OF[t]), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
    z = x.merge(y, on=["set", "view", "molecule"], how="left", suffixes=("", "_base"), validate="one_to_one")
    if z.main_base.isna().any() or ((z.main - z.main_base).abs() > TOL).any(): stop(f"{t}: main differs from {BASE_OF[t]}")
    x["ig"] = x.molecule.map(ig)
    if x.ig.isna().any() or x.duplicated(["set", "view", "ig"]).any(): stop(f"{t}: identity group missing or repeated within a cell")
    D[t] = x.sort_values(["set", "view", "molecule"]).reset_index(drop=True)
def cellrows(t, s, view):
    r = D[t]; r = r[(r.set == s) & (r.view == view)]
    if not len(r): stop(f"empty cell {t} {s} {view}")
    return r
def boot(cells, view, var, seed):
    rng = np.random.default_rng(seed); arrs = [(cellrows(t, s, view)[var] - cellrows(t, s, view)["main"]).values.astype(float) for t, s in cells]
    return float(np.mean([a.mean() for a in arrs])), np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])
def boot_pooled(r, var, seed):
    rng = np.random.default_rng(seed); a = (r[var] - r["main"]).values.astype(float); return float(a.mean()), np.array([a[rng.integers(0, len(a), len(a))].mean() for _ in range(NB)])
ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
def primary(var):
    pa, ba = boot(CELLS_A, "c2", var, 1111); pd_, bd = boot(CELLS_D, "c2", var, 1112); return 0.5 * pa + 0.5 * pd_, 0.5 * ba + 0.5 * bd, (pa, ba), (pd_, bd)
L = [f"# 128 reading (fold {K_}): within-formula rerank of P (128_prereg_wf.md)", ""]
ub, bub, _, _ = primary("wf_ub"); L += [f"- upper bound primary(wf_ub - main) = {fmt(ub, bub)} -> " + ("position-preserving families can reach the gate" if ub >= 0.005 else "**below +0.005: both families stop**"), ""]
L += ["| variant | primary | block A | block D | " + " | ".join(PROT) + (" | c1dev C1 pooled" if TAGB else "") + " | gate |", "|---|---|---|---|" + "---|" * len(PROT) + ("---|" if TAGB else "") + "---|"]
RES = {}
for f in FAMS:
    for al in ALS:
        v = f"wf_{f}_{al}"
        if A.pick and v != f"wf_{A.pick}": continue
        p, bs, (pa, ba), (pd_, bd) = primary(v); pr = {k: boot(c, w, v, 1117) for k, (c, w) in PROT.items()}
        gate = ub >= 0.005 and p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
        cell = ""
        if TAGB:
            bank = D[TAGB]; bank = bank[bank.view == "c1"]; pb, bb = boot_pooled(bank, v, 1118); gate = gate and ci(bb)[0] >= -0.01; cell = f" | {fmt(pb, bb)} (n {len(bank)})"
        RES[v] = (p, gate)
        L.append(f"| {v} | **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pd_, bd)} | " + " | ".join(fmt(*pr[k]) for k in PROT) + cell + f" | {'PASS' if gate else 'no'} |")
if K_ == 1:
    passing = [v for v in RES if RES[v][1]]
    sel = max(passing, key=lambda v: (RES[v][0], v.startswith("wf_gl"), -float(v.rsplit("_", 1)[1]))) if passing else None
    L += ["", f"- **Selection (fold 1): {sel if sel else 'none'}**" + (" -> fold-2 stability check with --fold 2 --pick " + sel[3:] if sel else "")]
else:
    v = f"wf_{A.pick}"; L += ["", f"- fold-2 stability of {v}: primary {RES[v][0]:+.4f} -> " + ("go to the confirmation" if RES[v][0] > 0 else "**not positive: no confirmation**")]
L += ["", "## Diagnostics (not used for the decision)", "", "| tag | set | view | n | main | wf_ub | changed up / down per variant | cov gl / mist (median) | truth within-formula rank P / gl / mist (median, in-formula rows) |", "|---|---|---|---:|---:|---:|---|---|---|"]
for t, x in D.items():
    for (s, w), r in x.groupby(["set", "view"], sort=True):
        ch = " ; ".join(f"{f}{al}: {int((r[f'wf_{f}_{al}'] > r.main + TOL).sum())}/{int((r[f'wf_{f}_{al}'] < r.main - TOL).sum())}" for f in FAMS for al in ALS)
        inr = r[r.wf_rP_form > 0]
        L.append(f"| {t} | {s} | {w} | {len(r)} | {r.main.mean():.4f} | {r.wf_ub.mean():.4f} | {ch} | {r.wf_cov_gl.median():.0f} / {r.wf_cov_mist.median():.0f} | "
                 f"{inr.wf_rP_form.median() if len(inr) else float('nan'):.0f} / {inr.wf_rgl_form_pess.median() if len(inr) else float('nan'):.0f} / {inr.wf_rmist_form_pess.median() if len(inr) else float('nan'):.0f} |")
out = chr(10).join(L) + chr(10); open(os.path.join(HERE, f"diag/x128{'' if K_ == 1 else 'f2'}_summary.md"), "w", encoding="utf-8").write(out); print(out)
