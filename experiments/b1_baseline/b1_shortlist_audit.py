"""Shortlist-recall audit from the molecule tables written by b1_features (Codex 008 Q2).

For every molecule of a set: the stored class-2 shortlist (FP top-100 ∪ (z(FP)+0.15·pop) top-100 ∪ library top-20) and hypothetical
allocations measured in the same window without forward models:
    fp200        : FP branch 200           fpp200 : FP+prior branch 200       fp200_fpp200 : both branches 200
    pop50/pop100 : stored + prior-only branch 50/100                           fpp200_pop50 : FP+prior 200 + prior 50
Reported per allocation: truth recall over ALL N molecules and over the reachable ones, mean/max candidate count, predicted forward jobs
(≈ candidates × query spectra), and the literature popularity of the truths newly recovered. Usage: python b1_shortlist_audit.py RUN[:set] ...
"""
import sys
import numpy as np, pandas as pd

ALLOC = ["fp200", "fpp200", "fp200_fpp200", "pop50", "pop100", "fpp200_pop50"]

for arg in sys.argv[1:]:
    run, _, s = arg.partition(":")
    for s in ([s] if s else ["A_timstof", "B_nplib"]):
        try: M = pd.read_csv(f"{run}/b1_molecules_{s}.csv")
        except FileNotFoundError: continue
        if "truth_in_short_fp200" not in M.columns: print(f"{run}/{s}: no audit columns"); continue
        N = len(M); reach = M.reach_external_b1.fillna(False).astype(bool); R = M[reach]
        base = M.truth_in_short_c2.fillna(False).astype(bool)
        print(f"\n== {run}/{s}: N={N}, reachable {int(reach.sum())}, truth in window {int((M.truth_in_window.fillna(False).astype(bool)).sum())} | "
              f"stored C2 shortlist: recall all-N {base.mean():.3f}, reachable {base[reach].mean():.3f}, mean size {M.n_short_c2.mean():.0f}, jobs ≈ {(M.n_short_c2 * M.n_query).sum():,.0f}")
        print("| allocation | recall all-N | recall reachable | newly recovered (reachable) | lost | mean size | max size | jobs ≈ cands × spectra | pop>0 among recovered |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for a in ALLOC:
            hit = M[f"truth_in_short_{a}"].fillna(False).astype(bool); n = M[f"n_short_{a}"]
            new = (hit & ~base & reach); lost = (~hit & base & reach)
            pop_new = "-" if new.sum() == 0 else f"{int((M.loc[new, 'truth_fp_rank'] > 0).sum())}/{int(new.sum())} in window"
            print(f"| {a} | {hit.mean():.3f} | {hit[reach].mean():.3f} | {int(new.sum())} | {int(lost.sum())} | {n.mean():.0f} | {int(n.max())} | {(n * M.n_query).sum():,.0f} | {pop_new} |")
        # where the window ranks the truth (reachable molecules with the truth in the window)
        W = R[R.truth_fp_rank > 0]
        if len(W):
            q = lambda c: " / ".join(f"{x:.0f}" for x in np.percentile(W[c], [25, 50, 75, 90]))
            print(f"truth window ranks (reachable, n={len(W)}; p25/p50/p75/p90): FP {q('truth_fp_rank')} | FP+0.15pop {q('truth_fppop_rank')} | FP+0.5pop {q('truth_fppop50_rank')} | pop {q('truth_pop_rank')}")
