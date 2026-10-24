"""B1 step 3 -- learned fusion (LightGBM LambdaRank) on the unified candidate table, compared with the fixed rule on the same molecules.

Training rows: shortlist candidates of molecules in the FIT groups of the given runs, under both scenario views (C2 and, where
possible, C1) -- the two views of one molecule are one 'identity' and always stay in the same split. Features are molecule-relative
(z within the shortlist) plus raw values and flags; the label is is_truth. Model selection (num_leaves / learning rate / rounds) uses
the TUNE groups; the EVAL groups are scored once with the selected setting and reported next to the fixed rule S(2,1,0.15).
Usage: python -X utf8 b1_rank_train.py --runs RUN[:eval_csv] ... [--out DIR]
       e.g. --runs experiments/b1_baseline/run1:experiments/b1_baseline/eval_set/p1_molecules.csv experiments/b1_baseline/run_c1:...
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
import lightgbm as lgb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_evaluate import z, rr, boot, term, LAM

FEATS = ["z_fp", "z_gl", "z_ice", "fp", "gl", "ice", "pop_public", "lsid", "lpmid", "lsynonyms", "np_bit", "src_bit", "lotus", "lib_sim", "lib_same", "lib_nref", "lib_margin",
         "lib_max_mol", "in_tier", "in_train", "in_coconut", "ppm_err", "fp_rank_window", "n_cands", "gl_missing", "ice_missing", "n_query", "ce_known", "view_c1"]


def load_run(run, eval_csv):
    ev = pd.read_csv(eval_csv).set_index("molecule")
    out = []
    for s in ("A_timstof", "B_nplib"):
        fp_ = f"{run}/b1_features_{s}.parquet"
        if not os.path.exists(fp_): continue
        F = pd.read_parquet(fp_); M = pd.read_csv(f"{run}/b1_molecules_{s}.csv").set_index("molecule")
        def load(model):
            p = f"{run}/work/{model}_{s}.json"
            try: ok = json.load(open(p + ".meta.json")).get("status") == "ok"
            except Exception: ok = False
            return (json.load(open(p)) if ok else {}), ok
        gl, gl_ok = load("gl"); ice, ice_ok = load("ice")
        for mid, g in F.groupby("molecule", sort=False):
            if mid not in M.index: continue
            m = M.loc[mid]
            fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float)
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            zfp = z(fp); zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
            for view in ("c2", "c1"):
                if view == "c1" and not bool(m.c1_possible): continue
                lib = g[f"lib_sim_{view}"].values.astype(float); top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
                S = zfp + (2 * zgl if zgl is not None else 0) + (zice if zice is not None else 0) + LAM * pop
                d = pd.DataFrame(dict(run=run, set=s, molecule=mid, view=view, group=m.group, identity=mid, is_truth=g.is_truth.values.astype(int),
                                      z_fp=zfp, z_gl=zgl if zgl is not None else 0.0, z_ice=zice if zice is not None else 0.0, fp=np.nan_to_num(fp, nan=np.nanmin(fp) if np.isfinite(fp).any() else 0),
                                      gl=np.nan_to_num(glv, nan=-1.0), ice=np.nan_to_num(icv, nan=-1.0), pop_public=pop, lsid=g.lsid.values, lpmid=g.lpmid.values, lsynonyms=g.lsynonyms.values,
                                      np_bit=(g["np"].values != 0).astype(float), src_bit=((g.src_mask.values.astype(np.int64) & 1) != 0).astype(float), lotus=np.log1p(np.maximum(g.lotus_refs.values, 0)),
                                      lib_sim=lib, lib_same=g[f"lib_same_{view}"].values.astype(float), lib_nref=g[f"lib_nref_{view}"].values.astype(float), lib_margin=lib - second,
                                      lib_max_mol=float(lib.max()), in_tier=g.in_tier.values.astype(float), in_train=g[f"in_train_{view}"].values.astype(float), in_coconut=g.in_coconut.values.astype(float),
                                      ppm_err=g.ppm_err.values.astype(float), fp_rank_window=np.log1p(g.fp_rank_window.values.astype(float)), n_cands=float(len(g)),
                                      gl_missing=(~np.isfinite(glv)).astype(float), ice_missing=(~np.isfinite(icv)).astype(float), n_query=float(m.n_query), ce_known=float(m.ce_known),
                                      view_c1=float(view == "c1"), S_fixed=S, reachable=bool(ev.loc[mid, "window_external"]) if mid in ev.index else True))
                out.append(d)
    return pd.concat(out, ignore_index=True)


def mrr_of(df, score_col):
    vals, strict = [], []
    for (mid, view), g in df.groupby(["molecule", "view"], sort=False):
        r, _ = rr(g[score_col].values, g.is_truth.values.astype(bool)); vals.append((view, r, bool(g.reachable.iloc[0])))
    d = pd.DataFrame(vals, columns=["view", "rr", "reach"])
    res = {}
    for view, gg in d.groupby("view"):
        res[view] = dict(mrr=float(gg.rr.mean()), n=len(gg), strict=float((gg.rr * (gg.reach | (view == "c1"))).mean()))
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--out", default="experiments/b1_baseline/rank")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    data = pd.concat([load_run(*r.split(":", 1)) for r in a.runs], ignore_index=True)
    print("rows", len(data), "| molecules", data.molecule.nunique(), "| groups", data.groupby("group").molecule.nunique().to_dict(), "| views", data.groupby("view").molecule.nunique().to_dict())
    fit, tune, ev = (data[data.group == g].copy() for g in ("fit", "tune", "eval"))
    # keep only training groups whose shortlist contains the truth (ranking loss needs a positive); evaluation keeps every molecule
    def groups_with_truth(d):
        has = d.groupby(["molecule", "view"]).is_truth.transform("max") > 0; return d[has]
    fit_t = groups_with_truth(fit)
    def to_ds(d):
        d = d.sort_values(["molecule", "view"], kind="stable")
        sizes = d.groupby(["molecule", "view"], sort=False).size().values
        return lgb.Dataset(d[FEATS].values, label=d.is_truth.values, group=sizes, free_raw_data=False), d
    ds_fit, fit_s = to_ds(fit_t)
    grid = [dict(num_leaves=nl, learning_rate=lr, min_data_in_leaf=20, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, objective="lambdarank",
                 metric="ndcg", eval_at=[25], label_gain=[0, 1], seed=0) for nl in (7, 15, 31) for lr in (0.03, 0.1)]
    results = []
    for params in grid:
        for rounds in (100, 300, 600):
            bst = lgb.train(params, ds_fit, num_boost_round=rounds)
            tune = tune.copy(); tune["pred"] = bst.predict(tune[FEATS].values)
            m = mrr_of(tune, "pred"); results.append(dict(params=params, rounds=rounds, tune_c2_strict=m.get("c2", {}).get("strict"), tune_c1=m.get("c1", {}).get("mrr"), tune_c2=m.get("c2", {}).get("mrr")))
            print(f"  leaves {params['num_leaves']} lr {params['learning_rate']} rounds {rounds}: tune C2 strict {m.get('c2', {}).get('strict', float('nan')):.4f} | C1 {m.get('c1', {}).get('mrr', float('nan')):.4f}", flush=True)
    base_tune = mrr_of(tune, "S_fixed"); print("fixed rule S(2,1,0.15) on tune:", base_tune)
    best = max(results, key=lambda r: (r["tune_c2_strict"] or 0) + 0.5 * (r["tune_c1"] or 0))
    print("selected:", best)
    bst = lgb.train(best["params"], ds_fit, num_boost_round=best["rounds"])
    ev = ev.copy(); ev["pred"] = bst.predict(ev[FEATS].values)
    out = dict(selected=best, tune_fixed=base_tune, eval_lambdarank=mrr_of(ev, "pred"), eval_fixed=mrr_of(ev, "S_fixed"),
               importance=dict(zip(FEATS, [int(x) for x in bst.feature_importance("gain").round().astype(int)])), n_fit_rows=len(fit_t), n_fit_groups=int(fit_t.groupby(["molecule", "view"]).ngroups))
    # paired bootstrap on eval (per molecule-view)
    rows = []
    for (mid, view), g in ev.groupby(["molecule", "view"], sort=False):
        r1, _ = rr(g.pred.values, g.is_truth.values.astype(bool)); r0, _ = rr(g.S_fixed.values, g.is_truth.values.astype(bool)); rows.append((view, r1 - r0, bool(g.reachable.iloc[0])))
    dd = pd.DataFrame(rows, columns=["view", "d", "reach"])
    out["eval_delta"] = {v: dict(delta=float(gg.d.mean()), ci95=boot(gg.d.values), n=len(gg)) for v, gg in dd.groupby("view")}
    json.dump(out, open(f"{a.out}/rank_results.json", "w"), indent=1, default=str); bst.save_model(f"{a.out}/lambdarank.txt")
    print(json.dumps({k: out[k] for k in ("eval_lambdarank", "eval_fixed", "eval_delta")}, indent=1)); print("importance (gain):", sorted(out["importance"].items(), key=lambda kv: -kv[1])[:12])


if __name__ == "__main__":
    main()
