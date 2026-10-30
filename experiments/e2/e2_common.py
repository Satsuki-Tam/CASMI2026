"""143 E2 shared code (fixed before any E2 result was read): the per-view feature frame of one set's E-window table (b1_ewin.py) joined
with its e2_feats.py table, the training-group rule and the ranking helper. e2_train.py and e2_eval.py use exactly this code.
View windows: C1 = every E-window row; C2 = every row except the truth's train-only rows (the truth key or a train alias of it -- the rows
whose train flag the C2 view removed -- that are in no other E source): in the C2 premise the truth is not a train structure, so a truth
that is only a train structure is outside the E window (unreachable, as in the P views).
Features: no popularity, no GL, no source flag except the view's train flag (needed to read the library features)."""
import numpy as np, pandas as pd

ANA = ("ap", "a1", "best_tan", "top_tan", "mean_tan")
FEATS = ["fp", "fp_rank", "fp_z", "fp_gap", "log_n", "ppm_err", "in_train", "lib_sim", "lib_same", "lib_nref", "lib_gap",
         "frag", "frag_rank", "frag_gap"] + [f"ana_{f}" for f in ANA] + ["ana_ap_rank", "ana_ap_gap"]


def view_frame(E, F, view):
    """E: ewin_<set>.parquet rows, F: e2f_<set>.parquet rows (same set), view 'c1' / 'c2' -> one row per (molecule, official key) of the view window."""
    if view not in ("c1", "c2"): raise ValueError(view)
    D = E.merge(F, on=["set", "molecule", "official_key"], how="left", validate="one_to_one")
    if D.frag.isna().any(): raise SystemExit(f"STOP: {int(D.frag.isna().sum())} E-window rows without an e2_feats row")
    if view == "c2": D = D[~(D.in_train_c1 & ~D.in_train_c2 & ~(D.in_coconut | D.in_pcl | D.in_bio))]
    D = D.reset_index(drop=True); v = view
    X = D[["set", "molecule", "official_key", "smiles", "is_truth", "in_coconut", "in_pcl", "in_bio"]].copy()
    X["gk"] = X.set.astype(str) + "|" + X.molecule.astype(str); G = lambda c: X.groupby("gk", sort=False)[c]
    X["fp"] = D.fp.astype(float).values; X["fp"] = X.fp.fillna(G("fp").transform("min") - 1.0).fillna(0.0)
    X["log_n"] = np.log(G("fp").transform("size").astype(float))
    X["fp_rank"] = G("fp").rank(ascending=False, method="min")
    X["fp_z"] = (X.fp - G("fp").transform("mean")) / (G("fp").transform("std").fillna(0.0) + 1e-6)
    X["fp_gap"] = X.fp - G("fp").transform("max")
    X["ppm_err"] = D.ppm_err.astype(float).values; X["in_train"] = D[f"in_train_{v}"].astype(float).values
    for f in ("sim", "same", "nref"): X[f"lib_{f}"] = D[f"lib_{f}_{v}"].astype(float).values
    X["lib_gap"] = X.lib_sim - G("lib_sim").transform("max")
    X["frag"] = D.frag.astype(float).values; X["frag_rank"] = G("frag").rank(ascending=False, method="min"); X["frag_gap"] = X.frag - G("frag").transform("max")
    for f in ANA: X[f"ana_{f}"] = D[f"ana_{f}_{v}"].astype(float).values
    X["ana_ap_rank"] = G("ana_ap").rank(ascending=False, method="min"); X["ana_ap_gap"] = X.ana_ap - G("ana_ap").transform("max")
    X["view"] = v
    return X


def train_groups(X):
    """Training groups of a view frame: C2 = truth inside the view window; C1 = truth inside with >= 1 library reference after the exclusions."""
    t = X[X.is_truth]
    ok = set(t.gk) if X.view.iloc[0] == "c2" else set(t.gk[t.lib_nref > 0])
    return X[X.gk.isin(ok)]


def rank_lists(X, score):
    """Ranks inside each gk by score desc, ties -> fp desc -> official key."""
    X = X.assign(score=np.asarray(score, float)).sort_values(["gk", "score", "fp", "official_key"], ascending=[True, False, False, True], kind="mergesort")
    X["rank"] = X.groupby("gk", sort=False).cumcount() + 1
    return X


def rr_of(R):
    """Reciprocal rank@25 of the truth per gk (groups without a truth row are absent)."""
    t = R[R.is_truth]
    return pd.Series(np.where(t["rank"].values <= 25, 1.0 / t["rank"].values, 0.0), index=t.gk.values)
