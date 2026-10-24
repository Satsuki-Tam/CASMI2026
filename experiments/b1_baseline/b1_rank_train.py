"""B1 step 3 -- learned fusion (LightGBM LambdaRank) on the unified candidate table, compared with the fixed rule on the same molecules.

Training rows: shortlist candidates of molecules in the FIT groups of the given runs, under both scenario views (C2 and, where
possible, C1) -- the two views of one molecule are one 'identity' and always stay in the same split. Features are molecule-relative
(z within the shortlist) plus raw values and flags; the label is is_truth. Model selection (num_leaves / learning rate / rounds) uses
the TUNE groups; the EVAL groups are scored once with the selected setting and reported next to the fixed rules S(2,1,0.5) (reference) and S(2,1,0.15).
Usage: python -X utf8 b1_rank_train.py --runs RUN:eval_csv[:group_override] ... [--out DIR]   (e.g. run_p1:...:fit uses all P1 molecules as fit)
       e.g. --runs experiments/b1_baseline/run1:experiments/b1_baseline/eval_set/p1_molecules.csv experiments/b1_baseline/run_c1:...
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
import lightgbm as lgb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_evaluate import z, rr, boot, term, LAM
from b1_rankfeats import FEATS, FEATSETS, MONO, feature_matrix



def load_run(run, eval_csv, group_override=None, feats=FEATS):
    ev = pd.read_csv(eval_csv).set_index("molecule")
    out = []
    for s in ("A_timstof", "B_nplib"):
        fp_ = f"{run}/b1_features_{s}.parquet"
        if not os.path.exists(fp_): continue
        F = pd.read_parquet(fp_); M = pd.read_csv(f"{run}/b1_molecules_{s}.csv").set_index("molecule")
        def load(model):
            p = f"{run}/work/{model}_{s}.json"
            try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
            except Exception: ok = False
            return (json.load(open(p)) if ok else {}), ok
        gl, gl_ok = load("gl"); ice, ice_ok = load("ice")
        LEDGER[(run, s)] = M.copy()
        for mid, g0 in F.groupby("molecule", sort=False):
            if mid not in M.index: continue
            m = M.loc[mid]
            for view in ("c2", "c1"):
                if view == "c1" and not bool(m["c1_usable"] if "c1_usable" in M.columns else m.c1_possible): continue
                # class-2 view: a structure that exists in no external source and whose train membership is hidden would not be a candidate
                # for a genuinely novel-to-libraries molecule -> drop it (otherwise 'no source flags' identifies the truth = leak)
                keep = g0[f"in_short_{view}"].values.astype(bool) if f"in_short_{view}" in g0.columns else np.ones(len(g0), bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0[f"in_train_{view}"].values).astype(bool)
                g = g0[keep].reset_index(drop=True)
                if len(g) == 0: continue
                fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                zfp = z(fp); zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
                lib = g[f"lib_sim_{view}"].values.astype(float); top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
                S = zfp + (2 * zgl if zgl is not None else 0) + (zice if zice is not None else 0) + 0.5 * pop
                S15 = zfp + (2 * zgl if zgl is not None else 0) + (zice if zice is not None else 0) + LAM * pop
                X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values,
                                   lib, g[f"lib_same_{view}"].values, g[f"lib_nref_{view}"].values, g.in_tier.values, g[f"in_train_{view}"].values, g.in_coconut.values,
                                   g.ppm_err.values, g.fp_rank_window.values, float(m.n_query), float(m.ce_known),
                                   n_window=float(m["n_unique"]) if "n_unique" in M.columns and np.isfinite(float(m["n_unique"])) else np.nan, feats=feats)
                d = pd.DataFrame(X, columns=feats)
                d.insert(0, "is_truth", g.is_truth.values.astype(int)); d.insert(0, "identity", mid); d.insert(0, "group", group_override or m.group); d.insert(0, "view", view)
                d.insert(0, "molecule", mid); d.insert(0, "set", s); d.insert(0, "run", run)
                d["S_fixed"] = S; d["S_fixed15"] = S15; d["reachable"] = bool(m["reach_external_b1"]) if "reach_external_b1" in M.columns else (bool(ev.loc[mid, "window_external"]) if mid in ev.index else True)
                d["identity_group"] = int(m["identity_group"]) if "identity_group" in M.columns else -1
                out.append(d)
    return pd.concat(out, ignore_index=True)


LEDGER = {}   # (run, set) -> molecule table (reach / c1 flags), filled by load_run; molecules without candidate rows count as 0


def mrr_of(df, score_col):
    vals = []
    for (mid, view), g in df.groupby(["molecule", "view"], sort=False):
        r, _ = rr(g[score_col].values, g.is_truth.values.astype(bool)); vals.append((mid, view, r, bool(g.reachable.iloc[0])))
    d = pd.DataFrame(vals, columns=["molecule", "view", "rr", "reach"])
    groups = set(df.group.unique()); runs = set(zip(df.run, df.set)); have = set(zip(d.molecule, d.view)); missing = []
    for (run, s), L in LEDGER.items():
        if (run, s) not in runs: continue
        for mid, row in L[L.group.isin(groups)].iterrows():
            if (mid, "c2") not in have: missing.append((mid, "c2", 0.0, bool(row.get("reach_external_b1", True))))
            if bool(row.get("c1_usable", row.get("c1_possible", False))) and (mid, "c1") not in have: missing.append((mid, "c1", 0.0, True))
    if missing: d = pd.concat([d, pd.DataFrame(missing, columns=d.columns)], ignore_index=True)
    res = {}
    for view, gg in d.groupby("view"):
        res[view] = dict(mrr=float(gg.rr.mean()), n=len(gg), strict=float((gg.rr * (gg.reach | (view == "c1"))).mean()))
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--out", default="experiments/b1_baseline/rank")
    ap.add_argument("--feats", default="v2", choices=sorted(FEATSETS), help="feature set (v2 = 28 features; v3 adds per-model confidence/rank/window features)")
    ap.add_argument("--monotone", action="store_true", help="monotone constraints (scores/similarities up, ranks/|ppm| down)")
    ap.add_argument("--drop", nargs="*", default=[], help="features removed from the set (e.g. lib_nref in_train: pure 'is a library compound' identity, see diag 2026-10-25 panel probe)")
    ap.add_argument("--c1_repeat", type=int, default=1, help="replicate the class-1-view fit groups this many times (the C2 view hides every reference of the truth, so without "
                    "re-weighting the ranker learns 'has references -> decoy' from the C2 majority)")
    ap.add_argument("--c2_nolib", action="store_true", help="zero every library feature in the C2-view fit rows (the C2 view hides the truth's references, so there "
                    "'has a reference' is a perfect negative label; with this flag the use of reference evidence is learned from the C1 rows only)")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); FE = [f for f in FEATSETS[a.feats] if f not in set(a.drop)]
    print("features:", len(FE), "| dropped:", a.drop, "| c1_repeat:", a.c1_repeat, "| c2_nolib:", a.c2_nolib)
    data = pd.concat([load_run(*r.split(":"), feats=FE) for r in a.runs], ignore_index=True)   # RUN:eval_csv[:group_override]
    print("rows", len(data), "| molecules", data.molecule.nunique(), "| groups", data.groupby("group").molecule.nunique().to_dict(), "| views", data.groupby("view").molecule.nunique().to_dict())
    fit, tune, ev = (data[data.group == g].copy() for g in ("fit", "tune", "eval"))
    ig = {g: set(data[(data.group == g) & (data.identity_group >= 0)].identity_group) for g in ("fit", "tune", "eval")}
    assert not (ig["fit"] & ig["tune"]) and not (ig["fit"] & ig["eval"]) and not (ig["tune"] & ig["eval"]), "identity groups shared between fit/tune/eval"
    print("identity groups:", {g: len(v) for g, v in ig.items()})
    # keep only training groups whose shortlist contains the truth (ranking loss needs a positive); evaluation keeps every molecule
    def groups_with_truth(d):
        has = d.groupby(["molecule", "view"]).is_truth.transform("max") > 0; return d[has]
    fit_t = groups_with_truth(fit)
    if a.c2_nolib:
        LIBF = [f for f in ("lib_sim", "lib_same", "lib_nref", "lib_margin", "lib_max_mol", "in_train", "lib_rank", "in_train_x_lib") if f in FE]
        fit_t = fit_t.copy(); fit_t.loc[fit_t.view == "c2", LIBF] = 0.0; print("c2 fit rows: library features zeroed:", LIBF)
    if a.c1_repeat > 1:
        c1 = fit_t[fit_t.view == "c1"]
        fit_t = pd.concat([fit_t] + [c1.assign(molecule=c1.molecule.astype(str) + f"#r{k}") for k in range(1, a.c1_repeat)], ignore_index=True)
        print("fit groups after c1 replication:", fit_t.groupby(["molecule", "view"]).ngroups, "| c1 share:", round(float((fit_t.groupby(['molecule', 'view']).view.first() == 'c1').mean()), 3))
    def to_ds(d):
        d = d.sort_values(["molecule", "view"], kind="stable")
        sizes = d.groupby(["molecule", "view"], sort=False).size().values
        return lgb.Dataset(d[FE].values, label=d.is_truth.values, group=sizes, free_raw_data=False, feature_name=list(FE)), d
    ds_fit, fit_s = to_ds(fit_t)
    grid = [dict(num_leaves=nl, learning_rate=lr, min_data_in_leaf=20, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, objective="lambdarank",
                 metric="ndcg", eval_at=[25], label_gain=[0, 1], seed=0, **({"monotone_constraints": [MONO.get(f, 0) for f in FE], "monotone_constraints_method": "advanced"} if a.monotone else {}))
            for nl in (7, 15, 31) for lr in (0.03, 0.1)]
    results = []
    for params in grid:
        for rounds in (100, 300, 600):
            bst = lgb.train(params, ds_fit, num_boost_round=rounds)
            tune = tune.copy(); tune["pred"] = bst.predict(tune[FE].values)
            m = mrr_of(tune, "pred"); results.append(dict(params=params, rounds=rounds, tune_c2_strict=m.get("c2", {}).get("strict"), tune_c1=m.get("c1", {}).get("mrr"), tune_c2=m.get("c2", {}).get("mrr")))
            print(f"  leaves {params['num_leaves']} lr {params['learning_rate']} rounds {rounds}: tune C2 strict {m.get('c2', {}).get('strict', float('nan')):.4f} | C1 {m.get('c1', {}).get('mrr', float('nan')):.4f}", flush=True)
    base_tune = mrr_of(tune, "S_fixed"); print("fixed rule S(2,1,0.5) on tune:", base_tune); print("fixed rule S(2,1,0.15) on tune:", mrr_of(tune, "S_fixed15"))
    best = max(results, key=lambda r: (r["tune_c2_strict"] or 0) + 0.5 * (r["tune_c1"] or 0))
    print("selected:", best)
    bst = lgb.train(best["params"], ds_fit, num_boost_round=best["rounds"])
    ev = ev.copy(); ev["pred"] = bst.predict(ev[FE].values)
    out = dict(selected=best, tune_fixed=base_tune, eval_lambdarank=mrr_of(ev, "pred"), eval_fixed=mrr_of(ev, "S_fixed"), eval_fixed15=mrr_of(ev, "S_fixed15"),
               importance=dict(zip(FE, [int(x) for x in bst.feature_importance("gain").round().astype(int)])), n_fit_rows=len(fit_t), n_fit_groups=int(fit_t.groupby(["molecule", "view"]).ngroups),
               feats=a.feats, feature_names=list(FE), monotone=bool(a.monotone), drop=list(a.drop), c1_repeat=int(a.c1_repeat))
    # paired bootstrap on eval (per molecule-view)
    rows = []
    for (mid, view), g in ev.groupby(["molecule", "view"], sort=False):
        r1, _ = rr(g.pred.values, g.is_truth.values.astype(bool)); r0, _ = rr(g.S_fixed.values, g.is_truth.values.astype(bool)); rows.append((view, r1 - r0, bool(g.reachable.iloc[0])))
    dd = pd.DataFrame(rows, columns=["view", "d", "reach"])
    dd["d_strict"] = dd.d * (dd.reach | (dd.view == "c1"))
    out["eval_delta"] = {v: dict(delta=float(gg.d.mean()), ci95=boot(gg.d.values), delta_strict=float(gg.d_strict.mean()), ci95_strict=boot(gg.d_strict.values), n=len(gg)) for v, gg in dd.groupby("view")}
    json.dump(out, open(f"{a.out}/rank_results.json", "w"), indent=1, default=str); bst.save_model(f"{a.out}/lambdarank.txt")
    print(json.dumps({k: out[k] for k in ("eval_lambdarank", "eval_fixed", "eval_delta")}, indent=1)); print("importance (gain):", sorted(out["importance"].items(), key=lambda kv: -kv[1])[:12])


if __name__ == "__main__":
    main()
