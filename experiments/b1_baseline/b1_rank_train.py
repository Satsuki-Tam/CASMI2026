"""B1 step 3 -- learned fusion (LightGBM LambdaRank) on the unified candidate table, compared with the fixed rule on the same molecules.

Training rows: shortlist candidates of molecules in the FIT groups of the given runs, under both scenario views (C2 and, where
possible, C1) -- the two views of one molecule are one 'identity' and always stay in the same split. Features are molecule-relative
(z within the shortlist) plus raw values and flags; the label is is_truth. Model selection (num_leaves / learning rate / rounds) uses
the TUNE groups; the EVAL groups are scored once with the selected setting and reported next to the fixed rules S(2,1,0.5) (reference) and S(2,1,0.15).
Usage: python -X utf8 b1_rank_train.py --runs RUN:eval_csv[:group_override] ... [--out DIR]   (e.g. run_p1:...:fit uses all P1 molecules as fit)
       e.g. --runs experiments/b1_baseline/run1:experiments/b1_baseline/eval_set/p1_molecules.csv experiments/b1_baseline/run_c1:...
"""
import glob, argparse, json, os, sys
import numpy as np, pandas as pd
import lightgbm as lgb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_evaluate import z, rr, boot, term, LAM
from b1_rankfeats import FEATS, FEATSETS, MONO, MONO_LIB, feature_matrix



FRG = {}    # (set, molecule) -> {smiles: frag} from --frag_parquet (039)
ANA = {}    # (set, view, molecule) -> {smiles: (ap, mean_tan)} from --analog_parquet (analog_probe.py); used only when the feature list asks for the analog block
CMPX = {}   # 078: (run basename, set, molecule, official key) -> (n_cmp_pol_c1, n_cmp_add_c1, n_cmp_pol_c2, n_cmp_add_c2) from diag/refcmpx_<run>.parquet (refcmp_exact.py)
EXPO = {}   # official key -> (fp_pos, negpool) from --exposure_ledger (Codex 028); used only when the feature list asks for the exposure block


def exposure_of(keys):
    fp_ = np.array([EXPO.get(str(k), (0.0, 0.0))[0] for k in keys], float); ng_ = np.array([EXPO.get(str(k), (0.0, 0.0))[1] for k in keys], float)
    return dict(fp_pos=fp_, negpool=ng_)


RESTRICT = ""   # 095: '' = full view list (default), 'B' = B-group candidates only; 102: 'E' = E-window candidates only
EKEYS = set()   # 102: official keys of the extra E-window layers (PubChemLite / BIO, diag/e_window_keys.parquet)


