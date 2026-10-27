"""090 development reading (090_prereg_popshift.md). One gen_eval2fd --v7f --pop_ws 0.15,0 pass: diag/r090m_<model>_<tag>.csv.
R0 = rank_v7a_pc main (control), R1 = rank_v7a_pc pw0.15, R2 = rank_v7a_np4 main, R3 = rank_v7a_np4 pw0.15, R4 = rank_v7a_np7 pw0.0.
Primary (i): f1/f2 dev NP strata C2 (C/D/E/F pooled within a fold, folds = equal blocks), Rk - R0.
Secondary (ii): 053 dev C2 re-weighted to the hidden-like prior-rank mix of reached molecules (rank 1 9%, 2-3 18%, 4-10 30%, 11+ 43%; unreached excluded),
plus the stratum table. Protection (eps 0.01, three states): G C1 (f1/f2), 053 NP C1. Reported: panel C1 clean (cost on famous class 1), dev2 NP C2 (stress)."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
VAR = {"R0": ("rank_v7a_pc", "main"), "R1": ("rank_v7a_pc", "pw0.15"), "R2": ("rank_v7a_np4", "main"), "R3": ("rank_v7a_np4", "pw0.15"), "R4": ("rank_v7a_np7", "pw0.0")}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
TGT = {"1": 0.09, "2-3": 0.18, "4-10": 0.30, "11+": 0.43}
def load(tag):
    out = {}
    for m in sorted({v[0] for v in VAR.values()}):
        p = os.path.join(HERE, f"diag/r090m_{m}_{tag}.csv")
        if not os.path.exists(p): return None
        out[m] = pd.read_csv(p)
    base = out["rank_v7a_pc"][["set", "view", "molecule"]].copy(); base["molecule"] = base.molecule.astype(str)
    for k, (m, col) in VAR.items():
        d = out[m]; assert len(d) == len(base) and (d.molecule.astype(str).values == base.molecule.values).all()
        base[k] = d[col].values
    return base
def prior_rank(tag, view="c2"):
    run = os.path.join(HERE, RUN_OF[tag]); pr = {}
    for f in sorted(os.listdir(run)):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(run, f), columns=["molecule", "is_truth", f"in_short_{view}", "pop_public", "fp"]); F = F[F[f"in_short_{view}"]]
        for mid, g in F.groupby("molecule"):
            o = np.lexsort((-g.fp.fillna(-1e9).values, -g.pop_public.values)); t = np.flatnonzero(g.is_truth.values[o])
            pr[(s, str(mid))] = int(t[0] + 1) if len(t) else 0
    return pr
def stratum(r): return "unreached" if r == 0 else ("1" if r == 1 else ("2-3" if r <= 3 else ("4-10" if r <= 10 else "11+")))
def block_stat(blocks):
    """blocks = list of arrays of per-molecule deltas; point = mean of block means; bootstrap within blocks."""
    blocks = [b for b in blocks if len(b)]
    pt = float(np.mean([b.mean() for b in blocks]))
    bs = np.array([np.mean([b[rng.integers(0, len(b), len(b))].mean() for b in blocks]) for _ in range(NB)])
    return pt, np.percentile(bs, [2.5, 97.5])
def wstat(d, w):
    w = w / w.sum(); pt = float((d * w).sum())
    bs = np.array([(lambda i: (d[i] * w[i]).sum() / w[i].sum())(rng.integers(0, len(d), len(d))) for _ in range(NB)])
    return pt, np.percentile(bs, [2.5, 97.5])
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo > -e else "undetermined")
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
D = {t: load(t) for t in RUN_OF}
miss = [t for t, d in D.items() if d is None]
if any(t in miss for t in ("f1dev", "f2dev", "np053f1dev", "np053f2dev")): sys.exit(f"missing tables: {miss}")
PR = {t: prior_rank(t) for t in ("np053f1dev", "np053f2dev")}
L = ["# 090 development reading", "", f"missing (stress / reported only): {miss}", "",
     "| variant | (i) f1/f2 NP C2 | (ii) 053 C2 hidden-like reweighted | 053 C2 plain | G C1 (state) | 053 NP C1 (state) | panel C1 clean | dev2 NP C2 |", "|---|---|---|---|---|---|---|---|"]
strat_rows = []
for k in ("R1", "R2", "R3", "R4"):
    # (i)
    bl = []
    for t in ("f1dev", "f2dev"):
        x = D[t]; x = x[(x.view == "c2") & x.set.isin(NP)]; bl.append((x[k] - x["R0"]).values)
    p_i, ci_i = block_stat(bl)
    # (ii) and plain 053
    ds, ws, dpl = [], [], []
    for t in ("np053f1dev", "np053f2dev"):
        x = D[t]; x = x[x.view == "c2"].copy(); x["st"] = [stratum(PR[t].get((s, m), 0)) for s, m in zip(x.set, x.molecule)]
        dpl.append((x[k] - x["R0"]).values)
        for s_, g in x.groupby("st"):
            strat_rows.append(dict(variant=k, fold=t, stratum=s_, n=len(g), R0=g["R0"].mean(), d=(g[k] - g["R0"]).mean()))
        y = x[x.st != "unreached"]; n_st = y.st.value_counts()
        ds.append((y[k] - y["R0"]).values); ws.append(np.array([TGT[s_] / n_st[s_] for s_ in y.st]) * 0.5)   # folds equal
    p_ii, ci_ii = wstat(np.concatenate(ds), np.concatenate(ws)); p_pl, ci_pl = block_stat(dpl)
    # protection
    bl = []
    for t in ("f1dev", "f2dev"):
        x = D[t]; x = x[(x.view == "c1") & (x.set == "G_tims_crosslib")]; bl.append((x[k] - x["R0"]).values)
    p_g, ci_g = block_stat(bl)
    bl = []
    for t in ("np053f1dev", "np053f2dev"):
        x = D[t]; x = x[(x.view == "c1")]; bl.append((x[k] - x["R0"]).values)
    p_n1, ci_n1 = block_stat(bl)
    pan = "n/a"
    if D["panel"] is not None:
        x = D["panel"]; x = x[(x.view == "c1") & x.molecule.isin(CLEAN)]; p_, ci_ = block_stat([(x[k] - x["R0"]).values]); pan = fmt(p_, ci_)
    dv2 = "n/a"
    if D["p2dev"] is not None:
        x = D["p2dev"]; x = x[(x.view == "c2") & x.set.isin(NP)]; p_, ci_ = block_stat([(x[x.set == s][k] - x[x.set == s]["R0"]).values for s in NP]); dv2 = fmt(p_, ci_)
    L.append(f"| {k} ({VAR[k][0]} {VAR[k][1]}) | {fmt(p_i, ci_i)} | {fmt(p_ii, ci_ii)} | {fmt(p_pl, ci_pl)} | {fmt(p_g, ci_g)} ({st(*ci_g)}) | {fmt(p_n1, ci_n1)} ({st(*ci_n1)}) | {pan} | {dv2} |")
S = pd.DataFrame(strat_rows).groupby(["variant", "stratum"]).apply(lambda g: pd.Series(dict(n=g.n.sum(), R0=(g.R0 * g.n).sum() / g.n.sum(), d=(g.d * g.n).sum() / g.n.sum()))).reset_index()
L += ["", "053 dev C2 by the truth's prior rank (f1+f2 pooled): R0 MRR and Rk - R0", "", "| stratum | n | R0 | " + " | ".join(["R1", "R2", "R3", "R4"]) + " |", "|---|---:|---:|---:|---:|---:|---:|"]
for s_ in ("1", "2-3", "4-10", "11+", "unreached"):
    r = S[(S.stratum == s_)]
    if not len(r): continue
    L.append(f"| {s_} | {int(r.n.iloc[0])} | {r.R0.iloc[0]:.4f} | " + " | ".join(f"{float(r[r.variant == k].d.iloc[0]):+.4f}" for k in ("R1", "R2", "R3", "R4")) + " |")
open(os.path.join(HERE, "diag/x090_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
