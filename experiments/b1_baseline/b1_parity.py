"""W7 parity test (Codex 007/009): the submission pipeline's candidate dump vs the evaluator's feature table on the same molecules and view,
and -- when the pipeline's fixed-rule submission is given -- the agreement of the two paths' fixed-rule top-25 lists and per-molecule RR.

Compared per molecule: candidate sets (official scorer keys), truth membership, features both sides compute (fp, pop, library similarity
of the view, in_tier / in_coconut / in_train, ppm error); with --pred_csv: top-1 agreement, |ΔRR| between the pipeline's fixed output and
the evaluator's fixed rule S(2, w_ice, 0.5) (+ libpri tau/margin) computed from the feature table and the evaluator run's GL/ICE scores.
Usage: python b1_parity.py --dump <pipeline_out>/b1_candidates.parquet --features_run experiments/b1_baseline/run1_v2 --view c2 --solution <eval_test>/solution.csv
                           --out <pipeline_out>/parity_c2.md [--pred_csv <pipeline_out>/submission_fixed.csv --w_ice 1 --tau 0.9 --margin 0.2]
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))

ap = argparse.ArgumentParser(); ap.add_argument("--dump", required=True); ap.add_argument("--features_run", required=True); ap.add_argument("--view", choices=["c1", "c2"], required=True)
ap.add_argument("--solution", required=True); ap.add_argument("--out", required=True); ap.add_argument("--pred_csv", default=None); ap.add_argument("--w_ice", type=float, default=1.0)
ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); a = ap.parse_args()
D = pd.read_parquet(a.dump); D["molecule"] = D["molecule"].astype(str)
F = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{a.features_run}/b1_features_*.parquet"))], ignore_index=True); F["molecule"] = F["molecule"].astype(str)
S = pd.read_csv(a.solution); S["molecule_id"] = S["molecule_id"].astype(str)
v = a.view
keep = F[f"in_short_{v}"].astype(bool)
if v == "c2": keep &= (F.in_tier | F.in_coconut | F.in_train_c2).astype(bool)
F = F[keep]
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
md = [f"# W7 parity: {a.dump} vs {a.features_run} (view {v})", "", f"molecules in solution {len(S)}; with candidates on both sides {int(((R.n_f > 0) & (R.n_p > 0)).sum())}; "
      f"features side only {int(((R.n_f > 0) & (R.n_p == 0)).sum())}; pipeline side only {int(((R.n_f == 0) & (R.n_p > 0)).sum())}", "",
      "| metric | value |", "|---|---:|",
      f"| identical candidate sets | {(R.jaccard == 1).mean():.3f} |", f"| Jaccard median / mean / min | {R.jaccard.median():.3f} / {R.jaccard.mean():.3f} / {R.jaccard.min():.3f} |",
      f"| candidates only in evaluator (mean) | {R.only_f.mean():.1f} |", f"| candidates only in pipeline (mean) | {R.only_p.mean():.1f} |",
      f"| truth in evaluator shortlist / in pipeline shortlist | {R.truth_in_f.mean():.3f} / {R.truth_in_p.mean():.3f} |",
      f"| truth membership disagrees | {int((R.truth_in_f != R.truth_in_p).sum())} molecules |"]
if "fp_absdiff_max" in R.columns:
    md += [f"| fp abs diff: max over molecules of per-molecule max / mean of means | {R.fp_absdiff_max.max():.4f} / {R.fp_absdiff_mean.mean():.5f} |",
           f"| library similarity abs diff max | {R.lib_absdiff_max.max():.4f} |", f"| pop equal share (mean) | {R.pop_equal.mean():.4f} |",
           f"| in_tier / in_coconut / in_train equal share (mean) | {R.tier_equal.mean():.4f} / {R.coco_equal.mean():.4f} / {R.train_equal.mean():.4f} |",
           f"| ppm error abs diff max | {R.ppm_absdiff_max.max():.3f} |"]
md += ["", "## by set", "", "| set | n | identical sets | Jaccard mean | truth in F | truth in P |", "|---|---:|---:|---:|---:|---:|"]
for k, g in R.groupby("set"): md.append(f"| {k} | {len(g)} | {(g.jaccard == 1).mean():.3f} | {g.jaccard.mean():.3f} | {g.truth_in_f.mean():.3f} | {g.truth_in_p.mean():.3f} |")
# ---- fixed-rule output agreement: the pipeline's fixed submission vs the evaluator's fixed rule from the feature table + the run's forward scores
if a.pred_csv and os.path.exists(a.pred_csv):
    from b1_evaluate import z, term
    import metric
    P = pd.read_csv(a.pred_csv); P["molecule_id"] = P["molecule_id"].astype(str); pred_p = dict(zip(P.molecule_id, P.smiles.astype(str)))
    def load(model, s):
        p = f"{a.features_run}/work/{model}_{s}.json"
        try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        return (json.load(open(p)) if ok else {}), ok
    agree1 = []; drr = []; both = 0
    for s_name, Fs in F.groupby("set"):
        gl, gl_ok = load("gl", s_name); ice, ice_ok = load("ice", s_name)
        if a.w_ice == 0: ice, ice_ok = {}, False
        for mid, g in Fs.groupby("molecule", sort=False):
            if mid not in pred_p or mid not in set(S.molecule_id): continue
            g = g.reset_index(drop=True); fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{v}"].values.astype(float)
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
            Sc = z(fp) + (2 * zgl if zgl is not None else 0) + (a.w_ice * zice if zice is not None else 0) + 0.5 * pop
            top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
            if lib.max() >= a.tau and lib.max() - second >= a.margin: Sc = np.where(lib >= a.tau, 100.0 + lib, Sc)
            ev_top = [str(g.smiles.values[i]) for i in np.argsort(-Sc, kind="stable")[:25]]; pp = pred_p[mid].split(";")
            truth_smi = S.set_index("molecule_id").loc[mid, "smiles"]
            agree1.append(metric.inchikey14_identity(ev_top[0]) == metric.inchikey14_identity(pp[0]) if hasattr(metric, "inchikey14_identity") else ev_top[0] == pp[0])
            drr.append(metric.per_molecule_reciprocal_rank(truth_smi, pp) - metric.per_molecule_reciprocal_rank(truth_smi, ev_top)); both += 1
    if both:
        drr = np.array(drr)
        md += ["", f"## fixed-rule output agreement ({both} molecules; evaluator rule S(2,{a.w_ice:g},0.5)+libpri({a.tau},{a.margin}) from {a.features_run})", "",
               f"top-1 identical: {np.mean(agree1):.3f} | mean RR(pipeline) − RR(evaluator): {drr.mean():+.4f} | molecules with |ΔRR| > 0: {int((np.abs(drr) > 1e-9).sum())}"]
worst = R.sort_values("jaccard").head(10); cols = ["molecule", "set", "n_f", "n_p", "n_inter", "only_f", "only_p", "jaccard", "truth_in_f", "truth_in_p"]
md += ["", "## largest disagreements", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f"{r_[c]:.3f}" if isinstance(r_[c], float) else str(r_[c]) for c in cols) + " |" for _, r_ in worst.iterrows()]
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); R.to_csv(a.out.replace(".md", "_molecules.csv"), index=False)
print("\n".join(md[:24]))
