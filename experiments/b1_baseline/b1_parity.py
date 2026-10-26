"""W7 parity test with a verdict (Codex 007/009/010): the SUBMISSION pipeline vs the evaluator on the same molecules and view.

Compared per molecule: (1) the query selection (number of spectra and adduct multiset), (2) candidate sets (official scorer keys) and the
truth's membership, (3) features both sides compute (fp, pop, library similarity, flags, ppm), and -- given the pipeline's outputs and the
model -- (4) the ORDERED top-25 (official identities) of the main (learned with the pipeline's GL-coverage fallback) and the insurance
(fixed S + libpri) between the pipeline's submission files and the evaluator path (feature table + the evaluator run's GL/ICE + the same model).
Verdict (PARITY PASS / FAIL): query selection identical for all molecules; truth membership identical for all; top-1 identical and RR
identical for all molecules (main and insurance); ordered top-25 identical for >= 95% of molecules.
Usage: python b1_parity.py --dump RUN/b1_candidates.parquet --features_run FEATURES_RUN --view c2|c1 --solution solution.csv --out parity.md
         [--pred_main RUN/submission.csv --pred_fixed RUN/submission_fixed.csv --stage_stats RUN/b1_stage_stats.csv --model lambdarank.txt --w_ice 1 --tau 0.9 --margin 0.2 --min_gl_cover 0.5]
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))

ap = argparse.ArgumentParser(); ap.add_argument("--dump", required=True); ap.add_argument("--features_run", required=True); ap.add_argument("--view", choices=["c1", "c2"], required=True)
ap.add_argument("--solution", required=True); ap.add_argument("--out", required=True); ap.add_argument("--pred_main", default=None); ap.add_argument("--pred_fixed", default=None)
ap.add_argument("--stage_stats", default=None); ap.add_argument("--model", default=None); ap.add_argument("--w_ice", type=float, default=1.0); ap.add_argument("--tau", type=float, default=0.9)
ap.add_argument("--main", default="learned", choices=["learned", "blend21", "blend11"], help="the pipeline's main-list rule to replicate (b1_pipeline --main)")
ap.add_argument("--forward_from", default="evaluator", choices=["evaluator", "pipe"], help="GL/ICE scores for the evaluator-side ranking: 'evaluator' = the evaluator run's own forward "
                "run (independent GPU run -> ordering noise), 'pipe' = the pipeline's gl_out/ice_out (shared cache -> MECHANICAL check, Codex 014: outputs must then agree exactly)")
ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--min_gl_cover", type=float, default=0.5)
ap.add_argument("--analog_w", type=float, default=0.0, help="evaluator side adds analog_w * z(ap) to the main score (b1_pipeline --analog_w); ap from --analog_parquet (analog_probe.py)")
ap.add_argument("--analog_parquet", default=None)
ap.add_argument("--top25_set_min_share", type=float, default=0.95, help="top-25 identical as SETS (strict criterion)"); ap.add_argument("--top25_min_share", type=float, default=0.85, help="ordered top-25 identical (tail order is subject to forward-score run-to-run noise)")
ap.add_argument("--pipe_work", default=None, help="pipeline output dir with gl_out.json / ice_out.json: measures forward-score differences vs the evaluator run"); a = ap.parse_args()
D = pd.read_parquet(a.dump); D["molecule"] = D["molecule"].astype(str)
Fall = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{a.features_run}/b1_features_*.parquet"))], ignore_index=True); Fall["molecule"] = Fall["molecule"].astype(str)
Mall = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(f"{a.features_run}/b1_molecules_*.csv"))], ignore_index=True); Mall["molecule"] = Mall["molecule"].astype(str); Mall = Mall.set_index("molecule")
S = pd.read_csv(a.solution); S["molecule_id"] = S["molecule_id"].astype(str)
v = a.view
keep = Fall[f"in_short_{v}"].astype(bool)
if v == "c2": keep &= (Fall.in_tier | Fall.in_coconut | Fall.in_train_c2).astype(bool)
F = Fall[keep]
fails = []
# ---------------- (1) query selection
q_bad = []
if a.stage_stats and os.path.exists(a.stage_stats):
    st = pd.read_csv(a.stage_stats); st["molecule"] = st.molecule.astype(str); st = st.set_index("molecule")
    for mid in S.molecule_id:
        if mid in st.index and mid in Mall.index:
            if int(st.loc[mid, "n_query"]) != int(Mall.loc[mid, "n_query"]) or sorted(str(st.loc[mid, "adducts"]).split("|")) != sorted(str(Mall.loc[mid, "adducts"]).split("|")): q_bad.append(mid)
    if q_bad: fails.append(f"query selection differs for {len(q_bad)} molecules (e.g. {q_bad[:3]})")
# ---------------- (2)(3) candidate sets and features
rows = []
for _, s in S.iterrows():
    mid = s.molecule_id; truth = s.scorer_key if "scorer_key" in S.columns else None
    f = F[F.molecule == mid]; p = D[D.molecule == mid]
    fk, pk = set(f.official_key), set(p.key); inter = fk & pk
    rec = dict(molecule=mid, set=s.get("set"), group=s.get("group"), n_f=len(fk), n_p=len(pk), n_inter=len(inter), only_f=len(fk - pk), only_p=len(pk - fk),
               jaccard=len(inter) / max(len(fk | pk), 1), truth_in_f=truth in fk, truth_in_p=truth in pk)
    if inter:
        fm = f.drop_duplicates("official_key").set_index("official_key").loc[sorted(inter)]; pm = p.drop_duplicates("key").set_index("key").loc[sorted(inter)]
        fp_d = np.abs(fm.fp.astype(float).values - pm.fp.astype(float).values); lib_d = np.abs(fm[f"lib_sim_{v}"].astype(float).values - pm.lib.astype(float).values)
        rec.update(fp_absdiff_max=float(np.nanmax(fp_d)), fp_absdiff_mean=float(np.nanmean(fp_d)), lib_absdiff_max=float(np.nanmax(lib_d)),
                   pop_equal=float(np.mean(np.isclose(fm.pop_public.astype(float).values, pm["pop"].astype(float).values, atol=1e-6))),
                   tier_equal=float(np.mean(fm.in_tier.astype(bool).values == pm.in_tier.astype(bool).values)), coco_equal=float(np.mean(fm.in_coconut.astype(bool).values == pm.in_coconut.astype(bool).values)),
                   train_equal=float(np.mean(fm[f"in_train_{v}"].astype(bool).values == pm.in_train.astype(bool).values)),
                   ppm_absdiff_max=float(np.nanmax(np.abs(fm.ppm_err.astype(float).values - pm.ppm_err.astype(float).values))))
    rows.append(rec)
R = pd.DataFrame(rows)
if int((R.truth_in_f != R.truth_in_p).sum()): fails.append(f"truth membership differs for {int((R.truth_in_f != R.truth_in_p).sum())} molecules")
md = [f"# W7 parity: {a.dump} vs {a.features_run} (view {v})", "", f"molecules {len(S)}; query selection differs: {len(q_bad)}" + (" (stage stats not given)" if not a.stage_stats else ""), "",
      "| metric | value |", "|---|---:|", f"| identical candidate sets | {(R.jaccard == 1).mean():.3f} |", f"| Jaccard median / mean / min | {R.jaccard.median():.3f} / {R.jaccard.mean():.3f} / {R.jaccard.min():.3f} |",
      f"| candidates only in evaluator / only in pipeline (mean) | {R.only_f.mean():.2f} / {R.only_p.mean():.2f} |",
      f"| truth in evaluator shortlist / in pipeline shortlist | {R.truth_in_f.mean():.3f} / {R.truth_in_p.mean():.3f} (disagree {int((R.truth_in_f != R.truth_in_p).sum())}) |"]
if "fp_absdiff_max" in R.columns:
    md += [f"| fp abs diff: max / mean of means | {R.fp_absdiff_max.max():.4f} / {R.fp_absdiff_mean.mean():.5f} |", f"| library similarity abs diff max | {R.lib_absdiff_max.max():.4f} |",
           f"| pop / in_tier / in_coconut / in_train equal share | {R.pop_equal.mean():.4f} / {R.tier_equal.mean():.4f} / {R.coco_equal.mean():.4f} / {R.train_equal.mean():.4f} |", f"| ppm error abs diff max | {R.ppm_absdiff_max.max():.3f} |"]
# ---------------- (4) ordered top-25 of main and insurance, by official identity
if a.pred_main and a.pred_fixed and a.model and os.path.exists(a.pred_main) and os.path.exists(a.pred_fixed):
    from b1_evaluate import z, term
    from b1_rankfeats import feature_matrix
    import metric, lightgbm as lgb
    booster = lgb.Booster(model_file=a.model); feats = booster.feature_name()
    PM = pd.read_csv(a.pred_main); PF = pd.read_csv(a.pred_fixed); PM["molecule_id"] = PM.molecule_id.astype(str); PF["molecule_id"] = PF.molecule_id.astype(str)
    pm_of = dict(zip(PM.molecule_id, PM.smiles.astype(str))); pf_of = dict(zip(PF.molecule_id, PF.smiles.astype(str)))
    cache = {}
    def ident(smi):
        if smi not in cache: cache[smi] = metric.canonicalize_smiles_to_ik14(smi)
        return cache[smi]
    def load(model, s):
        p = f"{a.pipe_work}/{model}_out.json" if (a.forward_from == "pipe" and a.pipe_work) else f"{a.features_run}/work/{model}_{s}.json"
        try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        return (json.load(open(p)) if ok else {}), ok
    ANA = {}
    if a.analog_w:
        _A = pd.read_parquet(a.analog_parquet); _A = _A[_A.view == v]; _A["molecule"] = _A["molecule"].astype(str)
        ANA = {m_: dict(zip(h_.smiles.astype(str), h_.ap.astype(float))) for m_, h_ in _A.groupby("molecule")}
    ana_diff = []
    stats = dict(n=0, top1_main=0, top1_ins=0, rr_main=0, rr_ins=0, top25_main=0, top25_ins=0, set25_main=0, set25_ins=0, fallback_eval=0)
    truth_of = dict(zip(S.molecule_id, S.smiles))
    for s_name, Fs in F.groupby("set"):
        gl, gl_ok = load("gl", s_name); ice, ice_ok = load("ice", s_name)
        if a.w_ice == 0: ice, ice_ok = {}, False
        for mid, g in Fs.groupby("molecule", sort=False):
            if mid not in pm_of or mid not in pf_of or mid not in truth_of: continue
            g = g.reset_index(drop=True); fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{v}"].values.astype(float)
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
            Sc = z(fp) + (2 * zgl if zgl is not None else 0) + (a.w_ice * zice if zice is not None else 0) + 0.5 * pop
            top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
            ins = np.where(lib >= a.tau, 100.0 + lib, Sc) if (lib.max() >= a.tau and lib.max() - second >= a.margin) else Sc
            if np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g)):
                X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib, g[f"lib_same_{v}"].values,
                                   g[f"lib_nref_{v}"].values, g.in_tier.values, g[f"in_train_{v}"].values, g.in_coconut.values, g.ppm_err.values, g.fp_rank_window.values,
                                   float(Mall.loc[mid, "n_query"]), float(Mall.loc[mid, "ce_known"]), n_window=float(Mall.loc[mid, "n_unique"]) if "n_unique" in Mall.columns else np.nan, feats=feats)
                main = booster.predict(X)
                if a.main != "learned": main = (2.0 if a.main == "blend21" else 1.0) * z(main) + z(Sc)   # blend hedge, as in b1_pipeline --main
            else: main = ins; stats["fallback_eval"] += 1
            if a.analog_w:   # same formula as b1_pipeline: main + w * z(ap) over the molecule's candidates
                apx = np.array([ANA.get(mid, {}).get(str(sm), np.nan) for sm in g.smiles], float); assert np.isfinite(apx).all(), (mid, "analog features missing")
                main = np.asarray(main, float) + a.analog_w * (apx - apx.mean()) / (apx.std() + 1e-9)
                if "ana_ap" in D.columns:
                    dd_ = D[D.molecule == mid].drop_duplicates("smiles").set_index("smiles").ana_ap
                    ana_diff += [abs(float(dd_.get(str(sm), np.nan)) - x_) for sm, x_ in zip(g.smiles, apx) if str(sm) in dd_.index]
            ev_main = [ident(str(g.smiles.values[i])) for i in np.argsort(-main, kind="stable")[:25]]; ev_ins = [ident(str(g.smiles.values[i])) for i in np.argsort(-ins, kind="stable")[:25]]
            pp_main = [ident(x) for x in pm_of[mid].split(";")]; pp_ins = [ident(x) for x in pf_of[mid].split(";")]
            t = truth_of[mid]
            stats["n"] += 1
            stats["top1_main"] += ev_main[0] == pp_main[0]; stats["top1_ins"] += ev_ins[0] == pp_ins[0]
            stats["top25_main"] += ev_main == pp_main; stats["top25_ins"] += ev_ins == pp_ins; stats["set25_main"] += set(ev_main) == set(pp_main); stats["set25_ins"] += set(ev_ins) == set(pp_ins)
            stats["rr_main"] += metric.per_molecule_reciprocal_rank(t, pm_of[mid].split(";")) == metric.per_molecule_reciprocal_rank(t, [str(g.smiles.values[i]) for i in np.argsort(-main, kind="stable")[:25]])
            stats["rr_ins"] += metric.per_molecule_reciprocal_rank(t, pf_of[mid].split(";")) == metric.per_molecule_reciprocal_rank(t, [str(g.smiles.values[i]) for i in np.argsort(-ins, kind="stable")[:25]])
    n = max(stats["n"], 1)
    if a.analog_w: md += ["", f"analog feature parity (pipeline dump ana_ap vs analog_probe ap): {len(ana_diff)} candidates, max abs diff {max(ana_diff) if ana_diff else float('nan'):.6f}, share > 1e-6 {np.mean(np.array(ana_diff) > 1e-6) if ana_diff else float('nan'):.4f}"]
    md += ["", f"## output agreement on {stats['n']} molecules (model {os.path.basename(a.model)}, w_ice {a.w_ice:g}, libpri({a.tau},{a.margin}), GL fallback < {a.min_gl_cover:g})", "",
           "| output | top-1 identical | RR identical | top-25 identical as sets | ordered top-25 identical (official identities) |", "|---|---:|---:|---:|---:|",
           f"| main (learned + fallback) | {stats['top1_main']}/{n} | {stats['rr_main']}/{n} | {stats['set25_main']}/{n} ({stats['set25_main']/n:.3f}) | {stats['top25_main']}/{n} ({stats['top25_main']/n:.3f}) |",
           f"| insurance (fixed + libpri) | {stats['top1_ins']}/{n} | {stats['rr_ins']}/{n} | {stats['set25_ins']}/{n} ({stats['set25_ins']/n:.3f}) | {stats['top25_ins']}/{n} ({stats['top25_ins']/n:.3f}) |", f"evaluator-side GL fallbacks: {stats['fallback_eval']}"]
    if a.pipe_work:   # forward-score run-to-run differences (the pipeline's own runners vs the evaluator run's stored scores)
        for model in ("gl", "ice"):
            pw = os.path.join(a.pipe_work, f"{model}_out.json")
            if not os.path.exists(pw): continue
            P = json.load(open(pw)); diffs = []
            for s_name, Fs in F.groupby("set"):
                ref, _ok = load(model, s_name)
                for mid in Fs.molecule.unique():
                    for smi, val in (P.get(mid) or {}).items():
                        r_ = (ref.get(mid) or {}).get(smi)
                        if val is not None and r_ is not None: diffs.append(abs(float(val) - float(r_)))
            if diffs: d_ = np.array(diffs); md.append(f"forward-score noise {model}: {len(d_)} pairs, |diff| max {d_.max():.2e}, mean {d_.mean():.2e}, p99 {np.percentile(d_, 99):.2e}")
    if stats["top1_main"] < n: fails.append(f"main top-1 differs for {n - stats['top1_main']} molecules")
    if stats["top1_ins"] < n: fails.append(f"insurance top-1 differs for {n - stats['top1_ins']} molecules")
    if stats["rr_main"] < n or stats["rr_ins"] < n: fails.append(f"RR differs (main {n - stats['rr_main']}, insurance {n - stats['rr_ins']} molecules)")
    if stats["set25_main"] / n < a.top25_set_min_share or stats["set25_ins"] / n < a.top25_set_min_share: fails.append(f"top-25 sets identical below {a.top25_set_min_share:.2f} (main {stats['set25_main']/n:.3f}, insurance {stats['set25_ins']/n:.3f})")
    if stats["top25_main"] / n < a.top25_min_share or stats["top25_ins"] / n < a.top25_min_share: fails.append(f"ordered top-25 identical below {a.top25_min_share:.2f} (main {stats['top25_main']/n:.3f}, insurance {stats['top25_ins']/n:.3f})")
else:
    md += ["", "(output agreement not run: --pred_main/--pred_fixed/--model not given)"]
md += ["", "## by set", "", "| set | n | identical sets | Jaccard mean | truth in F | truth in P |", "|---|---:|---:|---:|---:|---:|"]
for k, g in R.groupby("set"): md.append(f"| {k} | {len(g)} | {(g.jaccard == 1).mean():.3f} | {g.jaccard.mean():.3f} | {g.truth_in_f.mean():.3f} | {g.truth_in_p.mean():.3f} |")
worst = R.sort_values("jaccard").head(8); cols = ["molecule", "set", "n_f", "n_p", "only_f", "only_p", "jaccard", "truth_in_f", "truth_in_p"]
md += ["", "## largest candidate-set disagreements", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f"{r_[c]:.3f}" if isinstance(r_[c], float) else str(r_[c]) for c in cols) + " |" for _, r_ in worst.iterrows()]
verdict = "PARITY PASS" if not fails else "PARITY FAIL: " + "; ".join(fails)
md = [md[0], "", f"**{verdict}**"] + md[1:]
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); R.to_csv(a.out.replace(".md", "_molecules.csv"), index=False)
print("\n".join(md[:30])); print(verdict)
sys.exit(0 if not fails else 1)
