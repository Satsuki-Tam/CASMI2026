"""Codex 033 Q4 audit: joint outcomes of the registered main list and the twin (best library match of the view) on the SAME molecules.

Regimes are kept apart (no substitution): panel C1 clean 202 / uncertain 48 (fixed CSV sha 961ceb94) under full_eval = identity seen, query unseen
(hidden class 1 of the working baseline); the same molecules under fold-0 = identity unseen; dev2 strata C1 (identity unseen under both FPNets);
C2 views (truth references hidden) for the loss side.
Per row: n; the 2x2 of (main rank-1 correct) x (twin is the truth); the RR change of the fixed twin rule twin1m_t0.7_m0.1 split into rescued
(main RR < 1 and twin correct, the rule fired) and harmed (rule fired on a wrong twin); and the same by twin-similarity bins.
Usage: python -X utf8 twin_joint_audit.py --out diag/twin_joint_audit.md
"""
import argparse, numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="diag/twin_joint_audit.md"); ap.add_argument("--rule", default="twin1m_t0.7_m0.1")
ap.add_argument("--audit_csv", default="../fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv")
a = ap.parse_args()
grp = pd.read_csv(a.audit_csv).set_index("molecule").audit_group
TAB = {cfg: pd.concat([pd.read_csv(f"diag/gf2_{cfg}_{p}.csv") for p in ("panel", "p2dev")], ignore_index=True) for cfg in ("fe", "m2x")}
for T in TAB.values():
    T["molecule"] = T["molecule"].astype(str)
    for c in ("main", "twin_only", a.rule, "twin_sim", "lib_2nd", "twin_rank"): T[c] = T[c].fillna(0.0)


def block(T, sel, label):
    g = T[sel]
    if not len(g): return []
    m1 = g["main"] >= 1.0 - 1e-9; tw = g["twin_only"] >= 1.0 - 1e-9; d = g[a.rule] - g["main"]; fired = (g[a.rule] != g["main"]) | ((g["twin_rank"] > 1) & (g["twin_sim"] >= 0.7) & (g["twin_sim"] - g["lib_2nd"] >= 0.1))
    resc = d[(d > 0)]; harm = d[(d < 0)]
    return [f"| {label} | {len(g)} | {g['main'].mean():.3f} | {g[a.rule].mean():.3f} | {d.mean():+.4f} | {int((m1 & tw).sum())} | {int((~m1 & tw).sum())} | {int((m1 & ~tw).sum())} | {int((~m1 & ~tw).sum())} | "
            f"{len(resc)} / {resc.sum():+.2f} | {len(harm)} / {harm.sum():+.2f} |"]


H = ["| regime | n | main | rule | Δ mean | main@1 & twin✓ | main✗ & twin✓ | main@1 & twin✗ | both ✗ | rescued n / ΣΔ | harmed n / ΣΔ |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|"]
L = [f"# Twin joint audit (Codex 033 Q4), rule {a.rule}", "", "main@1 = registered main list has the truth at rank 1; twin✓ = the best library match is the truth. ΣΔ = summed RR change (divide by n for the mean).", ""]
pan = lambda T, v, gname: (T.set == "P_np250") & (T.view == v) & T.molecule.map(grp).eq(gname)
for cfg, desc in (("fe", "full_eval (panel identities seen, queries unseen; dev2 identities unseen)"), ("m2x", "fold-0 (panel and dev2 identities unseen)")):
    T = TAB[cfg]; L += [f"## {desc}", ""] + H
    for v in ("c1", "c2"):
        L += block(T, pan(T, v, "clean_nearest_lt_0.90"), f"panel {v.upper()} clean")
        L += block(T, pan(T, v, "uncertain_nearest_ge_0.90"), f"panel {v.upper()} uncertain")
    for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"):
        for v in ("c1", "c2"):
            L += block(T, (T.set == s) & (T.view == v), f"dev2 {s[0]} {v.upper()}")
    L += [""]
# similarity bins of the twin, panel clean C1 (fe) vs dev2 G C1 (fe) vs C2 views (fe, all dev2 + panel)
L += ["## By twin similarity (full_eval tables)", "", "| regime | twin sim bin | n | twin correct share | main@1 share | Δ rule mean |", "|---|---|---:|---:|---:|---:|"]
T = TAB["fe"]; bins = [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
for label, sel in (("panel C1 clean", pan(T, "c1", "clean_nearest_lt_0.90")), ("dev2 G C1", (T.set == "G_tims_crosslib") & (T.view == "c1")),
                   ("dev2 C/E/F C1", T.set.isin(["C_np_crosslib", "E_np_negonly", "F_np_uncovered"]) & (T.view == "c1")), ("all C2 (panel + dev2)", T.view == "c2")):
    g = T[sel].copy(); g["bin"] = pd.cut(g.twin_sim, bins, right=False)
    for b, h in g.groupby("bin", observed=True):
        L.append(f"| {label} | {b} | {len(h)} | {(h.twin_only >= 1).mean():.2f} | {(h.main >= 1).mean():.2f} | {(h[a.rule] - h.main).mean():+.3f} |")
open(a.out, "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))
