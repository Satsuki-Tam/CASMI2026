"""P1 step 3 -- official-identity evaluation of the label-free funnel: stage recall table and ranking variants on identical candidates.

Inputs (per set): <run>/p1_molecules.csv (selection + DB/window recall by stage), <run>/p1_funnel_<set>.csv (window-level ranks),
<run>/p1_shortlist_<set>.parquet (shortlist candidates with official keys, FP score, prior components), optional GLACIER / ICEBERG
runner outputs <run>/work/gl_<set>.json, ice_<set>.json ({mid: {smiles: score|null}}).

Ranking variants (scores z-standardised within the shortlist of each molecule; worst-case ties; RR@25 = 1/rank if rank <= 25 else 0;
molecules whose truth is not in the shortlist score 0 for every variant):
  prior          documentation prior alone (pop_public) -- rank taken over the WHOLE window (raw-key identity; approximate)
  fp             fold-0 FPNet f.z                                     -- exact (shortlist contains the window's FP top-K)
  fp+0.15prior   z(fp) + 0.15 * pop_public (public pipeline lambda)   -- exact (shortlist contains this order's top-K)
  fp+0.5prior    z(fp) + 0.5 * pop_public                             -- shortlist-restricted (approximate)
  gl / ice       forward-model entropy similarity alone (shortlist)
  fp+gl, fp+gl+0.15prior, fp+2gl, fp+ice+gl, ice+gl, fp+ice+gl+0.15prior
Stage table (class-2 proxy): db_present_external -> window_external -> truth_in_window_raw (union window) -> truth_in_shortlist ->
top-25 -> top-1 under fp+gl.  Bootstrap 95% CIs over molecules; paired deltas vs fp and vs fp+gl; strata: group (fit/tune/eval), ce_known.
Usage: python -X utf8 p1_evaluate.py --run DIR [--sets A_timstof B_nplib] [--out DIR]
"""
import argparse, json, os
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")
_FORM = {}


def formula_of(smi):
    if smi not in _FORM:
        m = Chem.MolFromSmiles(smi); _FORM[smi] = CalcMolFormula(m) if m is not None else ""
    return _FORM[smi]


def zgrp(v):
    v = np.asarray(v, float); ok = np.isfinite(v); out = np.zeros_like(v)
    if ok.sum() >= 2 and v[ok].std() > 0: out[ok] = (v[ok] - v[ok].mean()) / v[ok].std()
    return out


GL_FUSE = None
_gdir = os.environ.get("CASMI_GLACIER_DIR")
if _gdir and os.path.isdir(_gdir):
    import sys as _sys; _sys.path.insert(0, _gdir)
    try:
        import gl_fuse as GL_FUSE
    except Exception as _e:
        print("gl_fuse import failed, using the replica:", repr(_e)); GL_FUSE = None


def public_rerank(base, formulas, rescorers, lams, top_n=25):
    if GL_FUSE is not None:                      # the real public function on the base-ordered list
        order = list(np.argsort(-np.nan_to_num(np.asarray(base, float), nan=-1e18), kind="stable"))
        smis = [str(i) for i in order]; scores = [float(np.nan_to_num(np.asarray(base, float)[i], nan=-1e18)) for i in order]; forms = [formulas[i] for i in order]
        dicts = [[None if not np.isfinite(np.asarray(sc, float)[i]) else float(np.asarray(sc, float)[i]) for i in order] for sc in rescorers]
        new = GL_FUSE.rerank_multi(smis, smis, scores, forms, dicts, list(lams), top_n=top_n)
        return [order[j] for j in new]
    return public_rerank_replica(base, formulas, rescorers, lams, top_n)


def public_rerank_replica(base, formulas, rescorers, lams, top_n=25):
    """Replica of the public pipeline's gl_fuse.rerank_multi: inside the top_n of the base order, every same-formula group with >= 2
    members and >= 2 members covered by some re-scorer is re-sorted by z(base) + sum lam_k z(score_k) (z within the group, uncovered -> 0)
    and put back into the same slots. Returns the new order (candidate indices)."""
    order = list(np.argsort(-np.nan_to_num(np.asarray(base, float), nan=-1e18), kind="stable")); m = min(top_n, len(order))
    groups = {}
    for pos in range(m): groups.setdefault(formulas[order[pos]], []).append(pos)
    new = list(order)
    for poss in groups.values():
        if len(poss) < 2: continue
        idxs = [order[p] for p in poss]
        cols = [(np.asarray(sc, float)[idxs], lam) for sc, lam in zip(rescorers, lams)]
        if not any(int(np.isfinite(v).sum()) >= 2 for v, _ in cols): continue
        fused = zgrp(np.asarray(base, float)[idxs])
        for v, lam in cols:
            if int(np.isfinite(v).sum()) >= 2: fused = fused + lam * zgrp(v)
        srt = sorted(range(len(idxs)), key=lambda k: (-fused[k], k))
        for p, k in zip(poss, srt): new[p] = idxs[k]
    return new


