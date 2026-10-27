"""072 error anatomy (exploratory, not a registered test): NP_H dev (COCONUT-listed truths, ranker path), current main (rank_v4b, anaw0.5).
For C2 misses: what kind of candidate takes rank 1 (library-referenced train structure? COCONUT? more popular?) and could an
'explained-away' signal (candidate has library spectra but they do not match the query) demote it; in C1, how often the truth itself
has low library similarity (the cost side)."""
import sys, os, numpy as np, pandas as pd
BLOCKS = [k for k in (1, 2) if os.path.exists(f"diag/e072_top_v4b_np053f{k}dev.parquet")]; print("blocks", BLOCKS)
T = pd.concat([pd.read_parquet(f"diag/e072_top_v4b_np053f{k}dev.parquet").assign(block=f"f{k}") for k in BLOCKS], ignore_index=True)
for v in ("c2", "c1"):
    t = T[T.view == v]; mol = t.groupby(["block", "molecule"])
    tr = t[t.is_truth].groupby(["block", "molecule"])["rank"].min()
    n = mol.ngroups; hit1 = int((tr == 1).sum()); intop10 = int((tr <= 10).sum())
    print(f"\n== view {v}: molecules {n}, truth rank1 {hit1} ({hit1 / n:.3f}), truth in top10 {intop10}, truth listed (any rank) {len(tr)}, MRR@25 approx {float((1 / tr[tr <= 25]).sum() / n):.4f}")
    gl = t.groupby(["block", "molecule"]).gl_ok.first(); print("   gl_ok share", round(float(gl.mean()), 3))
    w = t[(t["rank"] == 1)].set_index(["block", "molecule"])
    miss = w[~w.is_truth]
    print(f"   misses with a wrong rank-1: {len(miss)}")
    if len(miss):
        print("   winner: in_train %.3f | lib_nref>0 %.3f | lib_sim>0 %.3f | lib_sim median (if >0) %.3f | in_coconut %.3f | pop median %.2f" % (
            miss.in_train.mean(), (miss.lib_nref > 0).mean(), (miss.lib_sim > 0).mean(), miss.lib_sim[miss.lib_sim > 0].median() if (miss.lib_sim > 0).any() else np.nan,
            miss.in_coconut.mean(), miss["pop"].median()))
        tt = t[t.is_truth].set_index(["block", "molecule"]).reindex(miss.index)
        print("   truth (same molecules): listed %.3f | in_coconut %.3f | pop median %.2f | rank median %.0f" % (tt["rank"].notna().mean(), tt.in_coconut.mean(), tt["pop"].median(), tt["rank"].median()))
        ea = miss[(miss.lib_nref > 0) & (miss.lib_sim < 0.5)]
        print(f"   'explained-away' winners (has refs, lib_sim < 0.5): {len(ea)} of {len(miss)}; of those truth at rank 2: {int((tt.loc[ea.index, 'rank'] == 2).sum())}")
        for thr in (0.3, 0.5, 0.7):
            print(f"     winners with refs and lib_sim < {thr}: {int(((miss.lib_nref > 0) & (miss.lib_sim < thr)).sum())}")
        print("   winner pop - truth pop: median %.2f, share winner more popular %.3f" % (float((miss["pop"] - tt["pop"]).median()), float((miss["pop"] > tt["pop"]).mean())))
        print("   winner glz - truth glz: median %.2f | winner fp_rank_window median %.0f vs truth %.0f" % (float((miss.glz - tt.glz).median()), miss.fp_rank_window.median(), tt.fp_rank_window.median()))
    if v == "c1":
        tt1 = t[t.is_truth]
        print("   C1 truth lib_sim quantiles:", np.round(tt1.lib_sim.quantile([0.1, 0.25, 0.5, 0.75]).values, 3), "| share < 0.5:", round(float((tt1.lib_sim < 0.5).mean()), 3), "| lib_nref>0:", round(float((tt1.lib_nref > 0).mean()), 3))
# rank-1..10 composition in C2 (all molecules): how many referenced train structures sit above the truth
t = T[T.view == "c2"]
above = []
for (b, m), g in t.groupby(["block", "molecule"]):
    r = g[g.is_truth]["rank"].min() if g.is_truth.any() else 99
    a = g[(g["rank"] < r)]
    above.append(dict(block=b, molecule=m, truth_rank=r, n_above=len(a), above_ref=int((a.lib_nref > 0).sum()), above_ref_lowsim=int(((a.lib_nref > 0) & (a.lib_sim < 0.5)).sum()),
                      above_coco=int(a.in_coconut.sum()), above_tier_only=int((a.in_tier & ~a.in_coconut & ~a.in_train).sum())))
A = pd.DataFrame(above); A = A[A.truth_rank.between(2, 10)]
print(f"\n== C2, truth at ranks 2-10 (n={len(A)}): candidates above the truth: total {A.n_above.sum()}, with refs {A.above_ref.sum()}, refs & lib_sim<0.5 {A.above_ref_lowsim.sum()}, "
      f"COCONUT {A.above_coco.sum()}, tier-only (Pc) {A.above_tier_only.sum()}")
print("   molecules where ALL candidates above the truth are 'refs & lib_sim<0.5':", int(((A.n_above > 0) & (A.above_ref_lowsim == A.n_above)).sum()),
      "| where all above are Pc-only:", int(((A.n_above > 0) & (A.above_tier_only == A.n_above)).sum()))
