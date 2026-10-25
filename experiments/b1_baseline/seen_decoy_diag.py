"""Codex 024 Q1 (diagnostic): are the decoys that outrank the truth disproportionately FPNet-SEEN structures? For fold-0 development molecules
(truth unseen by the fold-safe fold-0 FPNet), split every candidate of the saved top-25 lists into: truth / seen training structure (identity fold 1-4,
not a panel NP group = trained by fpnet_fold0) / unseen training structure (identity fold 0 or panel group) / non-training (PubChem or COCONUT only).
Compares the share of each group among decoys ranked ABOVE the truth with its share among all shortlist candidates of the view, and the FP z-score
(within molecule) of seen vs unseen training decoys.
Usage: python -X utf8 seen_decoy_diag.py --eval_dir DIR --features_run RUN --sets S1 ... [--cand M2x] [--md out.md]
"""
import argparse, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
ap = argparse.ArgumentParser(); ap.add_argument("--eval_dir", required=True); ap.add_argument("--features_run", required=True); ap.add_argument("--sets", nargs="+", required=True)
ap.add_argument("--cand", default="M2x"); ap.add_argument("--md", default=""); ap.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap.add_argument("--split", default="data/external/fold_safe_fpnet/split.parquet"); ap.add_argument("--structs", default="data/external/v2_pool/train_structs.parquet"); a = ap.parse_args()
# seen by fpnet_fold0 = training structure whose sid is NOT in the fold-0 model's exclusion list (fold 0 'hold' + panel 'np'), keyed by the pool key
ts = pq.read_table(a.structs, columns=["sid", "key"]).to_pandas(); ex = set(pq.read_table(a.split).to_pandas().sid.astype(int))
seen_keys = set(ts.loc[~ts.sid.astype(int).isin(ex), "key"].astype(str)); unseen_train_keys = set(ts.loc[ts.sid.astype(int).isin(ex), "key"].astype(str)) - seen_keys
print(f"fold-0 FPNet: {len(seen_keys):,} seen training keys, {len(unseen_train_keys):,} unseen training keys")
lines = [f"# FPNet-seen decoys above the truth ({a.cand} blend21, {a.eval_dir}, features {a.features_run})", "",
         "| set | view | n mol | shortlist share seen / unseen-train / non-train | above-truth decoys | share seen / unseen-train / non-train | FP z: seen vs unseen-train decoys |",
         "|---|---|---:|---|---:|---|---|"]
for s in a.sets:
    f = pd.read_parquet(f"{a.features_run}/b1_features_{s}.parquet", columns=["molecule", "smiles", "official_key", "is_truth", "in_short_c1", "in_short_c2", "in_train_c1", "in_train_c2", "fp"])
    f["molecule"] = f.molecule.astype(str)
    for view in ("c1", "c2"):
        p = f"{a.eval_dir}/pred_{s}_{view}_{a.cand}_blend21.csv"
        if not os.path.exists(p): continue
        g = f[f[f"in_short_{view}"]].copy()
        g["grp"] = np.where(g.is_truth, "truth", np.where(g[f"in_train_{view}"] & g.official_key.astype(str).isin(seen_keys), "seen",
                    np.where(g[f"in_train_{view}"], "unseen_train", "nontrain")))
        g["fpz"] = g.groupby("molecule").fp.transform(lambda x: (x - x.mean()) / (x.std(ddof=1) + 1e-9))
        base = g[g.grp != "truth"].grp.value_counts(normalize=True)
        look = g.drop_duplicates(["molecule", "smiles"]).set_index(["molecule", "smiles"])
        above = []
        for mid, smi in zip(pd.read_csv(p).molecule_id.astype(str), pd.read_csv(p).smiles.astype(str)):
            for x in [y for y in smi.split(";") if y]:
                if (mid, x) not in look.index: continue
                r = look.loc[(mid, x)]
                if r.grp == "truth": break
                above.append((r.grp, float(r.fpz)))
        A = pd.DataFrame(above, columns=["grp", "fpz"]); sh = A.grp.value_counts(normalize=True) if len(A) else pd.Series(dtype=float)
        dz = g[g.grp.isin(["seen", "unseen_train"])].groupby("grp").fpz.mean()
        lines.append(f"| {s} | {view} | {g.molecule.nunique()} | {base.get('seen', 0):.2f} / {base.get('unseen_train', 0):.2f} / {base.get('nontrain', 0):.2f} | {len(A)} | "
                     f"{sh.get('seen', 0):.2f} / {sh.get('unseen_train', 0):.2f} / {sh.get('nontrain', 0):.2f} | {dz.get('seen', float('nan')):+.2f} vs {dz.get('unseen_train', float('nan')):+.2f} |")
text = "\n".join(lines); print(text)
if a.md: open(a.md, "w", encoding="utf-8").write(text + "\n")
