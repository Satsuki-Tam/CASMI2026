"""067 reading (067_prereg_fpnet_mix.md + Codex 068 addendum). locked2 v2 (fold 0, 500 molecules, opened once): A = full_eval tables,
B = public fold0 tables, C = 0.5F + 0.5 fold0 logit mix; rank_v4b + anaw0.5 main fixed (gen_eval2 --parents 0). Panel C1 clean: A = full_eval
panel tables (diag/r047_rank_v4b_panel.csv), C = mix panel tables (diag/m067_panel_C.csv).
Adoption target = C only. PASS = NP C2 (C/D/E/F equal) C - A point > 0 AND lower bound > -0.01 AND panel C1 clean C - A lower bound > -0.01."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule)
L2 = {k: pd.read_csv(os.path.join(HERE, f"diag/m067_l2_{k}.csv")) for k in "ABC"}
ev = pd.read_csv(os.path.join(HERE, "locked_eval2/v2/p2_molecules.csv")); ids = set(ev.molecule.astype(str))
for k, d in L2.items():
    d["molecule"] = d.molecule.astype(str)
    print(f"{k}: rows {len(d)} | molecules {d.molecule.nunique()} (expected {len(ids)}, missing {len(ids - set(d.molecule))}) | views {d.view.value_counts().to_dict()}")
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
def pair(a, b):
    x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_a", "_b")); x["d"] = x.main_b - x.main_a; return x
def stat(df, strata):
    gs = [df[df.set == s].d.values for s in strata] if strata else [df.d.values]; gs = [g for g in gs if len(g)]
    p = float(np.mean([g.mean() for g in gs])); bt = np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)])
    return p, np.percentile(bt, [2.5, 97.5])
out = ["# 067 reading (locked2 opened once)", ""]
for nm, (a, b) in {"C - A": ("A", "C"), "B - A": ("A", "B")}.items():
    x = pair(L2[a], L2[b]); c2 = x[x.view == "c2"]
    p, ci = stat(c2, NP)
    out.append(f"- {nm}: NP C2 (C/D/E/F equal) {p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}] | n per set {c2[c2.set.isin(NP)].groupby('set').size().to_dict()}")
    for s in NP + ["G_tims_crosslib"]:
        for v in ("c2", "c1"):
            g = x[(x.set == s) & (x.view == v)]
            if len(g): out.append(f"    {s} {v}: n {len(g)} {g.main_a.mean():.4f} -> {g.main_b.mean():.4f} ({g.d.mean():+.4f}; up {int((g.d > 0).sum())} / down {int((g.d < 0).sum())})")
pa = pd.read_csv(os.path.join(HERE, "diag/r047_rank_v4b_panel.csv")); pc = pd.read_csv(os.path.join(HERE, "diag/m067_panel_C.csv"))
xp = pair(pa, pc); c1 = xp[(xp.view == "c1") & xp.molecule.isin(CLEAN)]; pp, cip = stat(c1, None)
c2p = xp[xp.view == "c2"]
out.append(f"- panel C1 clean (n {len(c1)}): C - A {pp:+.4f} [{cip[0]:+.4f}, {cip[1]:+.4f}] | panel C2 (identity seen by F) {c2p.d.mean():+.4f} | panel C1 all {xp[xp.view == 'c1'].d.mean():+.4f}")
x = pair(L2["A"], L2["C"]); p, ci = stat(x[x.view == "c2"], NP)
verdict = (p > 0) and (ci[0] > -0.01) and (cip[0] > -0.01)
out.append(f"- REGISTERED VERDICT (C only): {'PASS' if verdict else 'FAIL'} (point > 0: {p > 0}; lower > -0.01: {ci[0] > -0.01}; panel C1 clean lower > -0.01: {cip[0] > -0.01})")
open(os.path.join(HERE, "diag/x067_summary.md"), "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