def rr_order(order, is_truth):
    pos = [i for i, c in enumerate(order) if is_truth[c]]
    if not pos: return 0.0
    return 1.0 / (pos[0] + 1) if pos[0] < 25 else 0.0

LAM = 0.15
rng = np.random.default_rng(20261024)


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.zeros_like(x)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    return out


def rr(scores, is_truth):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    if not is_truth.any(): return 0.0, None
    t = s[is_truth][0]; rank = int(np.sum(s >= t))
    return (1.0 / rank if rank <= 25 else 0.0), rank


def boot(v, n=20000):
    v = np.asarray(v, float); idx = rng.integers(0, len(v), (n, len(v))); return np.quantile(v[idx].mean(1), [.025, .975]).tolist()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); ap.add_argument("--out", default=None)
    a = ap.parse_args(); out = a.out or f"{a.run}/results"; os.makedirs(out, exist_ok=True)
    mols = pd.read_csv(f"{a.run}/p1_molecules.csv").set_index("molecule")
    md = ["# P1 baseline results (class-2 proxy, [M+H]+, fold-0 FPNet, label-free retrieval)", ""]
    allres = {}
    for s in a.sets:
        fun = pd.read_csv(f"{a.run}/p1_funnel_{s}.csv").set_index("molecule")
        sl = pd.read_parquet(f"{a.run}/p1_shortlist_{s}.parquet")
        def _complete(path):
            try: return os.path.exists(path) and json.load(open(path + ".meta.json")).get("status") == "ok"
            except Exception: return False
        gl = json.load(open(f"{a.run}/work/gl_{s}.json")) if _complete(f"{a.run}/work/gl_{s}.json") else None
        ice = json.load(open(f"{a.run}/work/ice_{s}.json")) if _complete(f"{a.run}/work/ice_{s}.json") else None
        print(f"{s}: GL complete {gl is not None} | ICE complete {ice is not None}")
        rows = []
        for mid, g in sl.groupby("molecule", sort=False):
            is_t = g.is_truth.values.astype(bool); fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float)
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float) if gl else None
            icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float) if ice else None
            rec = dict(molecule=mid, n_shortlist=len(g), truth_in_shortlist=bool(is_t.any()))
            rec["fp"], rec["fp_rank"] = rr(fp, is_t)
            rec["fp+0.15prior"], _ = rr(z(fp) + LAM * pop, is_t); rec["fp+0.5prior"], _ = rr(z(fp) + 0.5 * pop, is_t)
            if glv is not None:
                rec["gl_finite"] = float(np.isfinite(glv).mean()); rec["gl"], rec["gl_rank"] = rr(glv, is_t)
                rec["fp+gl"], rec["fp+gl_rank"] = rr(z(fp) + z(glv), is_t); rec["fp+2gl"], _ = rr(z(fp) + 2 * z(glv), is_t)
                rec["fp+gl+0.15prior"], _ = rr(z(fp) + z(glv) + LAM * pop, is_t); rec["fp+gl+0.5prior"], _ = rr(z(fp) + z(glv) + 0.5 * pop, is_t)
            if icv is not None:
                rec["ice_finite"] = float(np.isfinite(icv).mean()); rec["ice"], _ = rr(icv, is_t); rec["fp+ice"], _ = rr(z(fp) + z(icv), is_t)
                if glv is not None:
                    rec["fp+ice+gl"], _ = rr(z(fp) + z(icv) + z(glv), is_t); rec["ice+gl"], _ = rr(z(icv) + z(glv), is_t)
                    rec["fp+ice+gl+0.15prior"], _ = rr(z(fp) + z(icv) + z(glv) + LAM * pop, is_t)
            # public-pipeline replica: base list z(fp) + 0.15 pop, then same-formula slot rerank inside the top 25 with ICE_LAM = GL_LAM = 1
            if glv is not None:
                forms = [formula_of(sm) for sm in g.smiles]; base = z(fp) + LAM * pop
                rec["public: fp+0.15prior>sf25(gl)"] = rr_order(public_rerank(base, forms, [glv], [1.0]), is_t)
                rec["public: fp>sf25(gl)"] = rr_order(public_rerank(z(fp), forms, [glv], [1.0]), is_t)
                if icv is not None:
                    rec["public: fp+0.15prior>sf25(ice,gl)"] = rr_order(public_rerank(base, forms, [icv, glv], [1.0, 1.0]), is_t)
                    rec["public: fp>sf25(ice,gl)"] = rr_order(public_rerank(z(fp), forms, [icv, glv], [1.0, 1.0]), is_t)
            rows.append(rec)
        df = pd.DataFrame(rows).set_index("molecule")
        # molecules without any shortlist row (empty window) still count
        df = df.reindex(fun.index)
        df["truth_in_shortlist"] = df.truth_in_shortlist.fillna(False).astype(bool)
        variants = [c for c in ("fp", "fp+0.15prior", "fp+0.5prior", "gl", "ice", "fp+gl", "fp+2gl", "fp+gl+0.15prior", "fp+gl+0.5prior", "fp+ice", "ice+gl", "fp+ice+gl", "fp+ice+gl+0.15prior",
                                "public: fp>sf25(gl)", "public: fp+0.15prior>sf25(gl)", "public: fp>sf25(ice,gl)", "public: fp+0.15prior>sf25(ice,gl)") if c in df.columns]
        for c in variants: df[c] = df[c].fillna(0.0)
        pr = fun.truth_pop_rank_window.astype(float); df["prior"] = np.where(np.isfinite(pr) & (pr <= 25), 1.0 / pr.clip(lower=1), 0.0)
        variants = ["prior"] + variants
        df = df.join(fun[["group", "lib", "n_unique", "n_unique_external_only", "truth_in_window_raw", "truth_fp_rank_window", "truth_fpprior_rank_window", "n_spectra", "ce_known", "seconds"]])
        df = df.join(mols[["db_present_external", "window_external", "window_train", "truth_in_pool_ext", "truth_in_coco", "truth_in_tier_window", "truth_in_tier_exact", "n_tier_window", "n_tier_same_formula", "ppm_err_measured", "instruments"]])
        ref = "fp+gl" if "fp+gl" in df.columns else "fp"
        rk = df[f"{ref}_rank"] if f"{ref}_rank" in df.columns else df["fp_rank"]
        df["drop_stage"] = np.select([~df.db_present_external.astype(bool), ~df.window_external.astype(bool), ~df.truth_in_shortlist, rk.isna() | (rk > 25), rk > 1],
                                     ["not_in_external_db", "mass_window_miss", "not_in_shortlist", "rank_gt_25", "rank_2_25"], default="rank_1")
        N = len(df)
        res = dict(set=s, n=N, reference=ref,
                   stages={k: int(df[k].astype(bool).sum()) for k in ("db_present_external", "window_external", "truth_in_window_raw", "truth_in_shortlist")},
                   stages_ref={"top25": int((rk <= 25).sum()), "top1": int((rk == 1).sum())}, drop_stage=df.drop_stage.value_counts().to_dict(),
                   median_window_unique=float(df.n_unique.median()), median_external_only=float(df.n_unique_external_only.median()),
                   median_fp_rank_window=float(df.truth_fp_rank_window.median()), seconds_per_molecule_funnel=float(df.seconds.mean()), variants={}, deltas={}, by_group={}, by_ce={})
        # strict class-2 proxy: a truth that is reachable only as a train-library structure (window_external False) would not be a
        # candidate for a genuinely novel-to-libraries molecule -> counts as 0; also report the conditional value on reachable molecules
        reach = df.window_external.astype(bool).values
        for v in variants:
            x = df[v].values.astype(float); xs = x * reach
            res["variants"][v] = dict(mrr25=float(x.mean()), ci95=boot(x), top1=float((x == 1).mean()), hit25=float((x > 0).mean()),
                                      mrr25_strict=float(xs.mean()), ci95_strict=boot(xs), top1_strict=float((xs == 1).mean()), hit25_strict=float((xs > 0).mean()),
                                      mrr25_reachable=float(x[reach].mean()) if reach.any() else None, n_reachable=int(reach.sum()))
        for v in variants:
            for b in ("fp", "fp+gl"):
                if b in df.columns and v != b:
                    d = df[v].values.astype(float) - df[b].values.astype(float)
                    res["deltas"][f"{v} - {b}"] = dict(delta=float(d.mean()), ci95=boot(d), delta_strict=float((d * reach).mean()), ci95_strict=boot(d * reach))
        df["_reach"] = reach
        for gname, gd in df.groupby("group"):
            res["by_group"][gname] = {v: float(gd[v].mean()) for v in variants} | {f"{v}_strict": float((gd[v] * gd._reach).mean()) for v in variants} | {"n": len(gd)}
        for flag, gd in df.groupby(df.ce_known > 0.5):
            res["by_ce"][f"ce_known={bool(flag)}"] = {v: float(gd[v].mean()) for v in variants} | {"n": len(gd)}
        allres[s] = res
        df.to_csv(f"{out}/p1_per_molecule_{s}.csv")
        # ---- markdown
        md += [f"## {s} (N={N}; libs {df.lib.value_counts().to_dict()}; CE known for {int((df.ce_known > 0.5).sum())} molecules)", "",
               "| stage | molecules | share |", "|---|---:|---:|"]
        for k, v in res["stages"].items(): md.append(f"| {k} | {v} | {v/N:.3f} |")
        md += [f"| top-25 ({ref}) | {res['stages_ref']['top25']} | {res['stages_ref']['top25']/N:.3f} |", f"| top-1 ({ref}) | {res['stages_ref']['top1']} | {res['stages_ref']['top1']/N:.3f} |", "",
               f"drop stage ({ref}): " + ", ".join(f"{k} {v}" for k, v in res["drop_stage"].items()), "",
               f"window: median {res['median_window_unique']:.0f} unique structures (median {res['median_external_only']:.0f} not in train libraries); median FP rank of truth in window {res['median_fp_rank_window']:.0f}; funnel {res['seconds_per_molecule_funnel']:.1f} s/molecule", "",
               f"| variant | MRR@25 (all, truth kept if only in train pool) | 95% CI | top-1 | hit@25 | Δ vs fp | Δ vs fp+gl | MRR@25 strict class-2 (unreachable = 0) | MRR@25 on reachable (n={int(reach.sum())}) |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for v in variants:
            r = res["variants"][v]; d1 = res["deltas"].get(f"{v} - fp"); d2 = res["deltas"].get(f"{v} - fp+gl")
            f = lambda d: (f"{d['delta']:+.3f} [{d['ci95'][0]:+.3f},{d['ci95'][1]:+.3f}]" if d else "")
            md.append(f"| {v} | {r['mrr25']:.3f} | [{r['ci95'][0]:.3f},{r['ci95'][1]:.3f}] | {r['top1']:.3f} | {r['hit25']:.3f} | {f(d1)} | {f(d2)} | {r['mrr25_strict']:.3f} [{r['ci95_strict'][0]:.3f},{r['ci95_strict'][1]:.3f}] | {r['mrr25_reachable']:.3f} |")
        md += ["", "by group (MRR@25): " + "; ".join(f"{g}: " + ", ".join(f"{v} {res['by_group'][g][v]:.3f}" for v in ("fp", "fp+0.15prior", "fp+gl", "fp+gl+0.15prior") if v in res['by_group'][g]) + f" (n={res['by_group'][g]['n']})" for g in res["by_group"]), ""]
        if len(res["by_ce"]) > 1:
            md += ["by CE availability (MRR@25): " + "; ".join(f"{k}: " + ", ".join(f"{v} {res['by_ce'][k][v]:.3f}" for v in ("fp", "fp+gl", "fp+ice+gl") if v in res['by_ce'][k]) + f" (n={res['by_ce'][k]['n']})" for k in res["by_ce"]), ""]
        print("\n".join(md[-(len(variants) + 20):]))
    json.dump(allres, open(f"{out}/p1_results.json", "w"), indent=1); open(f"{out}/p1_results.md", "w", encoding="utf-8").write("\n".join(md))
    print("saved", out)


if __name__ == "__main__":
    main()
