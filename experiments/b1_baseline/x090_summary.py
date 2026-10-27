"""090 development reading (090_prereg_popshift.md incl. the Codex 090 amendment). One gen_eval2fd --v7f --pop_ws 0.15,0 pass: diag/r090m_<model>_<tag>.csv.
R0 = rank_v7a_pc main (control), R1 = rank_v7a_pc pw0.15, R2 = rank_v7a_np4 main, R3 = rank_v7a_np4 pw0.15, R4 = rank_v7a_np7 pw0.0.
Primary (i): f1/f2 dev NP strata strict C2 (C/D/E/F pooled within a fold, folds = equal blocks), Rk - R0, identity bootstrap.
Eligibility: (i) >= +0.005, both folds > 0, pooled lower > 0; non-inferiority L >= -0.01 on G C1 (f1/f2), 053 NP C1, panel C1 clean.
Sensitivity (not a condition): 053 dev C2 reweighted by the truth's prior-rank stratum (reached molecules) under three scenarios.
Breakdowns: C/D/E/F, truth COCONUT / not, GL path / fallback; 2x2 decomposition; implementation check (fallback rows: R0 == R2 and R1 == R3)."""
import os, sys, json, pickle
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv",
            "p2dev": "eval_set2/v2/p2_molecules.csv", "panel": "panel_np250/p1_molecules.csv"}
VAR = {"R0": ("rank_v7a_pc", "main"), "R1": ("rank_v7a_pc", "pw0.15"), "R2": ("rank_v7a_np4", "main"), "R3": ("rank_v7a_np4", "pw0.15"), "R4": ("rank_v7a_np7", "pw0.0")}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
SCEN = {"S1 9/18/30/43": {"1": 0.09, "2-3": 0.18, "4-10": 0.30, "11+": 0.43}, "S2 15/20/30/35": {"1": 0.15, "2-3": 0.20, "4-10": 0.30, "11+": 0.35},
        "S3 5/15/30/50": {"1": 0.05, "2-3": 0.15, "4-10": 0.30, "11+": 0.50}}
_POOL = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "v2_pool", "pool_meta.parquet"), columns=["key", "src"])
POOL_COCO = set(_POOL.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
COCO_RAW = set(str(x) for x in pickle.load(open(os.path.join(HERE, "..", "..", "data", "external", "coconut", "coco_meta.pkl"), "rb"))["keys"])
def tcoco(tag):
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[tag]))
    return {str(m): (str(k) in POOL_COCO) or (str(r) in COCO_RAW) for m, k, r in zip(ev.molecule, ev.scorer_key, ev.raw_key if "raw_key" in ev.columns else ev.molecule)}
