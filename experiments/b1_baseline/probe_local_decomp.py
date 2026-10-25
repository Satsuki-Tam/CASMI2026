"""Codex 023 local counterpart of the class-decomposition probes: for registered predictions of the evaluator (pred_<set>_<view>_<cand>_<out>.csv,
ranked SMILES lists) and the feature tables of the same run (in_train_c1 / in_train_c2 per candidate), recompute each molecule's reciprocal rank when
the final list is filtered to training structures (T) or to non-training structures (N), order unchanged. In the C1 view the truth is a training
structure (T >= main, N = 0); in the C2 view its identity is masked (N >= main, T = 0). The gain T - main (C1) / N - main (C2) is the cost of
cross-class decoys = what a perfect class gate would recover on that view.
Usage: python -X utf8 probe_local_decomp.py --eval_dir DIR --features_run RUN --cand M2x --out_name blend21 --sets S1 S2 ... [--md out.md]
"""
import argparse, os
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--eval_dir", required=True); ap.add_argument("--features_run", required=True); ap.add_argument("--cand", default="M2x")
ap.add_argument("--out_name", default="blend21"); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--md", default=""); a = ap.parse_args()
rng = np.random.default_rng(0)
def ci(d):
    d = np.asarray(d, float); idx = rng.integers(0, len(d), size=(5000, len(d))); m = d[idx].mean(1); return np.percentile(m, 2.5), np.percentile(m, 97.5)
def rr_first(flags_truth):
    for r, t in enumerate(flags_truth, 1):
        if t: return 1.0 / r if r <= 25 else 0.0
    return 0.0
lines = [f"# local class-decomposition probes ({a.cand} {a.out_name}; eval {a.eval_dir}; features {a.features_run})", "",
         "| set | view | n | main | T (train only) | N (non-train only) | gain of the view's own filter [95% CI] | molecules changed | interleave T-first | interleave N-first | Co only | Pc only | truth in COCONUT | pool (T or Co) − main [95% CI] |", "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|"]
for s in a.sets:
    f = pd.read_parquet(f"{a.features_run}/b1_features_{s}.parquet", columns=["molecule", "smiles", "official_key", "is_truth", "in_train_c1", "in_train_c2", "in_coconut"])
    for view in ("c1", "c2"):
        p = f"{a.eval_dir}/pred_{s}_{view}_{a.cand}_{a.out_name}.csv"
        if not os.path.exists(p): continue
        pr = pd.read_csv(p); fl = f.drop_duplicates(["molecule", "smiles"]).set_index(["molecule", "smiles"])
        keyt = f[f.is_truth].groupby("molecule").official_key.first().to_dict()
        rm, rt, rn, miss, it_, in_, rco, rpc, tco, rpool = [], [], [], 0, [], [], [], [], [], []
        f_truth_co = f[f.is_truth].groupby("molecule").in_coconut.any().to_dict()
        for mid, smi in zip(pr.molecule_id.astype(str), pr.smiles.astype(str)):
            lst = [x for x in smi.split(";") if x]
            tr, ist, co = [], [], []
            for x in lst:
                if (mid, x) in fl.index:
                    row = fl.loc[(mid, x)]; tr.append(bool(row[f"in_train_{view}"])); ist.append(bool(row["is_truth"])); co.append(bool(row["in_coconut"]))
                else: tr.append(None); ist.append(False); co.append(False); miss += 1
            rm.append(rr_first(ist))
            rt.append(rr_first([t for t, q in zip(ist, tr) if q is True])); rn.append(rr_first([t for t, q in zip(ist, tr) if q is False]))
            T_ = [t for t, q in zip(ist, tr) if q is True]; N_ = [t for t, q in zip(ist, tr) if q is not True]
            def inter(A, B):
                out = []
                for i in range(max(len(A), len(B))):
                    if i < len(A): out.append(A[i])
                    if i < len(B): out.append(B[i])
                return out
            it_.append(rr_first(inter(T_, N_))); in_.append(rr_first(inter(N_, T_)))
            rco.append(rr_first([t for t, q, c in zip(ist, tr, co) if q is False and c])); rpc.append(rr_first([t for t, q, c in zip(ist, tr, co) if q is False and not c]))
            rpool.append(rr_first([t for t, q, c in zip(ist, tr, co) if q is True or c]))
            tco.append(any(t and c for t, c in zip(ist, co)) or bool(f_truth_co.get(mid, False)))
        rm, rt, rn, it_, in_, rco, rpc, tco, rpool = map(np.array, (rm, rt, rn, it_, in_, rco, rpc, tco, rpool)); dpool = rpool - rm; plo, phi = ci(dpool); own = rt if view == "c1" else rn; d = own - rm; lo, hi = ci(d)
        lines.append(f"| {s} | {view} | {len(rm)} | {rm.mean():.3f} | {rt.mean():.3f} | {rn.mean():.3f} | {d.mean():+.3f} [{lo:+.3f}, {hi:+.3f}] | {int((d != 0).sum())} | {it_.mean():.3f} | {in_.mean():.3f} | {rco.mean():.3f} | {rpc.mean():.3f} | {tco.mean():.2f} | {dpool.mean():+.3f} [{plo:+.3f}, {phi:+.3f}] |" + (f" (unmatched SMILES {miss})" if miss else ""))
text = "\n".join(lines); print(text)
if a.md: open(a.md, "w", encoding="utf-8").write(text + "\n")
