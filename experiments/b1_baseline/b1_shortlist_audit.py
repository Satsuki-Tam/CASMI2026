"""Shortlist-recall audit from the molecule tables written by b1_features (truth_*_rank columns).

For reachable molecules whose truth is in the B1 window, the recall of hypothetical class-2 shortlists:
    FP top-K  ∪  (z(FP) + λ·pop) top-K  ∪  pop top-K3      (the library branch adds nothing in the class-2 view: the truth's references are hidden)
compared with the stored shortlist flag (K=100, λ=0.15, no pop branch). The union size, i.e. the forward-model cost, is measured in a real run.
Usage: python b1_shortlist_audit.py RUN[:set] ...
"""
import sys
import pandas as pd

for arg in sys.argv[1:]:
    run, _, s = arg.partition(":")
    for s in ([s] if s else ["A_timstof", "B_nplib"]):
        try: M = pd.read_csv(f"{run}/b1_molecules_{s}.csv")
        except FileNotFoundError: continue
        if "truth_fp_rank" not in M.columns: print(f"{run}/{s}: no audit columns"); continue
        R = M[M.reach_external_b1.fillna(False).astype(bool) & (M.truth_fp_rank > 0)]
        base = (R.truth_fp_rank <= 100) | (R.truth_fppop_rank <= 100)
        print(f"== {run}/{s}: reachable molecules with the truth in the window {len(R)} of {len(M)} | stored C2 shortlist recall {R.truth_in_short_c2.mean():.3f} | "
              f"reconstructed (K=100, λ=0.15) {base.mean():.3f} | truth pop rank: median {R.truth_pop_rank.median():.0f}, <=50 in {(R.truth_pop_rank <= 50).mean():.2f}")
        print("| K (FP and FP+λ·pop branches) | λ | pop branch K3 | recall |"); print("|---:|---:|---:|---:|")
        for K in (100, 150, 200, 300):
            for lam, col in ((0.15, "truth_fppop_rank"), (0.5, "truth_fppop50_rank")):
                for K3 in (0, 20, 50, 100):
                    hit = (R.truth_fp_rank <= K) | (R[col] <= K) | ((R.truth_pop_rank <= K3) if K3 > 0 else False)
                    print(f"| {K} | {lam} | {K3} | {hit.mean():.3f} |")