def glmeta(tag):
    run = os.path.join(HERE, RUN_OF[tag]); out = {}
    for f in sorted(os.listdir(run)):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(run, f)); F["molecule"] = F.molecule.astype(str)
        M = pd.read_csv(os.path.join(run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        pth = os.path.join(run, "work", f"gl_{s}.json")
        try: ok = json.load(open(pth + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        gl = json.load(open(pth)) if ok else {}
        for mid, g0 in F.groupby("molecule", sort=False):
            for view in ("c2", "c1"):
                if view == "c1" and (mid not in M.index or not bool(M.loc[mid, "c1_usable"])): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]; fin = sum((gl.get(mid) or {}).get(sm) is not None for sm in g.smiles)
                out[(s, view, mid)] = bool(len(g) and fin >= max(2, 0.5 * len(g)))
    return out
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
def stratum(r): return "unreached" if r == 0 else ("1" if r == 1 else ("2-3" if r <= 3 else ("4-10" if r <= 10 else ("11-25" if r <= 25 else "26+"))))
def load(tag):
    out = {}
    for m in sorted({v[0] for v in VAR.values()}):
        p = os.path.join(HERE, f"diag/r090m_{m}_{tag}.csv")
        if not os.path.exists(p): return None
        out[m] = pd.read_csv(p)
    base = out["rank_v7a_pc"][["set", "view", "molecule"]].copy(); base["molecule"] = base.molecule.astype(str)
    for k, (m, col) in VAR.items():
        d = out[m]; assert len(d) == len(base) and (d.molecule.astype(str).values == base.molecule.values).all(); base[k] = d[col].values
    T = tcoco(tag); base["tcoco"] = [T.get(m, False) for m in base.molecule]
    G = glmeta(tag); base["gl_ok"] = [G.get((s, v, m), False) for s, v, m in zip(base.set, base.view, base.molecule)]
    return base
def block_stat(blocks):
    blocks = [b for b in blocks if len(b)]
    pt = float(np.mean([b.mean() for b in blocks]))
    bs = np.array([np.mean([b[rng.integers(0, len(b), len(b))].mean() for b in blocks]) for _ in range(NB)])
    return pt, np.percentile(bs, [2.5, 97.5])
def wstat(d, w):
    w = w / w.sum(); return float((d * w).sum())
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo >= -e else "undetermined")
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
D = {t: load(t) for t in RUN_OF}
miss = [t for t, d in D.items() if d is None]
need = ("f1dev", "f2dev", "np053f1dev", "np053f2dev", "panel")
if any(t in miss for t in need): sys.exit(f"missing tables: {miss}")
PR = {t: prior_rank(t) for t in ("np053f1dev", "np053f2dev")}
def diff(t, a_, b_, f): x = D[t]; x = x[f(x)]; return (x[b_] - x[a_]).values
def prim(a_, b_, f=lambda x: (x.view == "c2") & x.set.isin(NP)):
    bl = [diff(t, a_, b_, f) for t in ("f1dev", "f2dev")]; p, ci = block_stat(bl); return p, ci, [float(b.mean()) for b in bl]
L = ["# 090 development reading (amended registration)", "", f"tables missing (stress only): {miss}", "",
     "## Implementation check (fallback rows must satisfy R0 == R2 and R1 == R3)"]
for t in ("f1dev", "f2dev", "np053f1dev", "np053f2dev", "panel"):
    x = D[t]; fb = x[~x.gl_ok]
    L.append(f"- {t}: fallback rows {len(fb)}, max |R2-R0| {float(np.abs(fb.R2 - fb.R0).max()) if len(fb) else 0:.6f}, max |R3-R1| {float(np.abs(fb.R3 - fb.R1).max()) if len(fb) else 0:.6f}")
L += ["", "## Registered variants vs R0", "",
      "| variant | (i) f1/f2 NP strict C2 | fold1 / fold2 | G C1 (f1/f2) | 053 NP C1 | panel C1 clean | eligible |", "|---|---|---|---|---|---|---|"]
ELIG = {}
for k in ("R1", "R2", "R3", "R4"):
    p, ci, folds = prim("R0", k)
    g = block_stat([diff(t, "R0", k, lambda x: (x.view == "c1") & (x.set == "G_tims_crosslib")) for t in ("f1dev", "f2dev")])
    n1 = block_stat([diff(t, "R0", k, lambda x: x.view == "c1") for t in ("np053f1dev", "np053f2dev")])
    pn = block_stat([diff("panel", "R0", k, lambda x: (x.view == "c1") & x.molecule.isin(CLEAN))])
    el = (p >= 0.005) and all(f > 0 for f in folds) and (ci[0] > 0) and all(c[1][0] >= -0.01 for c in (g, n1, pn))
    ELIG[k] = el
    L.append(f"| {k} {VAR[k]} | {fmt(p, ci)} | {folds[0]:+.4f} / {folds[1]:+.4f} | {fmt(*g)} ({st(*g[1])}) | {fmt(*n1)} ({st(*n1[1])}) | {fmt(*pn)} ({st(*pn[1])}) | {'YES' if el else 'no'} |")
p43, ci43, f43 = prim("R3", "R4")
sel = "R3" if ELIG["R3"] else None
if ELIG["R4"] and p43 >= 0.005 and ci43[0] > 0:
    g43 = block_stat([diff(t, "R3", "R4", lambda x: (x.view == "c1") & (x.set == "G_tims_crosslib")) for t in ("f1dev", "f2dev")])
    n43 = block_stat([diff(t, "R3", "R4", lambda x: x.view == "c1") for t in ("np053f1dev", "np053f2dev")])
    p43c = block_stat([diff("panel", "R3", "R4", lambda x: (x.view == "c1") & x.molecule.isin(CLEAN))])
    if all(c[1][0] >= -0.01 for c in (g43, n43, p43c)): sel = "R4"
L += ["", f"R4 - R3 on (i): {fmt(p43, ci43)} (folds {f43[0]:+.4f} / {f43[1]:+.4f})", f"**SELECTED (registered rule): {sel or 'none -> no normal candidate'}**", "",
      "## 2x2 decomposition on (i)", ""]
for name, a_, b_ in (("R1-R0 (fixed-rule prior 0.5 -> 0.15, original ranker)", "R0", "R1"), ("R2-R0 (ranker without 4 popularity features)", "R0", "R2"),
                     ("R3-R1 (ranker change at prior 0.15)", "R1", "R3"), ("R3-R2 (prior change with the new ranker)", "R2", "R3")):
    p, ci, fo = prim(a_, b_); L.append(f"- {name}: {fmt(p, ci)}")
bl = [diff(t, "R0", "R3", lambda x: (x.view == "c2") & x.set.isin(NP)) - diff(t, "R0", "R2", lambda x: (x.view == "c2") & x.set.isin(NP)) - diff(t, "R0", "R1", lambda x: (x.view == "c2") & x.set.isin(NP)) for t in ("f1dev", "f2dev")]
L.append(f"- interaction R3-R2-R1+R0: {fmt(*block_stat(bl))}")
L += ["", "## Breakdowns of (i) (f1/f2 pooled blocks)", "", "| variant | C | D | E | F | truth COCONUT | truth not COCONUT | GL path | fallback |", "|---|---|---|---|---|---|---|---|---|"]
for k in ("R1", "R2", "R3", "R4"):
    cells = []
    for s_ in NP: cells.append(f"{prim('R0', k, lambda x, s_=s_: (x.view == 'c2') & (x.set == s_))[0]:+.4f}")
    cells.append(f"{prim('R0', k, lambda x: (x.view == 'c2') & x.set.isin(NP) & x.tcoco)[0]:+.4f}")
    cells.append(f"{prim('R0', k, lambda x: (x.view == 'c2') & x.set.isin(NP) & ~x.tcoco)[0]:+.4f}")
    cells.append(f"{prim('R0', k, lambda x: (x.view == 'c2') & x.set.isin(NP) & x.gl_ok)[0]:+.4f}")
    cells.append(f"{prim('R0', k, lambda x: (x.view == 'c2') & x.set.isin(NP) & ~x.gl_ok)[0]:+.4f}")
    L.append(f"| {k} | " + " | ".join(cells) + " |")
L += ["", "## Sensitivity: 053 dev C2 by the truth's prior rank (f1+f2 pooled) and re-weighted scenarios (reached molecules; not a condition)", "",
      "| stratum | n | R0 | R1-R0 | R2-R0 | R3-R0 | R4-R0 |", "|---|---:|---:|---:|---:|---:|---:|"]
X = []
for t in ("np053f1dev", "np053f2dev"):
    x = D[t]; x = x[x.view == "c2"].copy(); x["st"] = [stratum(PR[t].get((s, m), 0)) for s, m in zip(x.set, x.molecule)]; X.append(x)
X = pd.concat(X)
for s_ in ("1", "2-3", "4-10", "11-25", "26+", "unreached"):
    g = X[X.st == s_]
    if len(g): L.append(f"| {s_} | {len(g)} | {g.R0.mean():.4f} | " + " | ".join(f"{(g[k] - g.R0).mean():+.4f}" for k in ("R1", "R2", "R3", "R4")) + " |")
Y = X[X.st != "unreached"].copy(); Y["st4"] = Y.st.replace({"11-25": "11+", "26+": "11+"})
for nm, sc in SCEN.items():
    cnt = Y.st4.value_counts(); w = np.array([sc[s_] / cnt[s_] for s_ in Y.st4])
    L.append(f"- {nm}: " + ", ".join(f"{k}-R0 {wstat((Y[k] - Y.R0).values, w):+.4f}" for k in ("R1", "R2", "R3", "R4")))
L.append(f"- plain 053 C2 (all molecules): " + ", ".join(f"{k}-R0 {(X[k] - X.R0).mean():+.4f}" for k in ("R1", "R2", "R3", "R4")))
if D["p2dev"] is not None:
    x = D["p2dev"]; x = x[(x.view == "c2") & x.set.isin(NP)]
    L.append(f"- dev2 NP C2 (stress): " + ", ".join(f"{k}-R0 {fmt(*block_stat([(x[x.set == s][k] - x[x.set == s].R0).values for s in NP]))}" for k in ("R1", "R2", "R3", "R4")))
open(os.path.join(HERE, "diag/x090_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
