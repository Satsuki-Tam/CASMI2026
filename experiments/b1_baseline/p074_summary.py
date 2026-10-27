"""074 development summary (074_prereg_p2p5ea.md), registered reading. Variant - main on the same rows (gen_eval2p output diag/p074_<tag>.csv).
Primary: 053 dev NP C2, NP_H and NP_N equal (NP_X reported), blocks f1dev / f2dev equal; tau +0.005.
Main protection (eps 0.01, three states, identity-level paired bootstrap): panel C1 clean (full_eval tables) and f1dev / f2dev NP C2 (C/D/E/F equal).
Selection: per family the max primary; among the family winners those with primary >= tau and no protection U < -eps; the max primary -> 073."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule)
FAM = {"P2": ["pcd0.5", "pcd1", "pcd2"], "EA": ["ea0.3w1", "ea0.3w2", "ea0.5w1", "ea0.5w2"], "P5": ["h2_S", "h2_prior", "h2_fp", "h2_lib", "h2_ap", "rrf_S", "rrf_prior"]}
ORA = ["o2_S", "o2_prior", "o2_fp", "o2_lib", "o2_ap"]
TAGS = ["np053f1dev", "np053f2dev", "panel", "f1dev", "f2dev", "p2dev"]
X = {}
for t in TAGS:
    p = os.path.join(HERE, f"diag/p074_{t}.csv")
    if os.path.exists(p): d = pd.read_csv(p); d["molecule"] = d.molecule.astype(str); X[t] = d
print("tables:", sorted(X))
VARS_ALL = [v for vs in FAM.values() for v in vs] + ORA
for t, d in X.items():
    miss = [v for v in VARS_ALL + ["main"] if v not in d.columns or d[v].isna().any()]
    assert not miss, (t, "missing / NaN variant columns", miss[:5])
    print(f"  {t}: rows {len(d)}, molecules {d.molecule.nunique()}, empty-candidate rows {int((d.n_cand == 0).sum())}")
def stat(frames, var):
    pts, boots = [], []
    for df, strata in frames:
        gs = [(df[df.set == s][var] - df[df.set == s].main).values for s in strata] if strata else [(df[var] - df.main).values]
        gs = [g for g in gs if len(g)]
        if not gs: continue
        pts.append(np.mean([g.mean() for g in gs])); boots.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    if not pts: return np.nan, (np.nan, np.nan), []
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(boots), axis=0), [2.5, 97.5]), pts
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo > -e else "undetermined")
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
NP4 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
L = ["# 074 development (P2 / EA / P5 variants of the 0.379 main), registered reading", "",
     "| family | variant | primary 053 NP C2 (H,N) | blocks | NP_X C2 | panel C1 clean (state) | f1/f2 NP C2 C-F (state) | panel C2 | G C1 / C2 | dev2 NP C2 | 053 NP C1 | G C1 prot3 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
res = []
for fam, vs in list(FAM.items()) + [("oracle", ORA)]:
    for v in vs:
        need = ["np053f1dev", "np053f2dev"]
        if not all(t in X for t in need): continue
        p, ci, bl = stat([(X[t][X[t].view == "c2"], ["NP_H", "NP_N"]) for t in need], v)
        px, _, _ = stat([(X[t][X[t].view == "c2"], ["NP_X"]) for t in need], v)
        if "panel" in X:
            pn = X["panel"]; pc, cic, _ = stat([(pn[(pn.view == "c1") & pn.molecule.isin(CLEAN)], None)], v); p2, _, _ = stat([(pn[pn.view == "c2"], None)], v)
        else: pc, cic, p2 = np.nan, (np.nan, np.nan), np.nan
        if all(t in X for t in ("f1dev", "f2dev")):
            q, ciq, _ = stat([(X[t][X[t].view == "c2"], NP4) for t in ("f1dev", "f2dev")], v)
            g1 = np.mean([(X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")][v] - X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")].main).mean() for t in ("f1dev", "f2dev")])
            g2 = np.mean([(X[t][(X[t].view == "c2") & (X[t].set == "G_tims_crosslib")][v] - X[t][(X[t].view == "c2") & (X[t].set == "G_tims_crosslib")].main).mean() for t in ("f1dev", "f2dev")])
        else: q, ciq, g1, g2 = np.nan, (np.nan, np.nan), np.nan, np.nan
        d2 = stat([(X["p2dev"][X["p2dev"].view == "c2"], NP4)], v)[0] if "p2dev" in X else np.nan
        c1 = stat([(X[t][X[t].view == "c1"], ["NP_H", "NP_N", "NP_X"]) for t in need], v)[0]
        if all(t in X for t in ("f1dev", "f2dev")): gc, cig, _ = stat([(X[t][(X[t].view == "c1") & (X[t].set == "G_tims_crosslib")], None) for t in ("f1dev", "f2dev")], v)
        else: gc, cig = np.nan, (np.nan, np.nan)
        res.append(dict(family=fam, variant=v, primary=p, lo=ci[0], hi=ci[1], prot1=st(*cic) if np.isfinite(pc) else "n/a", prot2=st(*ciq) if np.isfinite(q) else "n/a",
                        prot3=st(*cig) if np.isfinite(gc) else "n/a", prot1_lo=cic[0], prot1_hi=cic[1], prot2_hi=ciq[1], prot3_lo=cig[0], prot3_hi=cig[1], g_c1=gc))
        L[-1] = L[-1] + f" G C1 (prot3) {fmt(gc, cig)} ({st(*cig) if np.isfinite(gc) else 'n/a'}) |"
        L.append(f"| {fam} | {v} | {fmt(p, ci)} | {' / '.join(f'{b:+.4f}' for b in bl)} | {px:+.4f} | {fmt(pc, cic)} ({st(*cic) if np.isfinite(pc) else 'n/a'}) | "
                 f"{fmt(q, ciq)} ({st(*ciq) if np.isfinite(q) else 'n/a'}) | {p2:+.4f} | {g1:+.4f} / {g2:+.4f} | {d2:+.4f} | {c1:+.4f} |")
R = pd.DataFrame(res)
if len(R):
    STRENGTH = {"pcd0.5": 0.5, "pcd1": 1, "pcd2": 2, "ea0.3w1": 1.3, "ea0.3w2": 2.3, "ea0.5w1": 1.5, "ea0.5w2": 2.5}   # tie-break: weaker penalty first
    R["strength"] = R.variant.map(STRENGTH).fillna(0)
    cand = R[(R.family != "oracle") & (R.prot1_hi >= -0.01) & (R.prot2_hi >= -0.01) & (R.prot3_hi >= -0.01)]          # (1) no main protection with U < -eps
    win = cand.sort_values(["primary", "strength"], ascending=[False, True]).groupby("family").head(1)                  # (2) family max, ties -> weaker penalty
    ok = win[win.primary >= 0.005].sort_values(["primary", "strength"], ascending=[False, True])                          # (3) overall max with primary >= tau
    sel = ok.iloc[0] if len(ok) else None
    gate = None if sel is None else bool(sel.prot1_lo > -0.01 and sel.prot3_lo > -0.01)                                   # (4) 073 gate: panel C1 clean and G C1 lower > -0.01
    L += ["", "## selection (registered, as amended 2026-10-27 after Codex 072)", "",
          "after protection filter: " + (", ".join(cand.variant) if len(cand) else "none"),
          "family winners: " + "; ".join(f"{r.family} {r.variant} {r.primary:+.4f}" for r in win.itertuples()),
          "SELECTED: " + ("none" if sel is None else f"{sel.variant} ({sel.family}) primary {sel.primary:+.4f}"),
          "073 gate (panel C1 clean lower > -0.01 and G C1 lower > -0.01): " + ("n/a" if gate is None else ("PASS -> open 073 once" if gate else "FAIL -> do not open 073"))]
open(os.path.join(HERE, "diag/p074_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
