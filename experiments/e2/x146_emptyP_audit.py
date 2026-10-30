"""146 (Codex 146 Q1): are the expected (set, view, molecule) groups that have no P list in diag/top102_<tag>.parquet legitimately empty?
P's view candidate set = the run table rows with in_short_<view> (C2 additionally: in_tier | in_coconut | in_train_c2, the gen_eval2fd / x102 rule)
and a non-null official key. A missing group with >= 1 eligible row is a missing P output (not a legitimate empty list).
Also checks the E side: for every roster group, the E-window ledger n_e (C1 window) equals the E table's rows of the molecule, and the C2 view
frame has n_e minus the dropped truth train-only rows. Writes experiments/e2/x146_emptyP_audit.csv. No performance number."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline")
TAGS = {"np053f1dev": ("np053_f1dev", "p2_molecules.csv", ["NP_H", "NP_X", "NP_N"], "run_np053_f1dev"), "np053f2dev": ("np053_f2dev", "p2_molecules.csv", ["NP_H", "NP_X", "NP_N"], "run_np053_f2dev"),
        "f1dev": ("eval_set_f1", "p2_molecules.csv", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"], "run_f1dev"),
        "f2dev": ("eval_set_f2", "p2_molecules.csv", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"], "run_f2dev"),
        "panel": ("panel_np250", "p1_molecules.csv", ["P_np250"], "run_panel_fe")}


def main():
    rows = []; e_bad = 0; e_checked = 0
    for tag, (d, csv, sets, run) in TAGS.items():
        T = pd.read_parquet(os.path.join(B, "diag", f"top102_{tag}.parquet")); T["molecule"] = T.molecule.astype(str); have = set(zip(T.set, T.view, T.molecule))
        ev = pd.read_csv(os.path.join(B, d, csv)); ev["molecule"] = ev.molecule.astype(str)
        for s in sets:
            led = pd.read_csv(os.path.join(B, run, f"b1_molecules_{s}.csv")); led["molecule"] = led.molecule.astype(str); led = led.set_index("molecule")
            Fp = pd.read_parquet(os.path.join(B, run, f"b1_features_{s}.parquet")); Fp["molecule"] = Fp.molecule.astype(str)
            E = pd.read_parquet(os.path.join(ROOT, "experiments/e2/ewin", d, f"ewin_{s}.parquet")); E["molecule"] = E.molecule.astype(str)
            em = pd.read_csv(os.path.join(ROOT, "experiments/e2/ewin", d, f"ewin_molecules_{s}.csv")); em["molecule"] = em.molecule.astype(str); em = em.set_index("molecule")
            ecount = E.groupby("molecule").size()
            drop = E[E.in_train_c1 & ~E.in_train_c2 & ~(E.in_coconut | E.in_pcl | E.in_bio)].groupby("molecule").size()
            for x in ev[ev.set == s].molecule:
                views = ["c2"] + (["c1"] if bool(led.loc[x, "c1_usable"]) else [])
                n_e = int(em.loc[x, "n_e"]) if x in em.index else -1; n_tab = int(ecount.get(x, 0)); e_checked += 1
                if n_e != n_tab: e_bad += 1; rows.append(dict(tag=tag, set=s, view="E", molecule=x, issue=f"E ledger n_e {n_e} != table rows {n_tab}"))
                for v in views:
                    if (s, v, x) in have: continue
                    g = Fp[Fp.molecule == x]; keep = g[f"in_short_{v}"].astype(bool)
                    if v == "c2": keep &= (g.in_tier | g.in_coconut | g.in_train_c2).astype(bool)
                    elig = g[keep & g.official_key.notna()]
                    rows.append(dict(tag=tag, set=s, view=v, molecule=x, issue="P missing", eligible_rows=len(elig), eligible_keys=elig.official_key.nunique(),
                                     n_short_ledger=float(led.loc[x, f"n_short_{v}"]) if f"n_short_{v}" in led.columns else np.nan, e_rows=n_tab, e_rows_c2=n_tab - int(drop.get(x, 0))))
    A = pd.DataFrame(rows); A.to_csv(os.path.join(ROOT, "experiments/e2/x146_emptyP_audit.csv"), index=False)
    P = A[A.issue == "P missing"] if len(A) else A
    print(f"E ledger vs table: {e_checked} molecules checked, {e_bad} mismatches")
    print(f"P missing groups: {len(P)}; with eligible P candidates: {int((P.eligible_rows > 0).sum()) if len(P) else 0}")
    if len(P): print(P[["tag", "set", "view", "molecule", "eligible_rows", "eligible_keys", "n_short_ledger", "e_rows", "e_rows_c2"]].to_string(index=False))


if __name__ == "__main__":
    main()