def load_run(run, eval_csv, group_override=None, feats=FEATS):
    ev = pd.read_csv(eval_csv).set_index("molecule")
    out = []
    # Codex 017: sets are discovered from the run (b1_features_<set>.parquet) and restricted to the sets of the evaluation CSV, instead of the
    # former hard-coded ("A_timstof", "B_nplib"); the identities / groups actually used are reported per run and set (USED ledger).
    sets_here = sorted(set(ev["set"].astype(str)) & {os.path.basename(f)[len("b1_features_"):-len(".parquet")] for f in glob.glob(f"{run}/b1_features_*.parquet")})
    if not sets_here: print(f"WARNING: no feature table of {run} matches the sets of {eval_csv}", flush=True)
    for s in sets_here:
        fp_ = f"{run}/b1_features_{s}.parquet"
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
                if RESTRICT == "B":   # 095: B-group specialist = COCONUT and not a training structure in this view (T-priority, exclusive); features recomputed within B
                    g = g[g.in_coconut.values.astype(bool) & ~g[f"in_train_{view}"].values.astype(bool)].reset_index(drop=True)
                if RESTRICT == "E":   # 102: second engine E-lite = E window (COCONUT | train in this view | PubChemLite | BIO); features recomputed within the window
                    g = g[g.in_coconut.values.astype(bool) | g[f"in_train_{view}"].values.astype(bool) | g.official_key.astype(str).isin(EKEYS).values].reset_index(drop=True)
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
                                   n_window=float(m["n_unique"]) if "n_unique" in M.columns and np.isfinite(float(m["n_unique"])) else np.nan, feats=feats,
                                   exposure=exposure_of(g.official_key.values) if EXPO else None,
                                   libcond=(dict(sup2=g[f"lib_sup2_{view}"].values, ncond=g[f"lib_ncond_{view}"].values) if f"lib_sup2_{view}" in g.columns else None),
                                   frag=([FRG.get((s, mid), {}).get(str(sm), 0.0) for sm in g.smiles] if FRG else None),
                                   cmp=(dict(n_cmp_pol=[CMPX.get((os.path.basename(run), s, str(mid), str(k_)), (0, 0, 0, 0))[0 if view == "c1" else 2] for k_ in g.official_key],
                                             n_cmp_add=[CMPX.get((os.path.basename(run), s, str(mid), str(k_)), (0, 0, 0, 0))[1 if view == "c1" else 3] for k_ in g.official_key]) if CMPX else None),
                                   analog=(dict(ap=[ANA.get((s, view, mid), {}).get(str(sm), (0.0, 0.0))[0] for sm in g.smiles], mean_tan=[ANA.get((s, view, mid), {}).get(str(sm), (0.0, 0.0))[1] for sm in g.smiles]) if ANA else None))
                d = pd.DataFrame(X, columns=feats)
                d.insert(0, "is_truth", g.is_truth.values.astype(int)); d.insert(0, "identity", mid); d.insert(0, "group", group_override or m.group); d.insert(0, "view", view)
                d.insert(0, "molecule", mid); d.insert(0, "set", s); d.insert(0, "run", run)
                d["S_fixed"] = S; d["S_fixed15"] = S15; d["reachable"] = bool(m["reach_external_b1"]) if "reach_external_b1" in M.columns else (bool(ev.loc[mid, "window_external"]) if mid in ev.index else True)
                d["identity_group"] = int(m["identity_group"]) if "identity_group" in M.columns else -1
                out.append(d)
    T = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    # Codex 017: USED ledger -- what actually enters the training / evaluation tables per run and set (selection counts are not training counts)
    for s_ in sets_here:
        t = T[T.set == s_] if len(T) else T
        if not len(t): print(f"USED {os.path.basename(run)} {s_}: 0 rows", flush=True); continue
        gv = t.groupby(["molecule", "view"]); pos = gv.is_truth.max()
        print(f"USED {os.path.basename(run)} {s_}: identities {t.molecule.nunique()} | groups c1 {int((pos.index.get_level_values(1) == 'c1').sum())} c2 {int((pos.index.get_level_values(1) == 'c2').sum())} "
              f"| groups with a positive c1 {int(pos[pos.index.get_level_values(1) == 'c1'].sum())} c2 {int(pos[pos.index.get_level_values(1) == 'c2'].sum())} | fit/tune/eval {dict(t.groupby('molecule').group.first().value_counts())}", flush=True)
    return T


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
    ap.add_argument("--c1_only_runs", nargs="*", default=[], help="Codex 021: run basenames whose CLASS-2 view rows are dropped from fit/tune/eval (their identities are "
                    "seen by the FPNet that built the table, so a hidden-reference C2 row only measures memory residue)")
    ap.add_argument("--params_from", default="", help="Codex 019: reuse the SELECTED params + rounds of an earlier rank_results.json (no search) so that a pair "
                    "comparison changes only the training rows")
    ap.add_argument("--refcmp", action="store_true", help="078: load diag/refcmpx_<run>.parquet (exact reference comparability) for every run; needed by the v2_noice_cmp feature set")
    ap.add_argument("--restrict", default="", choices=["", "B", "E"], help="095: B = train the ranker on the B-group candidates of each view only (COCONUT and not train; groups whose truth is not B drop out); "
                    "102: E = the E window (COCONUT | train in this view | PubChemLite | BIO keys of --ekeys)")
    ap.add_argument("--ekeys", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag", "e_window_keys.parquet"), help="102: e_keys.py output (key, in_pcl, in_bio)")
    ap.add_argument("--pointwise", action="store_true", help="102: row weights = group weight / group size, rescaled to mean 1 (every (molecule, view) group carries its group weight in total) "
                    "for a pointwise objective given by --params_from (e.g. binary)")
    ap.add_argument("--prior_iw", default="", help="090: target shares of the C2 truths' prior-rank strata (rank by pop_public, fp tie-break: 1 / 2-3 / 4-10 / 11+), e.g. "
                    "0.09,0.18,0.30,0.43 -> every C2 fit group gets weight target/observed of its stratum (C1 groups 1), mean group weight renormalised to 1")
    ap.add_argument("--c1_weight", type=float, default=1.0, help="Codex 075 (b): relative weight of every CLASS-1-view fit group vs class-2 groups (row weights, the mean group "
                    "weight is renormalised to 1); 1.0 = no weights passed = unchanged")
    ap.add_argument("--c1_repeat_run", nargs="*", default=[], help="Codex 019: per-run C1 replication RUN_BASENAME=K overriding --c1_repeat for that run's C1 fit groups "
                    "(e.g. run_fitpool_v3=1 = 'G C1 weight reduced')")
    ap.add_argument("--c2_drop_exposure", default="", help="Codex 021/023: query_identity_exposure.csv of the FPNet that built the tables (molecule, exposure); the CLASS-2 "
                    "view rows of molecules whose identity is trained by that FPNet (exposure c1_seen) are dropped, rows of unseen_after_removal molecules are kept")
    ap.add_argument("--c1_seen_only", default="", help="query_identity_exposure.csv: keep CLASS-1 view rows only for molecules whose identity the table-building FPNet "
                    "was trained on (exposure c1_seen; molecules absent from the table count as unseen) -- leak-free design for FPNet-exposure features (Codex 029)")
    ap.add_argument("--frag_parquet", default="", help="frag_probe.py features of the training tables (v2_noice_ana_frag)")
    ap.add_argument("--analog_parquet", default="", help="analog_probe.py features of the training tables (needed by the v2_noice_ana feature set)")
    ap.add_argument("--exposure_ledger", default="", help="ledger_<checkpoint>.parquet (key, fp_pos, negpool) of the FPNet that built the tables; needed by the v2_noice_exp feature set")
    ap.add_argument("--monotone_lib", action="store_true", help="monotone constraints incl. the library similarities (reference evidence may only raise a candidate)")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); FE = [f for f in FEATSETS[a.feats] if f not in set(a.drop)]
    if a.frag_parquet:
        F_ = pd.read_parquet(a.frag_parquet); F_ = F_[F_.view == "c1"]; F_["molecule"] = F_["molecule"].astype(str)
        for k_, h_ in F_.groupby(["set", "molecule"]): FRG[k_] = dict(zip(h_.smiles.astype(str), h_.frag.astype(float)))
        print(f"frag features {a.frag_parquet}: {len(FRG):,} (set, molecule) groups", flush=True)
    if a.refcmp:   # 078: exact reference comparability per run (refcmp_exact.py output, verified against the tables)
        for spec_ in a.runs:
            run_ = spec_.split(':')[0]; p_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diag', f'refcmpx_{os.path.basename(run_)}.parquet')
            if not os.path.exists(p_): raise FileNotFoundError(p_)
            d_ = pd.read_parquet(p_)
            for r_ in d_.itertuples(index=False): CMPX[(os.path.basename(run_), str(r_.set), str(r_.molecule), str(r_.official_key))] = (int(r_.n_cmp_pol_c1), int(r_.n_cmp_add_c1), int(r_.n_cmp_pol_c2), int(r_.n_cmp_add_c2))
        print('refcmp entries:', len(CMPX), flush=True)
    global RESTRICT; RESTRICT = a.restrict
    if RESTRICT == "E":
        EKEYS.update(pd.read_parquet(a.ekeys).key.astype(str)); print(f"E window: {len(EKEYS):,} PubChemLite / BIO keys from {a.ekeys}", flush=True)
    if a.analog_parquet:
        A_ = pd.read_parquet(a.analog_parquet); A_["molecule"] = A_["molecule"].astype(str)
        for k_, h_ in A_.groupby(["set", "view", "molecule"]): ANA[k_] = dict(zip(h_.smiles.astype(str), zip(h_.ap.astype(float), h_.mean_tan.astype(float))))
        print(f"analog features {a.analog_parquet}: {len(ANA):,} (set, view, molecule) groups", flush=True)
    if a.exposure_ledger:
        L_ = pd.read_parquet(a.exposure_ledger); EXPO.update(zip(L_.key.astype(str), zip(L_.fp_pos.astype(float), L_.negpool.astype(float))))
        print(f"exposure ledger {a.exposure_ledger}: {len(EXPO):,} keys, fp_pos {int(L_.fp_pos.sum()):,}, negpool {int(L_.negpool.sum()):,}", flush=True)
    if a.monotone_lib: a.monotone = True
    MONO_USED = MONO_LIB if a.monotone_lib else MONO
    print("features:", len(FE), "| dropped:", a.drop, "| c1_repeat:", a.c1_repeat, "| c2_nolib:", a.c2_nolib, "| monotone:", a.monotone, "lib" if a.monotone_lib else "")
    data = pd.concat([load_run(*r.split(":"), feats=FE) for r in a.runs], ignore_index=True)   # RUN:eval_csv[:group_override]
    if a.c1_only_runs:
        drop_ = data.run.map(lambda r: os.path.basename(str(r)) in set(a.c1_only_runs)) & (data.view == "c2")
        print(f"c1-only runs {a.c1_only_runs}: dropping {int(drop_.sum()):,} C2 rows ({data[drop_].groupby(['molecule']).ngroups} groups)", flush=True)
        data = data[~drop_].reset_index(drop=True)
    if a.c2_drop_exposure:
        ex_ = pd.read_csv(a.c2_drop_exposure); seen_ = set(ex_.loc[ex_.exposure == "c1_seen", "molecule"].astype(str)); unseen_ = set(ex_.loc[ex_.exposure != "c1_seen", "molecule"].astype(str)) - seen_
        drop_ = data.molecule.astype(str).isin(seen_) & (data.view == "c2")
        print(f"c2 rows of FPNet-seen identities dropped: {int(drop_.sum()):,} rows, {data[drop_].molecule.nunique()} molecules "
              f"(exposure table: {len(seen_)} seen, {len(unseen_)} unseen; molecules not in the table are kept)", flush=True)
        data = data[~drop_].reset_index(drop=True)
    if a.c1_seen_only:
        ex1_ = pd.read_csv(a.c1_seen_only); seen1_ = set(ex1_.loc[ex1_.exposure == "c1_seen", "molecule"].astype(str))
        drop1_ = (data.view == "c1") & ~data.molecule.astype(str).isin(seen1_)
        print(f"c1 rows of identities NOT trained by the FPNet dropped: {int(drop1_.sum()):,} rows, {data[drop1_].molecule.nunique()} molecules (kept c1 molecules: "
              f"{data[(data.view == 'c1') & ~drop1_].molecule.nunique()})", flush=True)
        data = data[~drop1_].reset_index(drop=True)
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
    REP = {kv.split("=")[0]: int(kv.split("=")[1]) for kv in a.c1_repeat_run}
    rep_of = fit_t.run.map(lambda r: REP.get(os.path.basename(str(r)), a.c1_repeat)) if REP else pd.Series(a.c1_repeat, index=fit_t.index)
    if int(rep_of.max()) > 1:
        c1 = fit_t[fit_t.view == "c1"]; c1_rep = rep_of[fit_t.view == "c1"]
        fit_t = pd.concat([fit_t] + [c1[c1_rep > k].assign(molecule=c1[c1_rep > k].molecule.astype(str) + f"#r{k}") for k in range(1, int(rep_of.max()))], ignore_index=True)
        if REP: print("per-run c1 replication:", REP, "(others", a.c1_repeat, ")")
        print("fit groups after c1 replication:", fit_t.groupby(["molecule", "view"]).ngroups, "| c1 share:", round(float((fit_t.groupby(['molecule', 'view']).view.first() == 'c1').mean()), 3))
    def to_ds(d):
        d = d.sort_values(["molecule", "view"], kind="stable")
        sizes = d.groupby(["molecule", "view"], sort=False).size().values
        if a.c1_weight != 1.0 or a.prior_iw or a.pointwise:   # query-level weight carried by every row of the group; mean GROUP weight renormalised to 1
            gview = d.groupby(["molecule", "view"], sort=False).view.first().values
            gw = np.where(gview == "c1", a.c1_weight, 1.0)
            if a.prior_iw:
                tgt = np.array([float(x) for x in a.prior_iw.split(",")]); assert len(tgt) == 4
                def _prank(g):
                    o = np.lexsort((-np.nan_to_num(g.fp.values.astype(float), nan=-1e9), -g.pop_public.values.astype(float))); t = np.flatnonzero(g.is_truth.values[o]); return t[0] + 1 if len(t) else 0
                pr = d.groupby(["molecule", "view"], sort=False).apply(_prank).values
                st = np.digitize(pr, [1.5, 3.5, 10.5])   # 0: rank 1, 1: 2-3, 2: 4-10, 3: 11+
                c2m = gview == "c2"; obs = np.array([(st[c2m] == k).mean() for k in range(4)])
                wk = tgt / np.maximum(obs, 1e-9); gw = np.where(c2m, gw * wk[st], gw)
                print(f"prior_iw: C2 strata observed {np.round(obs, 3).tolist()} -> target {tgt.tolist()} weights {np.round(wk, 3).tolist()}", flush=True)
            gw = gw / gw.mean()
            w_rows = np.repeat(gw, sizes)
            if a.pointwise:   # 102: each group sums to its group weight, rows rescaled to mean 1
                w_rows = np.repeat(gw / sizes, sizes); w_rows = w_rows * (len(w_rows) / w_rows.sum())
                print(f"pointwise weights: {len(sizes):,} groups, {len(w_rows):,} rows, row weight range {w_rows.min():.4f}-{w_rows.max():.4f}", flush=True)
            print(f"c1_weight {a.c1_weight}: group weights c1 {gw[gview == 'c1'][0] if (gview == 'c1').any() else float('nan'):.4f} / c2 {gw[gview == 'c2'][0] if (gview == 'c2').any() else float('nan'):.4f} | "
                  f"effective c1 share {float(gw[gview == 'c1'].sum() / gw.sum()):.4f}", flush=True)
            return lgb.Dataset(d[FE].values, label=d.is_truth.values, group=sizes, weight=w_rows, free_raw_data=False, feature_name=list(FE)), d
        return lgb.Dataset(d[FE].values, label=d.is_truth.values, group=sizes, free_raw_data=False, feature_name=list(FE)), d
    ds_fit, fit_s = to_ds(fit_t)
    FIXED = json.load(open(a.params_from))["selected"] if a.params_from else None
    if FIXED: print("params fixed from", a.params_from, ":", {k: FIXED["params"][k] for k in ("num_leaves", "learning_rate")}, "rounds", FIXED["rounds"], "(no search)")
    grid = [dict(num_leaves=nl, learning_rate=lr, min_data_in_leaf=20, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, objective="lambdarank",
                 metric="ndcg", eval_at=[25], label_gain=[0, 1], seed=0, **({"monotone_constraints": [MONO_USED.get(f, 0) for f in FE], "monotone_constraints_method": "advanced"} if a.monotone else {}))
            for nl in (7, 15, 31) for lr in (0.03, 0.1)]
    results = []
    for params in ([] if FIXED else grid):
        for rounds in (100, 300, 600):
            bst = lgb.train(params, ds_fit, num_boost_round=rounds)
            tune = tune.copy(); tune["pred"] = bst.predict(tune[FE].values)
            m = mrr_of(tune, "pred"); results.append(dict(params=params, rounds=rounds, tune_c2_strict=m.get("c2", {}).get("strict"), tune_c1=m.get("c1", {}).get("mrr"), tune_c2=m.get("c2", {}).get("mrr")))
            print(f"  leaves {params['num_leaves']} lr {params['learning_rate']} rounds {rounds}: tune C2 strict {m.get('c2', {}).get('strict', float('nan')):.4f} | C1 {m.get('c1', {}).get('mrr', float('nan')):.4f}", flush=True)
    base_tune = mrr_of(tune, "S_fixed"); print("fixed rule S(2,1,0.5) on tune:", base_tune); print("fixed rule S(2,1,0.15) on tune:", mrr_of(tune, "S_fixed15"))
    best = FIXED if FIXED else max(results, key=lambda r: (r["tune_c2_strict"] or 0) + 0.5 * (r["tune_c1"] or 0))
    print("selected:", best)
    bst = lgb.train(best["params"], ds_fit, num_boost_round=best["rounds"])
    ev = ev.copy(); ev["pred"] = bst.predict(ev[FE].values)
    out = dict(selected=best, tune_fixed=base_tune, eval_lambdarank=mrr_of(ev, "pred"), eval_fixed=mrr_of(ev, "S_fixed"), eval_fixed15=mrr_of(ev, "S_fixed15"),
               importance=dict(zip(FE, [int(x) for x in bst.feature_importance("gain").round().astype(int)])), n_fit_rows=len(fit_t), n_fit_groups=int(fit_t.groupby(["molecule", "view"]).ngroups),
               feats=a.feats, feature_names=list(FE), monotone=bool(a.monotone), drop=list(a.drop), c1_repeat=int(a.c1_repeat), c1_weight=float(a.c1_weight), prior_iw=a.prior_iw, restrict=a.restrict, pointwise=bool(a.pointwise), ekeys=(a.ekeys if a.restrict == "E" else ""), c1_only_runs=list(a.c1_only_runs), c2_drop_exposure=a.c2_drop_exposure, c1_seen_only=a.c1_seen_only, exposure_ledger=a.exposure_ledger)
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
