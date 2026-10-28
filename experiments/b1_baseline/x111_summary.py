"""111 reading (111_prereg_nscorer.md), written before any 111 model was trained. Inputs: diag/r111_<ck>_<tag>.csv = gen_eval2fd --v7f --parents 0
--nscore (main = rank_v8w7a on the EXISTING fold-1 tables run_f1dev / run_np053_f1dev with stored GLACIER; N from the 111 checkpoint <ck>, Fs from the
base fold-1 FPNet), ck in CKS (training budgets, fixed in the registration), tag in {f1dev, np053f1dev}.
Checks before any number (STOP): completeness (expected (set, view, molecule) from the selection CSV and c1_usable; no missing / extra / duplicate);
main, t1N_0.5, t1Fs_0.5 finite in [0, 1]; main equal to diag/r102_<tag>.csv main on every row (same tables, same GLACIER, same ranker); no missing
N / Fs value (miss_N = miss_Fs = 0); every row with main = 1 keeps 1 in both connections; one identity group per row within a cell.
Candidate per checkpoint: C_N = t1N_0.5 (main rank-1 kept; all other candidates of the view list ordered by 1/(10 + r_main) + 0.5/(10 + r_N), ties
-> main order, top 25). d = C_N - main. Primary = 1/4 d(np053f1dev NP_H C2) + 1/4 d(np053f1dev NP_N C2) + 1/2 d(f1dev D_np_single C2).
Gate: primary >= +0.005 and 95% lower > 0; block A (NP_H / NP_N C2 equal) and block D lower >= -0.01; protections lower >= -0.01: old B = f1dev
C/D/E/F C2 (equal), G C1 = f1dev G C1, NP C1 = np053f1dev NP_H / NP_N C1 (equal). NP_X descriptive. Bootstrap 4000, rows (= identities) resampled
within cells, seeds 1111 (A), 1112 (D), 1117 (protections), 1119 (C_N - C_Fs). Empty cell / undetermined protection = failure.
Selection over checkpoints: among those passing, the largest primary; ties (1e-12) -> the shorter budget; none passing -> no candidate.
Reported with each checkpoint: C_N - C_Fs on the primary weights (lower > 0 = value beyond the single-spectrum input format; otherwise unresolved;
C_Fs is never promoted to a candidate), C_Fs - main, the leader-safe upper bound (0.5 - RR_main for truths ranked > 1 in the list).
A pass is a fold-1 development result: the selected budget must pass the same gate on fold 2 (fold-2 init + training, same budget) on its own.
Usage: python -X utf8 x111_summary.py"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12
CKS = ["s2000", "s8000", "s20000"]   # budgets in updates; the order is the tie-break (shorter first)
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv"}
RUN_OF = {"f1dev": "run_f1dev", "np053f1dev": "run_np053_f1dev"}
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N")]; CELLS_D = [("f1dev", "D_np_single")]
PROT = {"old B f1dev C-F C2": ([("f1dev", s) for s in NPS], "c2"), "G C1 f1dev": ([("f1dev", "G_tims_crosslib")], "c1"), "NP C1 np053f1dev H/N": (CELLS_A, "c1")}


def stop(msg): sys.exit(f"STOP (111 check): {msg}")


def load(ck):
    D = {}
    for t, csv in EVAL_CSV.items():
        p = os.path.join(HERE, f"diag/r111_{ck}_{t}.csv")
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
        for c in ("main", "t1N_0.5", "t1Fs_0.5", "N_only", "Fs_only"):
            v = x[c].values.astype(float)
            if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{ck} {t}: {c} not finite in [0, 1]")
        if (x.miss_N.fillna(0) > 0).any() or (x.miss_Fs.fillna(0) > 0).any(): stop(f"{ck} {t}: missing N / Fs values ({int(x.miss_N.fillna(0).sum())} / {int(x.miss_Fs.fillna(0).sum())})")
        if ((x.main == 1) & ((x["t1N_0.5"] != 1) | (x["t1Fs_0.5"] != 1))).any(): stop(f"{ck} {t}: a rank-1-correct row changed")
        y = pd.read_csv(os.path.join(HERE, f"diag/r102_{t}.csv"), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
        z = x.merge(y, on=["set", "view", "molecule"], how="left", suffixes=("", "_102"), validate="one_to_one")
        if z.main_102.isna().any() or ((z.main - z.main_102).abs() > TOL).any(): stop(f"{ck} {t}: main differs from the 102 main on {int(((z.main - z.main_102).abs() > TOL).sum())} rows")
        x["ig"] = x.molecule.map(ig)
        if x.ig.isna().any() or x.duplicated(["set", "view", "ig"]).any(): stop(f"{ck} {t}: identity group missing or repeated within a cell")
        x["tag"] = t; D[t] = x
    return D


def boot(D, cells, view, var, ref, seed):
    rng = np.random.default_rng(seed); arrs = []
    for t, s in cells:
        r = D[t]; r = r[(r.set == s) & (r.view == view)]
        if not len(r): stop(f"empty cell {t} {s} {view}")
        arrs.append((r[var] - r[ref]).values.astype(float))
    return float(np.mean([a.mean() for a in arrs])), np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"


def primary(D, var, ref, sa, sd):
    pa, ba = boot(D, CELLS_A, "c2", var, ref, sa); pd_, bd = boot(D, CELLS_D, "c2", var, ref, sd)
    return 0.5 * pa + 0.5 * pd_, 0.5 * ba + 0.5 * bd, (pa, ba), (pd_, bd)


L = ["# 111 reading: own spectrum-molecule scorer N, fixed leader-safe connection (111_prereg_nscorer.md)", "",
     "| checkpoint | primary C_N - main | block A | block D | " + " | ".join(PROT) + " | gate | C_N - C_Fs (primary weights) | C_Fs - main | upper bound |", "|---|---|---|---|" + "---|" * len(PROT) + "---|---|---|---|"]
RES = {}
for ck in CKS:
    D = load(ck)
    p, bs, (pa, ba), (pd_, bd) = primary(D, "t1N_0.5", "main", 1111, 1112)
    pr = {k: boot(D, c, v, "t1N_0.5", "main", 1117) for k, (c, v) in PROT.items()}
    gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
    q, bq, _, _ = primary(D, "t1N_0.5", "t1Fs_0.5", 1119, 1120); f, bf, _, _ = primary(D, "t1Fs_0.5", "main", 1121, 1122)
    cm = lambda t, s_: D[t][(D[t].set == s_) & (D[t].view == "c2")]
    ub = lambda r: float(np.where(r.rP_n > 1, 0.5 - r.main, 0.0).mean())   # leader-safe upper bound: truth moved to rank 2
    u = 0.25 * ub(cm("np053f1dev", "NP_H")) + 0.25 * ub(cm("np053f1dev", "NP_N")) + 0.5 * ub(cm("f1dev", "D_np_single"))
    RES[ck] = (p, gate, D)
    L.append(f"| {ck} | **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pd_, bd)} | " + " | ".join(fmt(*pr[k]) for k in PROT) + f" | {'PASS' if gate else 'no'} | {fmt(q, bq)} | {fmt(f, bf)} | {u:+.4f} |")
passing = [ck for ck in CKS if RES[ck][1]]
sel = None
if passing:
    best = max(RES[ck][0] for ck in passing); sel = next(ck for ck in CKS if ck in passing and RES[ck][0] >= best - TOL)
L += ["", f"- **Selection: {sel + ' -> fold-2 replication with this budget' if sel else 'none (no checkpoint passed)'}**", "",
      "## Diagnostics (row means; not used for the decision)", "", "| checkpoint | cell | n | main | C_N | C_Fs | N alone | Fs alone | rescued / lost (C_N) | truth-rank Spearman main vs N (truth in list) |", "|---|---|---:|---:|---:|---:|---:|---:|---|---:|"]
for ck in CKS:
    for t, x in RES[ck][2].items():
        for (s, v), r in x.groupby(["set", "view"], sort=True):
            d = r["t1N_0.5"] - r.main; both = (r.rP_n > 0) & (r.rN > 0)
            sp = r[both][["rP_n", "rN"]].rank().corr().iloc[0, 1] if both.sum() > 2 else float("nan")
            L.append(f"| {ck} | {t} {s} {v} | {len(r)} | {r.main.mean():.4f} | {r['t1N_0.5'].mean():.4f} | {r['t1Fs_0.5'].mean():.4f} | {r.N_only.mean():.4f} | {r.Fs_only.mean():.4f} | {int((d > TOL).sum())} / {int((d < -TOL).sum())} | {sp:.3f} |")
open(os.path.join(HERE, "diag/x111_summary.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
