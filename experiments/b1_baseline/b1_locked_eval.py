"""B1 locked evaluation -- score the frozen candidates on the locked evaluation run with the OFFICIAL scorer replica (src/metric.py).

Codex 009 conditions: the ledger is the frozen molecule list of --eval_csv per set (C2: every molecule; C1: molecules usable in the class-1
view), molecules without candidates count as 0; each candidate is a (run, model, w_ice) triple whose learned fusion uses the feature names
stored in the model file (schema checked), scored next to its registered insurance (fixed S(2, w_ice, 0.5) + libpri(tau, margin)) and the
plain fixed rule; candidates are compared DIRECTLY per molecule (RR(cand) - RR(ref)), with molecule-level bootstrap CIs, per set and view.
Usage: python -X utf8 b1_locked_eval.py --eval_csv CSV --cands M1:RUN:MODEL:W_ICE M2:RUN:MODEL:W_ICE [--tau 0.9 --margin 0.2 --out DIR]
"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from b1_evaluate import z, term, boot
from b1_rankfeats import feature_matrix
import metric


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load_runner(run, s, model):
    p = f"{run}/work/{model}_{s}.json"
    try: meta = json.load(open(p + ".meta.json")); ok = meta.get("status") in ("ok", "partial")
    except Exception: meta, ok = {}, False
    return (json.load(open(p)) if ok else {}), ok, meta


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--eval_csv", required=True); ap.add_argument("--cands", nargs="+", required=True, help="NAME:RUN:MODEL:W_ICE")
    ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--out", required=True)
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    import lightgbm as lgb
    ev = pd.read_csv(a.eval_csv)
    keys = pl.read_parquet(os.path.join(os.path.dirname(os.path.dirname(HERE)), "data/processed/train_scorer_keys.parquet")).select("inchikey14", "normalized_smiles").unique("inchikey14")
    smi_of = dict(zip(keys["inchikey14"].to_list(), keys["normalized_smiles"].to_list()))
    cands = []
    for c in a.cands:
        name, run, model, w_ice = c.split(":"); booster = lgb.Booster(model_file=model); feats = booster.feature_name()
        assert not any(f.startswith("Column_") for f in feats), f"{model}: feature names missing"
        cands.append(dict(name=name, run=run, model=model, w_ice=float(w_ice), booster=booster, feats=feats, model_sha=sha(model)))
        print(f"candidate {name}: run {run} | model {model} ({booster.num_trees()} trees, {len(feats)} features, sha {cands[-1]['model_sha'][:12]}) | w_ice {w_ice}", flush=True)
    manifest = dict(eval_csv=a.eval_csv, tau=a.tau, margin=a.margin, candidates=[{k: v for k, v in c.items() if k != "booster"} for c in cands], code=dict(
        b1_locked_eval=sha(__file__), b1_rankfeats=sha(os.path.join(HERE, "b1_rankfeats.py")), b1_evaluate=sha(os.path.join(HERE, "b1_evaluate.py")), metric=sha(os.path.join(os.path.dirname(os.path.dirname(HERE)), "src", "metric.py"))))
    report = {"manifest": manifest}; md = ["# B1 locked evaluation (official scorer replica, frozen ledger)", ""]
    RR = {}   # (set, view, cand, rule) -> np.array over the ledger
    for s in a.sets:
        ledger = ev[ev.set == s].molecule.astype(str).tolist()
        missing = [m for m in ledger if m not in smi_of]; assert not missing, f"truth SMILES missing: {missing[:3]}"
        sol = pd.DataFrame({"molecule_id": ledger, "smiles": [smi_of[m] for m in ledger]})
        c1_flags = {}
        for c in cands:
            M = pd.read_csv(f"{c['run']}/b1_molecules_{s}.csv").set_index("molecule"); M.index = M.index.astype(str)
            c1_flags[c["name"]] = {m: bool(M.loc[m, "c1_usable"]) if m in M.index else False for m in ledger}
        base = c1_flags[cands[0]["name"]]
        for c in cands[1:]:
            diff = [m for m in ledger if c1_flags[c["name"]][m] != base[m]]
            if diff: print(f"AUDIT: c1_usable differs between candidates for {len(diff)} molecules in {s}; the C1 ledger uses the intersection", flush=True)
        c1_ledger = [m for m in ledger if all(c1_flags[c["name"]][m] for c in cands)]
        for c in cands:
            F = pd.read_parquet(f"{c['run']}/b1_features_{s}.parquet"); F["molecule"] = F["molecule"].astype(str); M = pd.read_csv(f"{c['run']}/b1_molecules_{s}.csv").set_index("molecule"); M.index = M.index.astype(str)
            gl, gl_ok, glm = load_runner(c["run"], s, "gl"); ice, ice_ok, icm = load_runner(c["run"], s, "ice")
            if c["w_ice"] == 0: ice, ice_ok = {}, False
            cover = dict(gl=glm.get("status"), ice=icm.get("status") if c["w_ice"] else "unused")
            for view in ("c2", "c1"):
                mols = ledger if view == "c2" else c1_ledger
                preds = {"learned": {}, "insurance": {}, "fixed": {}}
                for mid, g0 in F.groupby("molecule", sort=False):
                    if mid not in set(mols): continue
                    keep = g0[f"in_short_{view}"].values.astype(bool)
                    if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                    g = g0[keep].reset_index(drop=True)
                    if len(g) == 0: continue
                    fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{view}"].values.astype(float)
                    glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                    icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                    zfp = z(fp); zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
                    S = zfp + (2 * zgl if zgl is not None else 0) + (c["w_ice"] * zice if zice is not None else 0) + 0.5 * pop
                    top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
                    ins = np.where(lib >= a.tau, 100.0 + lib, S) if (lib.max() >= a.tau and lib.max() - second >= a.margin) else S
                    X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                       g[f"lib_same_{view}"].values, g[f"lib_nref_{view}"].values, g.in_tier.values, g[f"in_train_{view}"].values, g.in_coconut.values,
                                       g.ppm_err.values, g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]),
                                       n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=c["feats"])
                    assert X.shape[1] == len(c["feats"]), (X.shape, len(c["feats"]))
                    pr = c["booster"].predict(X)
                    for name, sc in (("learned", pr), ("insurance", ins), ("fixed", S)):
                        order = np.argsort(-sc, kind="stable")[:25]; preds[name][mid] = ";".join(str(g.smiles.values[i]) for i in order)
                sol_v = sol[sol.molecule_id.isin(set(mols))]
                for name, d in preds.items():
                    sub = pd.DataFrame({"molecule_id": mols, "smiles": [d.get(m, "CCO") for m in mols]})
                    official = float(metric.score(sol_v.copy(), sub.copy(), "molecule_id"))
                    rr = np.array([metric.per_molecule_reciprocal_rank(smi_of[m], d.get(m, "CCO").split(";")) for m in mols])
                    RR[(s, view, c["name"], name)] = rr; n_empty = int(sum(1 for m in mols if m not in d)); ci = boot(rr)
                    report[f"{s}:{view}:{c['name']}:{name}"] = dict(official_mrr25=official, ci95=ci, n=len(mols), n_empty=n_empty, cover=cover)
                    sub.assign(rr=rr).to_csv(f"{a.out}/pred_{s}_{view}_{c['name']}_{name}.csv", index=False)
                    md.append(f"| {s} | {view} (n={len(mols)}) | {c['name']} | {name} | {official:.4f} [{ci[0]:.3f}, {ci[1]:.3f}] | empty {n_empty} |")
                    print(md[-1], flush=True)
    md.insert(2, "| set | view | candidate | output | official MRR@25 [95% CI] | no candidates |"); md.insert(3, "|---|---|---|---|---|---|")
    # ---- direct paired comparisons (same ledger): within candidate (learned - fixed, insurance - fixed) and between candidates (cand - first)
    md += ["", "## paired differences (molecule-level bootstrap, same ledger)", "", "| set | view | comparison | mean Δ RR | 95% CI | n |", "|---|---|---|---:|---|---:|"]
    ref = cands[0]["name"]
    for s in a.sets:
        for view in ("c2", "c1"):
            pairs = []
            for c in cands:
                pairs.append((f"{c['name']}: learned − fixed", RR.get((s, view, c["name"], "learned")), RR.get((s, view, c["name"], "fixed"))))
                pairs.append((f"{c['name']}: insurance − fixed", RR.get((s, view, c["name"], "insurance")), RR.get((s, view, c["name"], "fixed"))))
                if c["name"] != ref:
                    pairs.append((f"{c['name']} − {ref} (learned)", RR.get((s, view, c["name"], "learned")), RR.get((s, view, ref, "learned"))))
                    pairs.append((f"{c['name']} − {ref} (insurance)", RR.get((s, view, c["name"], "insurance")), RR.get((s, view, ref, "insurance"))))
            for label, x, y in pairs:
                if x is None or y is None or len(x) != len(y): continue
                d = x - y; ci = boot(d); report[f"delta:{s}:{view}:{label}"] = dict(mean=float(d.mean()), ci95=ci, n=len(d))
                md.append(f"| {s} | {view} | {label} | {d.mean():+.4f} | [{ci[0]:+.3f}, {ci[1]:+.3f}] | {len(d)} |"); print(md[-1], flush=True)
    json.dump(report, open(f"{a.out}/locked_results.json", "w"), indent=1, default=str); open(f"{a.out}/locked_results.md", "w", encoding="utf-8").write("\n".join(md) + "\n"); print("saved", a.out)


if __name__ == "__main__":
    main()
