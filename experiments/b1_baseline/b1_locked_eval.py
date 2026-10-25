"""B1 locked evaluation -- score the frozen candidates on the locked evaluation run with the OFFICIAL scorer replica (src/metric.py).

Codex 009/010 conditions: (1) VALIDATE EVERYTHING FIRST (files, runner outputs, model schema, one prediction per candidate/set/view) and score
nothing until all checks pass; (2) ledger = the frozen molecule list of --eval_csv per set (C2: all; C1: molecules usable for every candidate),
molecules without candidates count as 0; (3) each candidate = (run, model, w_ice) whose learned fusion uses the model's own feature names AND
the submission pipeline's GL-coverage fallback (GL finite on < max(2, min_gl_cover * n) candidates -> the insurance ordering); scored next to
its insurance (fixed S(2, w_ice, 0.5) + libpri(tau, margin)) and the plain fixed rule; (4) candidates are compared DIRECTLY per molecule
(RR(cand) - RR(ref)) with molecule-level bootstrap CIs per set and view; (5) the output directory must not contain earlier results (no re-run
over a previous opening); the manifest records sha256 of code, models, feature tables, molecule tables, runner outputs and the ledger.
Usage: python -X utf8 b1_locked_eval.py --eval_csv CSV --cands M1:RUN:MODEL:W_ICE M2:RUN:MODEL:W_ICE --out DIR [--tau 0.9 --margin 0.2 --min_gl_cover 0.5]
"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from b1_evaluate import z, term, boot
from b1_rankfeats import feature_matrix
import metric


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""): h.update(chunk)
    return h.hexdigest()


def runner(run, s, model):
    p = f"{run}/work/{model}_{s}.json"
    if not os.path.exists(p) or not os.path.exists(p + ".meta.json"): return None, None, p
    meta = json.load(open(p + ".meta.json"))
    if meta.get("status") in ("ok", "partial"): return json.load(open(p)), meta, p
    # a runner that had NOTHING to score (no forward-coverable query in the set, e.g. negative-only or NH4-only strata) reports status
    # 'error' with n_mols_scored 0 and an all-null output: that is a legitimate empty result (every molecule takes the GL-cover fallback),
    # recorded as runner_empty in the manifest, not a validation failure (dev2 strata E/F, 2026-10-25)
    if meta.get("status") == "error" and int(meta.get("n_mols_scored") or 0) == 0:
        try: out = json.load(open(p))
        except Exception: return None, meta, p
        if all(v is None for d in out.values() for v in (d or {}).values()): meta = dict(meta, runner_empty=True); return {}, meta, p
    return None, meta, p


PCL = set()          # PubChemLite keys (official candidate_key + raw ik14), filled from --pcl_keys (2026-10-25 class-2 prior test)
PCL_W = []           # boost weights: extra outputs blend21_pcl<w> = blend21 + w * 1[candidate in PubChemLite]


def scores_for(view, g, mid, gl, ice, gl_ok, ice_ok, c, M, tau, margin, min_gl_cover):
    """-> dict(name -> top-25 smiles list) plus diagnostics for one molecule / view."""
    fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{view}"].values.astype(float)
    glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
    icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
    zfp = z(fp); zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
    S = zfp + (2 * zgl if zgl is not None else 0) + (c["w_ice"] * zice if zice is not None else 0) + 0.5 * pop
    top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
    ins = np.where(lib >= tau, 100.0 + lib, S) if (lib.max() >= tau and lib.max() - second >= margin) else S
    gl_cover_ok = np.isfinite(glv).sum() >= max(2, min_gl_cover * len(g))
    if gl_cover_ok:
        X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                           g[f"lib_same_{view}"].values, g[f"lib_nref_{view}"].values, g.in_tier.values, g[f"in_train_{view}"].values, g.in_coconut.values,
                           g.ppm_err.values, g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]),
                           n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=c["feats"])
        if X.shape[1] != len(c["feats"]): raise RuntimeError(f"schema mismatch {X.shape} vs {len(c['feats'])}")
        main = c["booster"].predict(X)
    else: main = ins   # the submission pipeline's fallback (b1_pipeline --min_gl_cover)
    fire = bool(lib.max() >= tau and lib.max() - second >= margin)
    # switch (Codex 012 (c)): one output function -- library priority fires or GL cover short -> insurance list, otherwise the learned list
    # blend (2026-10-25 01:05, hedge found with the probe): z(learned) and z(fixed) within the molecule's candidates, 2:1 and 1:1; the GL-cover
    # fallback (main = insurance) is kept, i.e. blend = z(ins) + z(S) there
    # blend definition unified with the submission pipeline (Codex 013): GL cover short -> the insurance list itself (no blending of the
    # insurance with the fixed rule); otherwise w*z(learned) + z(S) with S = the fixed rule WITHOUT library priority
    zm, zs = z(np.asarray(main, float)), z(np.asarray(S, float))
    blend21 = (2 * zm + zs) if gl_cover_ok else ins; blend11 = (zm + zs) if gl_cover_ok else ins
    out = {}
    variants = [("learned", main), ("insurance", ins), ("fixed", S), ("switch", ins if fire else main), ("blend21", blend21), ("blend11", blend11)]
    if PCL_W:
        in_pcl = np.array([(k in PCL) for k in g.official_key.astype(str).values], float)
        variants += [(f"blend21_pcl{w:g}", np.asarray(blend21, float) + w * in_pcl) for w in PCL_W]
    for name, sc in variants:
        order = np.argsort(-np.asarray(sc, float), kind="stable")[:25]; out[name] = [str(g.smiles.values[i]) for i in order]
    return out, dict(gl_cover_ok=bool(gl_cover_ok), gl_cover=float(np.isfinite(glv).mean()), ice_cover=float(np.isfinite(icv).mean()))


def view_frame(F, M, mid, view):
    g0 = F[F.molecule == mid]
    keep = g0[f"in_short_{view}"].values.astype(bool)
    if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
    return g0[keep].reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--eval_csv", required=True); ap.add_argument("--cands", nargs="+", required=True, help="NAME:RUN:MODEL:W_ICE")
    ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--min_gl_cover", type=float, default=0.5)
    ap.add_argument("--out", required=True); ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"])
    ap.add_argument("--pcl_keys", default="", help="PubChemLite annotation parquet (candidate_key, ik14): adds outputs blend21_pcl<w>")
    ap.add_argument("--pcl_w", nargs="*", default=["0.5", "1", "2", "4"], help="boost weights for the blend21_pcl<w> outputs")
    ap.add_argument("--main_of", nargs="*", default=[], help="registered MAIN output per candidate, NAME=OUTPUT (default learned), e.g. M1=learned M2x=blend21; "
                    "the paired difference of the registered mains is reported explicitly (Codex 014)")
    a = ap.parse_args()
    MAIN_OF = {kv.split("=")[0]: kv.split("=")[1] for kv in a.main_of}
    if a.pcl_keys:
        import polars as _pl
        _t = _pl.read_parquet(a.pcl_keys, columns=["candidate_key", "ik14"]); PCL.update(_t["candidate_key"].drop_nulls().to_list()); PCL.update(_t["ik14"].drop_nulls().to_list())
        PCL_W.extend(float(w) for w in a.pcl_w); print(f"PubChemLite keys {len(PCL):,}; boost weights {PCL_W}", flush=True)
    if os.path.exists(os.path.join(a.out, "locked_results.json")) or os.path.exists(os.path.join(a.out, "manifest.json")):
        print(f"REFUSED: {a.out} already holds an opening (locked_results.json / manifest.json); the locked set is opened once"); sys.exit(3)
    os.makedirs(a.out, exist_ok=True)
    import lightgbm as lgb
    # ------------------------------------------------------------------ phase 1: validate everything, score nothing
    problems = []; manifest = dict(eval_csv=a.eval_csv, eval_csv_sha=sha(a.eval_csv), tau=a.tau, margin=a.margin, min_gl_cover=a.min_gl_cover, sets=a.sets, registered_main=MAIN_OF, candidates=[], inputs={},
                                   code={os.path.basename(p): sha(p) for p in (__file__, os.path.join(HERE, "b1_rankfeats.py"), os.path.join(HERE, "b1_evaluate.py"), os.path.join(os.path.dirname(os.path.dirname(HERE)), "src", "metric.py"))})
    ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev["molecule"].astype(str)
    keys_p = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data/processed/train_scorer_keys.parquet")
    keys = pl.read_parquet(keys_p).select("inchikey14", "normalized_smiles").unique("inchikey14"); smi_of = dict(zip(keys["inchikey14"].to_list(), keys["normalized_smiles"].to_list()))
    cands, data = [], {}
    for cspec in a.cands:
        name, run, model, w_ice = cspec.split(":")
        try: booster = lgb.Booster(model_file=model); feats = booster.feature_name()
        except Exception as e: problems.append(f"{name}: model {model} unreadable: {e!r}"); continue
        if any(f.startswith("Column_") for f in feats): problems.append(f"{name}: model {model} has no feature names")
        c = dict(name=name, run=run, model=model, w_ice=float(w_ice), booster=booster, feats=feats)
        manifest["candidates"].append(dict(name=name, run=run, model=model, model_sha=sha(model), n_trees=booster.num_trees(), n_features=len(feats), features=feats, w_ice=float(w_ice)))
        for s in a.sets:
            fpq, mcsv = f"{run}/b1_features_{s}.parquet", f"{run}/b1_molecules_{s}.csv"
            for p in (fpq, mcsv):
                if not os.path.exists(p): problems.append(f"{name}/{s}: missing {p}"); continue
                manifest["inputs"][p] = sha(p)
            gl, glm, glp = runner(run, s, "gl"); ice, icm, icp = runner(run, s, "ice")
            if gl is None: problems.append(f"{name}/{s}: GL output unusable ({glp}, status {glm and glm.get('status')})")
            if c["w_ice"] > 0 and ice is None: problems.append(f"{name}/{s}: ICE output unusable ({icp}, status {icm and icm.get('status')})")
            for p, mm in ((glp, glm), (icp, icm)):
                if os.path.exists(p): manifest["inputs"][p] = sha(p); manifest["inputs"][p + ".meta.json"] = ("empty (nothing to score)" if (mm or {}).get("runner_empty") else json.load(open(p + ".meta.json")).get("status"))
            if problems: continue
            F = pd.read_parquet(fpq); F["molecule"] = F["molecule"].astype(str); M = pd.read_csv(mcsv).set_index("molecule"); M.index = M.index.astype(str)
            if c["w_ice"] == 0: ice = {}
            data[(name, s)] = dict(F=F, M=M, gl=gl, ice=ice or {}, gl_ok=True, ice_ok=bool(ice) and c["w_ice"] > 0)
            ledger = ev[ev.set == s].molecule.tolist()
            miss = [m for m in ledger if m not in smi_of]
            if miss: problems.append(f"{s}: truth SMILES missing for {len(miss)} ledger molecules")
            # one prediction per view (schema / fallback path exercised)
            for view in ("c2", "c1"):
                for mid in ledger:
                    g = view_frame(F, M, mid, view)
                    if len(g) == 0 or mid not in M.index: continue
                    try: scores_for(view, g, mid, data[(name, s)]["gl"], data[(name, s)]["ice"], True, data[(name, s)]["ice_ok"], c, M, a.tau, a.margin, a.min_gl_cover)
                    except Exception as e: problems.append(f"{name}/{s}/{view}: prediction failed on {mid}: {e!r}")
                    break
        cands.append(c)
    if len(cands) < 1: problems.append("no candidates")
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    if problems:
        print("VALIDATION FAILED:"); [print("  -", p) for p in problems]; sys.exit(2)
    print(f"validation passed: {len(cands)} candidates x {len(a.sets)} sets; manifest {a.out}/manifest.json", flush=True)
    # ------------------------------------------------------------------ phase 2: score (once)
    report = {"manifest_file": "manifest.json"}; md = ["# B1 locked evaluation (official scorer replica, frozen ledger)", "", "| set | view | candidate | output | official MRR@25 [95% CI] | no candidates | GL fallback |", "|---|---|---|---|---|---|---|"]
    RR = {}; MOLS_OF = {}
    for s in a.sets:
        ledger = ev[ev.set == s].molecule.tolist(); sol_all = pd.DataFrame({"molecule_id": ledger, "smiles": [smi_of[m] for m in ledger]})
        usable = {c["name"]: {m: bool(data[(c["name"], s)]["M"].loc[m, "c1_usable"]) if m in data[(c["name"], s)]["M"].index else False for m in ledger} for c in cands}
        c1_ledger = [m for m in ledger if all(usable[c["name"]][m] for c in cands)]
        n_diff = sum(1 for m in ledger if len({usable[c["name"]][m] for c in cands}) > 1)
        if n_diff: print(f"AUDIT {s}: c1_usable differs between candidates for {n_diff} molecules; C1 ledger = intersection ({len(c1_ledger)})", flush=True)
        report[f"{s}:ledger"] = dict(c2=len(ledger), c1=len(c1_ledger), c1_usable_disagreements=n_diff)
        for c in cands:
            d = data[(c["name"], s)]
            for view in ("c2", "c1"):
                mols = ledger if view == "c2" else c1_ledger; preds = {n_: {} for n_ in ["learned", "insurance", "fixed", "switch", "blend21", "blend11"] + [f"blend21_pcl{w:g}" for w in PCL_W]}; n_fb = 0; covers = []
                MOLS_OF[(s, view)] = list(mols)
                if len(mols) == 0:   # e.g. a stratum without usable C1 references (D_np_single): recorded as n=0, not scored (the official scorer rejects an empty submission)
                    md.append(f"| {s} | {view} (n=0) | {c['name']} | - | no molecules in this view (not scored) | - | - |"); print(md[-1], flush=True); continue
                for mid in mols:
                    g = view_frame(d["F"], d["M"], mid, view)
                    if len(g) == 0 or mid not in d["M"].index: continue
                    out, diag = scores_for(view, g, mid, d["gl"], d["ice"], True, d["ice_ok"], c, d["M"], a.tau, a.margin, a.min_gl_cover)
                    n_fb += int(not diag["gl_cover_ok"]); covers.append(diag["gl_cover"])
                    for name, lst in out.items(): preds[name][mid] = ";".join(lst)
                sol_v = sol_all[sol_all.molecule_id.isin(set(mols))]
                for name, pdict in preds.items():
                    sub = pd.DataFrame({"molecule_id": mols, "smiles": [pdict.get(m, "CCO") for m in mols]})
                    official = float(metric.score(sol_v.copy(), sub.copy(), "molecule_id"))
                    rr = np.array([metric.per_molecule_reciprocal_rank(smi_of[m], pdict.get(m, "CCO").split(";")) for m in mols]); ci = boot(rr)
                    RR[(s, view, c["name"], name)] = rr; n_empty = int(sum(1 for m in mols if m not in pdict))
                    report[f"{s}:{view}:{c['name']}:{name}"] = dict(official_mrr25=official, ci95=ci, n=len(mols), n_empty=n_empty, gl_fallback=n_fb, gl_cover_mean=float(np.mean(covers)) if covers else None)
                    sub.assign(rr=rr).to_csv(f"{a.out}/pred_{s}_{view}_{c['name']}_{name}.csv", index=False)
                    md.append(f"| {s} | {view} (n={len(mols)}) | {c['name']} | {name} | {official:.4f} [{ci[0]:.3f}, {ci[1]:.3f}] | {n_empty} | {n_fb} |"); print(md[-1], flush=True)
    md += ["", "## paired differences (molecule-level bootstrap, same ledger)", "", "| set | view | comparison | mean Δ RR | 95% CI | n |", "|---|---|---|---:|---|---:|"]
    ref = cands[0]["name"]
    for s in a.sets:
        for view in ("c2", "c1"):
            pairs = []
            for c in cands:
                pairs += [(f"{c['name']}: learned − fixed", (s, view, c["name"], "learned"), (s, view, c["name"], "fixed")), (f"{c['name']}: insurance − fixed", (s, view, c["name"], "insurance"), (s, view, c["name"], "fixed")),
                          (f"{c['name']}: switch − fixed", (s, view, c["name"], "switch"), (s, view, c["name"], "fixed")), (f"{c['name']}: switch − learned", (s, view, c["name"], "switch"), (s, view, c["name"], "learned")),
                          (f"{c['name']}: blend21 − learned", (s, view, c["name"], "blend21"), (s, view, c["name"], "learned")), (f"{c['name']}: blend21 − fixed", (s, view, c["name"], "blend21"), (s, view, c["name"], "fixed")),
                          (f"{c['name']}: blend11 − learned", (s, view, c["name"], "blend11"), (s, view, c["name"], "learned")), (f"{c['name']}: blend11 − fixed", (s, view, c["name"], "blend11"), (s, view, c["name"], "fixed"))]
                if c["name"] != ref:
                    pairs += [(f"{c['name']} − {ref} (learned)", (s, view, c["name"], "learned"), (s, view, ref, "learned")), (f"{c['name']} − {ref} (insurance)", (s, view, c["name"], "insurance"), (s, view, ref, "insurance")),
                              (f"{c['name']} − {ref} (switch)", (s, view, c["name"], "switch"), (s, view, ref, "switch")), (f"{c['name']} − {ref} (blend21)", (s, view, c["name"], "blend21"), (s, view, ref, "blend21")),
                              (f"{c['name']} learned − {ref} insurance", (s, view, c["name"], "learned"), (s, view, ref, "insurance")),
                              # the REGISTERED main outputs of the two candidates (Codex 014): this is the adoption-rule comparison
                              (f"REGISTERED {c['name']} {MAIN_OF.get(c['name'], 'learned')} − {ref} {MAIN_OF.get(ref, 'learned')}", (s, view, c["name"], MAIN_OF.get(c["name"], "learned")), (s, view, ref, MAIN_OF.get(ref, "learned")))]
            for label, kx, ky in pairs:
                x, y = RR.get(kx), RR.get(ky)
                if x is None or y is None or len(x) != len(y): continue
                dd = x - y; ci = boot(dd); report[f"delta:{s}:{view}:{label}"] = dict(mean=float(dd.mean()), ci95=ci, n=len(dd))
                md.append(f"| {s} | {view} | {label} | {dd.mean():+.4f} | [{ci[0]:+.3f}, {ci[1]:+.3f}] | {len(dd)} |"); print(md[-1], flush=True)
                if label.startswith("REGISTERED") and (s, view) in MOLS_OF and len(MOLS_OF[(s, view)]) == len(dd):   # per-molecule differences of the registered mains
                    pd.DataFrame({"molecule": MOLS_OF[(s, view)], "rr_candidate": x, "rr_reference": y, "d": dd}).to_csv(f"{a.out}/registered_delta_{s}_{view}.csv", index=False)
    json.dump(report, open(f"{a.out}/locked_results.json", "w"), indent=1, default=str); open(f"{a.out}/locked_results.md", "w", encoding="utf-8").write("\n".join(md) + "\n"); print("saved", a.out)


if __name__ == "__main__":
    main()
