"""071 development summary (071_prereg_p1_scale.md + Codex 070 amendment), registered reading. All models re-evaluated in one pass by
gen_eval2m (diag/r071m_<model>_<tag>.csv; v4b / v8w checked equal to the Spark r047 / r056 CSVs).
MAIN = rank_v9a - rank_v8w_pc (more groups, matched composition); REPRO = v8w_pc - v8w (Spark); CURVE = v9h - v8w_pc and v9a - v9h;
COCO weight = v9b - v9a; Public context = v9X - v4b.
Primary: 053 dev NP_H C2 (COCONUT-listed truths, ranker path), blocks f1dev / f2dev equal; tau +0.005 (vs v8w_pc for MAIN).
Main protection (eps 0.01, three states, identity-level bootstrap): panel C1 clean (full_eval tables; fixed CSV sha 961ceb94) and f1dev / f2dev
NP C2 (C/D/E/F equal, blocks equal). Secondary: non-COCONUT-truth C2 (f1/f2 C+D), NP_H C2 conditional on (GL path & truth in shortlist),
G C1 / C2, dev2 NP C2, NP_H C1. NP_X / NP_N must be exactly 0."""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule)
assert len(CLEAN) == 202
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
def meta(tag):
    """(set, view, molecule) -> gl_ok (production GL path), pos (truth in the view shortlist), tcoco (truth COCONUT-listed)."""
    run = os.path.join(HERE, RUN_OF[tag]); out = {}
    for f in sorted(os.listdir(run)):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(run, f)); F["molecule"] = F.molecule.astype(str)
        M = pd.read_csv(os.path.join(run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        p = os.path.join(run, "work", f"gl_{s}.json")
        try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        gl = json.load(open(p)) if ok else {}
        for mid, g0 in F.groupby("molecule", sort=False):
            tco = bool(g0[g0.is_truth].in_coconut.any())
            for view in ("c2", "c1"):
                if view == "c1" and (mid not in M.index or not bool(M.loc[mid, "c1_usable"])): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]
                fin = sum((gl.get(mid) or {}).get(sm) is not None for sm in g.smiles)
                out[(s, view, mid)] = (bool(len(g) and fin >= max(2, 0.5 * len(g))), bool(g.is_truth.any()), tco)
    return out
META = {t: meta(t) for t in RUN_OF}   # p2dev may still be running (stress only)
def pair(ma, mb, tag):
    a = pd.read_csv(os.path.join(HERE, f"diag/r071m_{ma}_{tag}.csv")); b = pd.read_csv(os.path.join(HERE, f"diag/r071m_{mb}_{tag}.csv"))
    x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_a", "_b")); assert len(x) == len(a) == len(b), (ma, mb, tag, len(x), len(a), len(b))
    x["d"] = x.main_b - x.main_a; x["molecule"] = x.molecule.astype(str)
    mm = [META[tag].get((s, v, m), (False, False, False)) for s, v, m in zip(x.set, x.view, x.molecule)]
    x["gl_ok"] = [t[0] for t in mm]; x["pos"] = [t[1] for t in mm]; x["tcoco"] = [t[2] for t in mm]; return x
def stat(frames):
    pts, boots = [], []
    for df, strata in frames:
        gs = [df[df.set == s].d.values for s in strata] if strata else [df.d.values]
        gs = [g for g in gs if len(g)]
        if not gs: continue
        pts.append(np.mean([g.mean() for g in gs])); boots.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(boots), axis=0), [2.5, 97.5]), pts
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo > -e else "undetermined")
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
CMPS = [("MAIN", "rank_v8w_pc", "rank_v9a"), ("REPRO", "rank_v8w", "rank_v8w_pc"), ("CURVE1", "rank_v8w_pc", "rank_v9h"), ("CURVE2", "rank_v9h", "rank_v9a"),
        ("COCO", "rank_v9a", "rank_v9b"), ("PUB", "rank_v4b", "rank_v8w_pc"), ("PUB", "rank_v4b", "rank_v9a"), ("PUB", "rank_v4b", "rank_v9b")]
L = ["# 071 development (P1 stage 1), registered reading (Codex 070 amendment)", "",
     "| role | comparison | primary NP_H C2 (f1,f2) | blocks | panel C1 clean (state) | f1/f2 NP C2 C-F (state) | non-COCO C2 (f1/f2 C+D) | NP_H C2 GL&pos | G C1 / G C2 | dev2 NP C2 | NP_H C1 | NP_X/N max abs |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
DET = []
for role, ma, mb in CMPS:
    X = {}
    for t in RUN_OF:
        try: X[t] = pair(ma, mb, t)
        except FileNotFoundError: pass
    if not all(t in X for t in ("np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel")): L.append(f"| {role} | {mb} - {ma} | missing decision tables |"); continue
    nph = [X[t][(X[t].view == "c2") & (X[t].set == "NP_H")] for t in ("np053f1dev", "np053f2dev")]
    p, ci, bl = stat([(f, None) for f in nph])
    pn = X["panel"][X["panel"].view == "c1"]; pc, cic, _ = stat([(pn[pn.molecule.isin(CLEAN)], None)])
    q, ciq, _ = stat([(X[t][X[t].view == "c2"], NP) for t in ("f1dev", "f2dev")])
    nc, cinc, _ = stat([(X[t][(X[t].view == "c2") & (~X[t].tcoco)], ["C_np_crosslib", "D_np_single"]) for t in ("f1dev", "f2dev")])
    gp, cigp, _ = stat([(f[f.gl_ok & f.pos], None) for f in nph])
    g1 = np.mean([X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")].d.mean() for t in ("f1dev", "f2dev")])
    g2 = np.mean([X[t][(X[t].view == "c2") & (X[t].set == "G_tims_crosslib")].d.mean() for t in ("f1dev", "f2dev")])
    d2, ci2, _ = stat([(X["p2dev"][X["p2dev"].view == "c2"], NP)]) if "p2dev" in X else (float("nan"), (float("nan"), float("nan")), [])
    h1 = np.mean([X[t][(X[t].view == "c1") & (X[t].set == "NP_H")].d.mean() for t in ("np053f1dev", "np053f2dev")])
    zz = max(float(X[t][X[t].set.isin(["NP_X", "NP_N"])].d.abs().max()) for t in ("np053f1dev", "np053f2dev"))
    L.append(f"| {role} | {mb} - {ma} | {fmt(p, ci)} | {' / '.join(f'{b:+.4f}' for b in bl)} | {fmt(pc, cic)} ({st(*cic)}) | {fmt(q, ciq)} ({st(*ciq)}) | {fmt(nc, cinc)} | "
             f"{fmt(gp, cigp)} | {g1:+.4f} / {g2:+.4f} | {fmt(d2, ci2)} | {h1:+.4f} | {zz:.4f} |")
    for t in X:
        for (s, v), g in X[t].groupby(["set", "view"]):
            DET.append(dict(role=role, cmp=f"{mb}-{ma}", block=t, set=s, view=v, n=len(g), d=round(g.d.mean(), 4), up=int((g.d > 0).sum()), down=int((g.d < 0).sum())))
D = pd.DataFrame(DET); L += ["", "## per layer (stress / detail)", "", "| " + " | ".join(D.columns) + " |", "|" + "---|" * len(D.columns)]
L += ["| " + " | ".join(str(v) for v in r) + " |" for r in D.itertuples(index=False)]
open(os.path.join(HERE, "diag/r071_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L[:14]))
