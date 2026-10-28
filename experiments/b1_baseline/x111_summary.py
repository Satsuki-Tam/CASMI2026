"""111 reading (111_prereg_nscorer.md, amended after Codex 112), written before any 111 model was trained. Inputs per training budget ck in CKS:
diag/r111_<ck>_<tag>.csv = gen_eval2fd --v7f --parents 0 --nscore (main = rank_v8w7a on the EXISTING fold-1 tables with their stored GLACIER;
N from the 111 checkpoint <ck>; Fs / Fm from the base fold-1 FPNet), tag in {f1dev, np053f1dev, c1bankdev}; plus diag/r111_base_c1bankdev.csv
(the same evaluator WITHOUT --nscore on the c1dev bank = its frozen P, since the bank has no r102 baseline).
Checks before any number (STOP): GLACIER audits of every table bound to the current files and accepted by the evaluator's loader with the
audited finite count; the score manifests' model sha256 / step equal to the budget's trained checkpoint; completeness (expected (set, view, molecule) from the selection CSV and c1_usable; no missing / extra /
duplicate); main, t1N_0.5, t1Fs_0.5, t1Fm_0.5 finite in [0, 1]; main equal to diag/r102_<tag>.csv (f1dev, np053f1dev) or to
diag/r111_base_c1bankdev.csv (bank) on every row; no missing N / Fs / Fm (miss_* = 0); every row with main = 1 keeps 1 in every connection;
t1Fs_0.5 and t1Fm_0.5 identical on every row across the budgets (they do not depend on the 111 model); one identity group per row within a cell.
Candidate per budget: C_N = t1N_0.5 (main rank-1 kept; all other candidates of the view list ordered by 1/(10 + r_main) + 0.5/(10 + r_N), ties
-> main order, top 25). d = C_N - main. Primary = 1/4 d(np053f1dev NP_H C2) + 1/4 d(np053f1dev NP_N C2) + 1/2 d(f1dev D_np_single C2).
Gate: primary >= +0.005 and 95% lower > 0; block A (NP_H / NP_N C2 equal) and block D lower >= -0.01; protections lower >= -0.01: old B = f1dev
C/D/E/F C2 (equal), G C1 = f1dev G C1, NP C1 = np053f1dev NP_H / NP_N C1 (equal), and (added before any result, Codex 112) C1 bank c1dev =
all c1dev C1 rows POOLED (one identity one vote over the bank strata; per-stratum / per-library numbers descriptive only). NP_X descriptive.
Bootstrap 4000, rows (= identities) resampled within cells (pooled: within the pooled set), seeds 1111 (A), 1112 (D), 1117 (protections),
1118 (bank), 1119 (C_N - C_Fs). Empty cell / undetermined protection = failure.
Selection over budgets: among those passing, the largest primary; ties (1e-12) -> the shorter budget; none passing -> no candidate.
Reported with each budget (never used to select): C_N - C_Fs on the primary weights (lower > 0 = value beyond the single-spectrum input on the
same representative structures; otherwise unresolved; C_Fs / C_Fm are never promoted), C_Fs - main, C_Fm - main (representative structure vs the
table's spelling aggregation), the leader-safe upper bound, and pure discrimination with NEUTRAL (pessimistic) ties: MRR of the truth under N,
Fs, Fm alone (r*_pess).
A pass is a fold-1 development result: the selected budget must pass the same gate on fold 2 (fold-2 init + training, same budget) on its own.
Usage: python -X utf8 x111_summary.py [--fold 1 --cks s2000 s8000 s20000] (default = the registered fold-1 reading); fold 2: --fold 2 --cks s<selected>"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("--fold", type=int, default=1, choices=[1, 2]); _ap.add_argument("--cks", nargs="+", default=["s2000", "s8000", "s20000"])
_A = _ap.parse_args(); K_ = _A.fold
CKS = _A.cks   # budgets in updates; the order is the tie-break (shorter first); fold 2 = the one budget selected on fold 1 (Codex 111 Q3)
SUF = "" if K_ == 1 else "f2"   # fold-2 files: diag/r111f2_<ck>_<tag>.csv, experiments/n111/scores_f2/<ck>/, run dir n111/r2
TAGF, TAGN, TAGB = f"f{K_}dev", f"np053f{K_}dev", ("c1bankdev" if K_ == 1 else "c1bankf2dev")
EVAL_CSV = {TAGF: f"eval_set_f{K_}/p2_molecules.csv", TAGN: f"np053_f{K_}dev/p2_molecules.csv", TAGB: f"c1bank_f{K_}/c1dev/p2_molecules.csv"}
RUN_OF = {TAGF: f"run_f{K_}dev", TAGN: f"run_np053_f{K_}dev", TAGB: f"run_c1bankdev_f{K_}"}
BASE_OF = {TAGF: f"diag/r102_{TAGF}.csv", TAGN: f"diag/r102_{TAGN}.csv", TAGB: f"diag/r111{SUF}_base_{TAGB}.csv"}
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [(TAGN, "NP_H"), (TAGN, "NP_N")]; CELLS_D = [(TAGF, "D_np_single")]
PROT = {f"old B {TAGF} C-F C2": ([(TAGF, s) for s in NPS], "c2"), f"G C1 {TAGF}": ([(TAGF, "G_tims_crosslib")], "c1"), f"NP C1 {TAGN} H/N": (CELLS_A, "c1")}
VARS = ["t1N_0.5", "t1Fs_0.5", "t1Fm_0.5"]


def stop(msg): sys.exit(f"STOP (111 check): {msg}")


import hashlib, json
import b1_locked_eval as LE
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


for t, csv in EVAL_CSV.items():   # Codex 114: GLACIER audit of every table used (bound to the current files) and the evaluator's loader acceptance
    for s in sorted(pd.read_csv(os.path.join(HERE, csv)).set.unique()):
        g = os.path.join(HERE, RUN_OF[t], "work", f"gl_{s}.json"); ap_ = g + ".audit.json"; inp = os.path.join(HERE, RUN_OF[t], f"b1_runner_{s}_in.json")
        if not os.path.isfile(ap_): stop(f"missing GLACIER audit {ap_}")
        au = json.load(open(ap_)); hs = au.get("sha256", {})
        if au.get("failure", 1) != 0 or hs.get("output") != sha(g) or hs.get("input") != sha(inp) or hs.get("meta") != sha(g + ".meta.json"): stop(f"GLACIER audit {ap_} failed or not about the current files")
        d, meta, _ = LE.runner(os.path.join(HERE, RUN_OF[t]), s, "gl")
        if d is None: stop(f"the evaluator's loader rejects {g}")
        if sum(1 for dd in d.values() for v in (dd or {}).values() if v is not None and np.isfinite(float(v))) != au.get("finite"): stop(f"{g}: loader finite count differs from the audit")


def load(ck):
    D = {}; S_ = ck[1:]
    ckp = os.path.join(ROOT, "experiments", "n111", "r1" if K_ == 1 else "r2", f"n111{SUF}_s{S_}_s{S_}.pt"); ck_sha = sha(ckp)
    for t in EVAL_CSV:   # Codex 114: the scores were made with this budget's trained checkpoint
        mf = json.load(open(os.path.join(ROOT, "experiments", "n111", "scores" if K_ == 1 else "scores_f2", ck, f"n111_{t}_manifest.json")))
        if mf.get("model_sha256") != ck_sha or int(mf.get("model_step", -1)) != int(S_): stop(f"{ck} {t}: scores not made with the trained checkpoint {ckp}")
    for t, csv in EVAL_CSV.items():
        p = os.path.join(HERE, f"diag/r111{SUF}_{ck}_{t}.csv")
        if not os.path.exists(p): stop(f"missing {p}")
        x = pd.read_csv(p); x["molecule"] = x.molecule.astype(str)
        ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ig = dict(zip(ev.molecule, ev.identity_group.astype(int)))
        exp = set()
        for s, g in ev.groupby("set"):
            M = pd.read_csv(os.path.join(HERE, RUN_OF[t], f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
            for m in g.molecule:
                if m not in M.index: stop(f"{ck} {t} {s} {m}: selected molecule without a ledger row")
                exp.add((s, "c2", m))
                if bool(M.loc[m, "c1_usable"]): exp.add((s, "c1", m))
        got = list(zip(x.set, x.view, x.molecule))
        if len(got) != len(set(got)): stop(f"{ck} {t}: duplicate rows")
        if set(got) != exp: stop(f"{ck} {t}: rows missing {len(exp - set(got))} / extra {len(set(got) - exp)}")
        for c in ["main"] + VARS + ["N_only", "Fs_only", "Fm_only"]:
            v = x[c].values.astype(float)
            if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{ck} {t}: {c} not finite in [0, 1]")
        for c in ("miss_N", "miss_Fs", "miss_Fm"):
            if (x[c].fillna(0) > 0).any(): stop(f"{ck} {t}: missing values {c} = {int(x[c].fillna(0).sum())}")
        if ((x.main == 1) & (x[VARS] != 1).any(axis=1)).any(): stop(f"{ck} {t}: a rank-1-correct row changed")
        y = pd.read_csv(os.path.join(HERE, BASE_OF[t]), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
        z = x.merge(y, on=["set", "view", "molecule"], how="left", suffixes=("", "_base"), validate="one_to_one")
        if z.main_base.isna().any() or ((z.main - z.main_base).abs() > TOL).any(): stop(f"{ck} {t}: main differs from {BASE_OF[t]} on {int(((z.main - z.main_base).abs() > TOL).sum())} rows")
        x["ig"] = x.molecule.map(ig)
        if x.ig.isna().any() or x.duplicated(["set", "view", "ig"]).any(): stop(f"{ck} {t}: identity group missing or repeated within a cell")
        x["tag"] = t; D[t] = x.sort_values(["set", "view", "molecule"]).reset_index(drop=True)
    return D


def cellrows(D, t, s, view):
    r = D[t]; r = r[(r.set == s) & (r.view == view)]
    if not len(r): stop(f"empty cell {t} {s} {view}")
    return r


def boot(D, cells, view, var, ref, seed):
    rng = np.random.default_rng(seed); arrs = [(cellrows(D, t, s, view)[var] - cellrows(D, t, s, view)[ref]).values.astype(float) for t, s in cells]
    return float(np.mean([a.mean() for a in arrs])), np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


def boot_pooled(r, var, ref, seed):
    rng = np.random.default_rng(seed); a = (r[var] - r[ref]).values.astype(float)
    if not len(a): stop("empty pooled set")
    return float(a.mean()), np.array([a[rng.integers(0, len(a), len(a))].mean() for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"


def primary(D, var, ref, sa, sd):
    pa, ba = boot(D, CELLS_A, "c2", var, ref, sa); pd_, bd = boot(D, CELLS_D, "c2", var, ref, sd)
    return 0.5 * pa + 0.5 * pd_, 0.5 * ba + 0.5 * bd, (pa, ba), (pd_, bd)


L = ["# 111 reading: own spectrum-molecule scorer N, fixed leader-safe connection (111_prereg_nscorer.md)", "",
     "| budget | primary C_N - main | block A | block D | " + " | ".join(PROT) + " | C1 bank c1dev pooled | gate | C_N - C_Fs (primary w.) | C_Fs - main | C_Fm - main | upper bound |",
     "|---|---|---|---|" + "---|" * len(PROT) + "---|---|---|---|---|---|"]
RES = {}; REF = None
for ck in CKS:
    D = load(ck)
    if REF is None: REF = {t: x[["set", "view", "molecule", "t1Fs_0.5", "t1Fm_0.5"]].copy() for t, x in D.items()}
    else:
        for t, x in D.items():
            if not (np.array_equal(x[["set", "view", "molecule"]].values, REF[t][["set", "view", "molecule"]].values) and np.allclose(x["t1Fs_0.5"].values, REF[t]["t1Fs_0.5"].values, atol=TOL, rtol=0)
                    and np.allclose(x["t1Fm_0.5"].values, REF[t]["t1Fm_0.5"].values, atol=TOL, rtol=0)): stop(f"{ck} {t}: C_Fs / C_Fm differ between budgets (scoring conditions mixed up)")
    p, bs, (pa, ba), (pd_, bd) = primary(D, "t1N_0.5", "main", 1111, 1112)
    pr = {k: boot(D, c, v, "t1N_0.5", "main", 1117) for k, (c, v) in PROT.items()}
    bank = D[TAGB]; bank = bank[bank.view == "c1"]; pb, bb = boot_pooled(bank, "t1N_0.5", "main", 1118)
    gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values()) and ci(bb)[0] >= -0.01
    q, bq, _, _ = primary(D, "t1N_0.5", "t1Fs_0.5", 1119, 1120); f, bf, _, _ = primary(D, "t1Fs_0.5", "main", 1121, 1122); fm, bfm, _, _ = primary(D, "t1Fm_0.5", "main", 1123, 1124)
    cm = lambda t, s_: D[t][(D[t].set == s_) & (D[t].view == "c2")]
    ub = lambda r: float(np.where(r.rP_n > 1, 0.5 - r.main, 0.0).mean())
    u = 0.25 * ub(cm(TAGN, "NP_H")) + 0.25 * ub(cm(TAGN, "NP_N")) + 0.5 * ub(cm(TAGF, "D_np_single"))
    RES[ck] = (p, gate, D)
    L.append(f"| {ck} | **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pd_, bd)} | " + " | ".join(fmt(*pr[k]) for k in PROT) + f" | {fmt(pb, bb)} (n {len(bank)}) | {'PASS' if gate else 'no'} | {fmt(q, bq)} | {fmt(f, bf)} | {fmt(fm, bfm)} | {u:+.4f} |")
passing = [ck for ck in CKS if RES[ck][1]]
sel = None
if passing:
    best = max(RES[ck][0] for ck in passing); sel = next(ck for ck in CKS if ck in passing and RES[ck][0] >= best - TOL)
L += ["", f"- **Selection: {sel + ' -> fold-2 replication with this budget' if sel else 'none (no budget passed)'}**", "",
      "## Diagnostics (row means; not used for the decision)", "",
      "| budget | cell | n | main | C_N | C_Fs | C_Fm | N alone (neutral ties) | Fs alone (neutral) | Fm alone (neutral) | rescued / lost (C_N) | truth-rank Spearman main vs N |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
rr = lambda r: np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
for ck in CKS:
    for t, x in RES[ck][2].items():
        for (s, v), r in x.groupby(["set", "view"], sort=True):
            d = r["t1N_0.5"] - r.main; both = (r.rP_n > 0) & (r.rN > 0)
            sp = r[both][["rP_n", "rN"]].rank().corr().iloc[0, 1] if both.sum() > 2 else float("nan")
            L.append(f"| {ck} | {t} {s} {v} | {len(r)} | {r.main.mean():.4f} | {r['t1N_0.5'].mean():.4f} | {r['t1Fs_0.5'].mean():.4f} | {r['t1Fm_0.5'].mean():.4f} | {rr(r.rN_pess.values).mean():.4f} | "
                     f"{rr(r.rFs_pess.values).mean():.4f} | {rr(r.rFm_pess.values).mean():.4f} | {int((d > TOL).sum())} / {int((d < -TOL).sum())} | {sp:.3f} |")
open(os.path.join(HERE, f"diag/x111{SUF}_summary.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
