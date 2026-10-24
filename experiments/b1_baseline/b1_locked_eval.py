"""B1 locked evaluation -- score the frozen rules on the locked evaluation run with the OFFICIAL scorer replica (src/metric.py).

For each scenario view (C2: truth references hidden, no-source candidates dropped; C1: molecules with usable independent references)
and each rule (fixed S = z(FP)+2z(GL)+z(ICE)+0.5 pop; LambdaRank model), the top-25 SMILES per molecule are written as a submission
frame and scored with metric.score(); per-molecule reciprocal ranks give bootstrap CIs and the paired delta LambdaRank - fixed.
The locked set is used once, after the settings were frozen; nothing here is tuned.
Usage: python -X utf8 b1_locked_eval.py --run DIR --eval_csv CSV --model lambdarank.txt [--out DIR]
"""
import argparse, json, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from b1_evaluate import z, term, boot
from b1_rankfeats import feature_matrix
import metric


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--model", required=True); ap.add_argument("--out", default=None)
    a = ap.parse_args(); out = a.out or f"{a.run}/results_locked"; os.makedirs(out, exist_ok=True)
    import lightgbm as lgb
    booster = lgb.Booster(model_file=a.model)
    keys = pl.read_parquet(os.path.join(os.path.dirname(os.path.dirname(HERE)), "data/processed/train_scorer_keys.parquet")).select("inchikey14", "normalized_smiles").unique("inchikey14")
    smi_of = dict(zip(keys["inchikey14"].to_list(), keys["normalized_smiles"].to_list()))
    report = {}; md = ["# B1 locked evaluation (official scorer replica)", ""]
    for s in ("A_timstof", "B_nplib"):
        F = pd.read_parquet(f"{a.run}/b1_features_{s}.parquet"); M = pd.read_csv(f"{a.run}/b1_molecules_{s}.csv").set_index("molecule")

        def load(model):
            p = f"{a.run}/work/{model}_{s}.json"
            try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
            except Exception: ok = False
            return (json.load(open(p)) if ok else {}), ok
        gl, gl_ok = load("gl"); ice, ice_ok = load("ice")
        for view in ("c2", "c1"):
            mols = [m for m in M.index if view == "c2" or bool(M.loc[m, "c1_usable"])]
            preds = {"fixed S(2,1,0.5)": {}, "lambdarank": {}}
            for mid, g0 in F.groupby("molecule", sort=False):
                if mid not in M.index or (view == "c1" and mid not in mols): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep].reset_index(drop=True)
                if len(g) == 0: continue
                fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                zfp = z(fp); zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
                S = zfp + (2 * zgl if zgl is not None else 0) + (zice if zice is not None else 0) + 0.5 * pop
                lib = g[f"lib_sim_{view}"].values.astype(float)
                X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                   g[f"lib_same_{view}"].values, g[f"lib_nref_{view}"].values, g.in_tier.values, g[f"in_train_{view}"].values, g.in_coconut.values,
                                   g.ppm_err.values, g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]))
                pr = booster.predict(X)
                for name, sc in (("fixed S(2,1,0.5)", S), ("lambdarank", pr)):
                    order = np.argsort(-sc, kind="stable")[:25]; preds[name][mid] = ";".join(str(g.smiles.values[i]) for i in order)
            missing = [m for m in mols if m not in smi_of]
            assert not missing, f"truth SMILES missing for {len(missing)} molecules (e.g. {missing[:3]})"
            sol = pd.DataFrame({"molecule_id": mols, "smiles": [smi_of[m] for m in mols]})
            res = {}
            for name, d in preds.items():
                sub = pd.DataFrame({"molecule_id": mols, "smiles": [d.get(m, "CCO") for m in mols]})
                official = float(metric.score(sol.copy(), sub.copy(), "molecule_id"))
                rr = np.array([metric.per_molecule_reciprocal_rank(smi_of[m], d.get(m, "CCO").split(";")) for m in mols])
                res[name] = dict(official_mrr25=official, mean_rr=float(rr.mean()), ci95=boot(rr), n=len(mols), rr=rr)
                sub.assign(rr=rr).to_csv(f"{out}/pred_{s}_{view}_{name.split()[0]}.csv", index=False)
            d_ = res["lambdarank"]["rr"] - res["fixed S(2,1,0.5)"]["rr"]
            report[f"{s}:{view}"] = {k: {kk: vv for kk, vv in v.items() if kk != "rr"} for k, v in res.items()} | {"delta": dict(mean=float(d_.mean()), ci95=boot(d_))}
            md.append(f"| {s} | {view} (n={len(mols)}) | fixed {res['fixed S(2,1,0.5)']['official_mrr25']:.4f} [{res['fixed S(2,1,0.5)']['ci95'][0]:.3f},{res['fixed S(2,1,0.5)']['ci95'][1]:.3f}] | "
                      f"lambdarank {res['lambdarank']['official_mrr25']:.4f} [{res['lambdarank']['ci95'][0]:.3f},{res['lambdarank']['ci95'][1]:.3f}] | Δ {d_.mean():+.4f} [{boot(d_)[0]:+.3f},{boot(d_)[1]:+.3f}] |")
            print(md[-1], flush=True)
    md.insert(2, "| set | view | fixed S(2,1,0.5) (official MRR@25) | LambdaRank | Δ (paired) |"); md.insert(3, "|---|---|---|---|---|")
    json.dump(report, open(f"{out}/locked_results.json", "w"), indent=1); open(f"{out}/locked_results.md", "w", encoding="utf-8").write("\n".join(md)); print("saved", out)


if __name__ == "__main__":
    main()
