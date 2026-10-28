"""[gen_eval2fd = gen_eval2m + --fp_override (091: per-spectrum FPNet logit mean on the fixed candidate rows) + --pop_ws (090: fixed-rule prior weight variants pw<w>, same blend / fallback rules) + --fpD (089 stage b): DreaMS-FP scores (dreams_fp_score.py parquet: set, molecule, smiles, fpD) as variants
fd_s<w> (w * term(fpD) added to the fixed rule S, i.e. inside z(S) on the GL path and inside the insurance S on the fallback path) and
fd_o<w> (w * term(fpD) added to the final score); main is unchanged (must equal gen_eval2m).]
[gen_eval2m = gen_eval2 scoring SEVERAL rankers in one pass: --model m1,m2,... --out o1,o2,... (analogs / generation shared;
per model the identical main / rule computation; one CSV + md per model)]
042 v2 (after Codex 042): generated analog derivatives merged into the registered main output, evaluated in C1 / C2 / C3 views.

Views (the shortlist frames come from b1_locked_eval.view_frame of the registered feature tables):
  c1, c2  : protection views; parents = the top-P analogs under the view's own mask (c1: truth references re-selected outside the query
            library; c2: truth key, raw keys and identity group removed) = what the pipeline does in evaluation mode.
  c3      : MAIN class-3 proxy = the c2 shortlist and window without the truth; parents under the UNION mask (every identity of the evaluated
            sets removed: other evaluation molecules are unknown structures too).
  c3m     : the same with the per-molecule mask (the other evaluation molecules stay known) - secondary.
  c3n     : c3 with near parents removed (Tanimoto to the truth >= 0.9, top-P re-selected after the removal) - sensitivity.
Generation: b1_gen v2 (product exact mass within max(2 mDa, 10 ppm) of the query-derived neutral mass = median over the molecule's adducts
of precursor - adduct shift; both orders of two-step edits; strict caps). Identity = official scorer key (b1_gen.official_key).
Product location per view: 'short' (official key in the view's shortlist; not added, but marks a derivable candidate), 'window' (raw key in
the molecule's window, not shortlisted = database reach rescue), 'novel' (in neither). The truth counts as generated only by its official key.
Scores: FPNet f.z with the dumped logits (same bits and function as the tables; parity printed).
Rules (fixed list, Codex 042): gk2 / gk3 = best novel structure (f.z, ties by parent score) at rank k; gt3 = at rank 3 only when its f.z >= the
f.z of the main list's rank-3 candidate; gk3all = best of novel + window-rescue structures at rank 3; dv1 = main score + 1 * 1[derivable].
Usage: python -X utf8 gen_eval2.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets C_np_crosslib ... --eval_csv eval_set2/v2/p2_molecules.csv --out diag/geneval2_p2dev
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

ap_ = argparse.ArgumentParser()
ap_.add_argument("--run", required=True); ap_.add_argument("--gen", required=True); ap_.add_argument("--sets", nargs="+", required=True)
ap_.add_argument("--eval_csv", required=True); ap_.add_argument("--out", required=True)
ap_.add_argument("--model", default="rank_v4b/lambdarank.txt"); ap_.add_argument("--analog_w", type=float, default=0.5)
ap_.add_argument("--parents", type=int, default=10); ap_.add_argument("--workers", type=int, default=16); ap_.add_argument("--limit", type=int, default=0)
ap_.add_argument("--views", default="c1,c2,c3,c3m,c3n"); ap_.add_argument("--dump_choice", default=""); ap_.add_argument("--refcmp", action="store_true"); ap_.add_argument("--v7f", action="store_true", help="087: the v7f main (analog features into rankers that use them, no outer analog term on the GL path; GL fallback = insurance + 1 z(ap) + 1 z(MetFrag-lite))")
ap_.add_argument("--store", default="data/processed/spectra_store"); ap_.add_argument("--fpD", default="", help="dreams_fp_score.py parquet"); ap_.add_argument("--tparents", default="", help="099: --dump_top parquet; the c2-view rank-1 structure of every OTHER molecule of the same set becomes a generation parent (label-free test-side parents)")
ap_.add_argument("--tparents_mode", default="only", choices=["only", "add"], help="only = test-side parents replace the train-analog parents; add = appended to them")
ap_.add_argument("--dump_top", default="", help="099: parquet of the first model's main order, top 25 per (set, view, molecule): smiles, official key, fp (f.z), score")
ap_.add_argument("--bmodel", default="", help="095: B-group specialist ranker (b1_rank_train --restrict B); variant bpp = the main order with the B candidates re-ordered by it inside the positions B already holds (GL path only; non-B positions unchanged)")
ap_.add_argument("--emodel", default="", help="102: comma-separated second-engine E-lite models (b1_rank_train --restrict E), scored on the E-window rows of each view (COCONUT | train in that view | PubChemLite / BIO keys of --ekeys), features recomputed within the window; variants <tag>_only (E list alone), p_e (main order restricted to the E window), rrf_<tag>_<a> / rrf_pe_<a> (identity RRF of the main order with E / with p_e, K = --rrf_k, weight a on the second list), orc_<tag> (max(main, E alone)); diagnostics e_reach, nE, rP, r_<tag>; tag = model directory name")
ap_.add_argument("--ekeys", default="diag/e_window_keys_v2.parquet"); ap_.add_argument("--rrf_k", type=float, default=10.0)
ap_.add_argument("--fp_col", default="fp_s", choices=["fp_s", "fp_m"], help="091: which fp_mean_score column overrides fp (fp_m = PC-recomputed merge input = platform control)")
ap_.add_argument("--fp_override", default="", help="091: fp_mean_score.py parquet; fp <- fp_s and fp_rank_window <- fprw_s for every candidate row (main and variants)")
ap_.add_argument("--pop_ws", default="", help="090: comma-separated fixed-rule prior weights -> variants pw<w>")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap_.add_argument("--v3", default="data/external/v3_models/code"); ap_.add_argument("--fold_safe", default="data/external/fpnet_fulleval_as_fold0")
ap_.add_argument("--tau", type=float, default=0.9); ap_.add_argument("--margin", type=float, default=0.2); ap_.add_argument("--min_gl_cover", type=float, default=0.5)
a = ap_.parse_args()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
VIEWS = a.views.split(",")
def log(*x): print(f"[geneval2 {time.time() - T0:6.0f}s]", *x, flush=True)

_W = {}


def _winit(v3, fs):
    sys.path.insert(0, v3)
    from casmi import chem
    from rdkit import RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*"); _W["chem"] = chem; _W["bits"] = np.load(f"{fs}/fp_bits.npy"); _W["mg"] = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def gen_job(t):
    """one molecule: (key, Mt, zlog, {view: parents}, {view: window raw keys}, {view: shortlist official keys}) ->
    (key, {view: (products [(okey, smiles, fz, apsc, n_parents, best_parent, best_combo, loc)], derivable official keys)})."""
    import b1_gen as BG
    from rdkit import Chem, DataStructs
    key, Mt, zlog, vpar, vwin, vshort = t
    cache, info = {}, {}
    def prod_of(psmi):
        if psmi not in cache:
            res = []
            for smi, combo in BG.derive(psmi, Mt).items():
                if smi not in info:
                    m = Chem.MolFromSmiles(smi)
                    if m is None: info[smi] = None; continue
                    try: rk = Chem.MolToInchiKey(m)[:14]
                    except Exception: info[smi] = None; continue
                    ok = BG.official_key(smi); f = _W["chem"].raw_fingerprint(smi)
                    info[smi] = None if (not rk or ok is None or f is None) else dict(rk=rk, ok=ok, fz=float(f[_W["bits"]].astype(np.float32) @ zlog), mfp=_W["mg"].GetFingerprint(m))
                if info[smi] is not None: res.append((smi, combo))
            cache[psmi] = res
        return cache[psmi]
    out = {}
    for v, parents in vpar.items():
        prods = {}
        for pi, (psmi, sim) in enumerate(parents):
            pm = Chem.MolFromSmiles(psmi)
            if pm is None: continue
            pfp = _W["mg"].GetFingerprint(pm)
            for smi, combo in prod_of(psmi):
                d0 = info[smi]; sc = sim ** 3 * DataStructs.TanimotoSimilarity(d0["mfp"], pfp)
                d = prods.get(d0["ok"])
                if d is None: d = prods[d0["ok"]] = dict(smiles=smi, rk=d0["rk"], fz=d0["fz"], apsc=-1.0, parents=set(), bp=None, bc=None)
                d["parents"].add(pi)
                if sc > d["apsc"]: d["apsc"] = sc; d["bp"] = pi; d["bc"] = "+".join(combo)
                if d0["fz"] > d["fz"]: d["fz"] = d0["fz"]; d["smiles"] = smi
        lst, der = [], set()
        for ok, d in prods.items():
            if ok in vshort[v]: loc = "short"; der.add(ok)
            elif d["rk"] in vwin[v]: loc = "window"
            else: loc = "novel"
            lst.append((ok, d["smiles"], d["fz"], d["apsc"], len(d["parents"]), d["bp"], d["bc"], loc))
        out[v] = (lst, der)
    return key, out


if __name__ == "__main__":
    import b1_locked_eval as E
    import b1_analog as BA
    from b1_evaluate import z, term
    from b1_rankfeats import feature_matrix
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
    from numba import set_num_threads, config as _ncfg
    import lightgbm as lgb
    set_num_threads(min(16, int(_ncfg.NUMBA_NUM_THREADS)))
    MODELS = a.model.split(","); OUTS = a.out.split(","); assert len(MODELS) == len(OUTS), (MODELS, OUTS)
    BSTS = [lgb.Booster(model_file=os.path.join(HERE, m_)) for m_ in MODELS]; FEATS = BSTS[0].feature_name()
    FEATS_M = [tuple(b_.feature_name()) for b_ in BSTS]
    EMODS = [(os.path.basename(os.path.dirname(m_)) or m_, lgb.Booster(model_file=os.path.join(HERE, m_))) for m_ in a.emodel.split(",") if m_]   # 102
    EKS = set(pd.read_parquet(os.path.join(HERE, a.ekeys)).key.astype(str)) if EMODS else set()   # set lookup (np.isin over 456k strings costs ~1.4 s per call)
    if EMODS: log(f"E-lite models {[t_ for t_, _ in EMODS]}, E-window extra keys {len(EKS):,}, RRF K {a.rrf_k}")
    BMOD = lgb.Booster(model_file=os.path.join(HERE, a.bmodel)) if a.bmodel else None   # 078: models may use different feature lists (one matrix per distinct list)
    TOPD = []   # 099 dump
    TPAR = {}
    if a.tparents:
        _tp = pd.read_parquet(os.path.join(HERE, a.tparents) if not os.path.isabs(a.tparents) else a.tparents)
        _tp = _tp[(_tp.view == 'c2') & (_tp['rank'] == 1)]
        for s_, m_, sm_ in zip(_tp['set'], _tp.molecule.astype(str), _tp.smiles.astype(str)): TPAR.setdefault(str(s_), {})[m_] = sm_
        log(f'test-side parents: {sum(len(v) for v in TPAR.values())} molecules from {a.tparents} (mode {a.tparents_mode})')
    FPO = {}
    if a.fp_override:
        _fo = pd.read_parquet(os.path.join(HERE, a.fp_override) if not os.path.isabs(a.fp_override) else a.fp_override)
        _rc = 'fprw_s' if a.fp_col == 'fp_s' else 'fprw_m'
        FPO = {(str(s_), str(m_), str(sm_)): (float(v_), float(r_)) for s_, m_, sm_, v_, r_ in zip(_fo['set'], _fo['molecule'], _fo['smiles'], _fo[a.fp_col], _fo[_rc])}
        log(f'fp override: {len(FPO):,} candidate rows from {a.fp_override}')
    FPD = {}
    if a.fpD:
        _fd = pd.read_parquet(os.path.join(HERE, a.fpD) if not os.path.isabs(a.fpD) else a.fpD)
        FPD = {(str(s_), str(m_), str(sm_)): float(v_) for s_, m_, sm_, v_ in zip(_fd['set'], _fd['molecule'], _fd['smiles'], _fd['fpD'])}
        log(f'fpD: {len(FPD):,} candidate rows from {a.fpD}')
    CMPX = {}
    if a.refcmp:
        _p = os.path.join(HERE, "diag", f"refcmpx_{os.path.basename(a.run)}.parquet"); _d = pd.read_parquet(_p)
        for r_ in _d.itertuples(index=False): CMPX[(str(r_.set), str(r_.molecule), str(r_.official_key))] = (int(r_.n_cmp_pol_c1), int(r_.n_cmp_add_c1), int(r_.n_cmp_pol_c2), int(r_.n_cmp_add_c2))
        log(f"refcmp entries {len(CMPX)} from {_p}")
    ev = pd.read_csv(os.path.join(HERE, a.eval_csv)); ev["molecule"] = ev["molecule"].astype(str)
    S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
    store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=log)
    from rdkit import Chem, RDLogger, DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*"); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    _FP, _RK = {}, {}
    def fp_of(smi):
        if smi not in _FP:
            m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = MG.GetFingerprint(m) if m is not None else None
        return _FP[smi]
    def rawkey(smi):
        if smi not in _RK:
            m = Chem.MolFromSmiles(smi) if smi else None
            try: _RK[smi] = Chem.MolToInchiKey(m)[:14] if m is not None else None
            except Exception: _RK[smi] = None
        return _RK[smi]
    _idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
    GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
    _winit(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))
    RULES = ["gk2", "gk3", "gt3", "gk3all", "dv1"]
    PWS = [float(x) for x in a.pop_ws.split(",") if x]
    FDV = ([f"fd_{k}{w}" for k in ("s", "o") for w in (0.5, 1.0)] if a.fpD else []) + [f"pw{w}" for w in PWS] + (["bpp", "rB_main", "rB_spec", "truth_B", "nB"] if a.bmodel else [])
    FDV += (["p_e"] + [f"rrf_pe_{al_}" for al_ in (0.5, 1.0)] + [v_ for t_, _ in EMODS for v_ in [f"{t_}_only", f"orc_{t_}"] + [f"rrf_{t_}_{al_}" for al_ in (0.5, 1.0)]]) if a.emodel else []
    # ---- union mask over every evaluated molecule (all sets of this run)
    allm = ev[ev.set.isin(a.sets)]
    UNION = set()
    for r in allm.itertuples(index=False):
        tk = str(r.scorer_key); raw = {key_of_row[x] for x in ik_rows.get(str(r.molecule), []) if key_of_row[x] is not None}
        UNION |= raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set()))
    log(f"union mask: {len(UNION):,} keys over {len(allm)} molecules")
    ROWS, parity, choice = [[] for _ in MODELS], [], []
    for s in a.sets:
        F = pd.read_parquet(os.path.join(HERE, a.run, f"b1_features_{s}.parquet")); F["molecule"] = F["molecule"].astype(str)
        M = pd.read_csv(os.path.join(HERE, a.run, f"b1_molecules_{s}.csv")).set_index("molecule"); M.index = M.index.astype(str)
        gl, _, _ = E.runner(os.path.join(HERE, a.run), s, "gl"); gl = gl or {}
        G = np.load(os.path.join(HERE, a.gen, f"gen_{s}.npz")); ZL = dict(zip([str(x) for x in G["mol"]], G["zlog"])); MASS = dict(zip([str(x) for x in G["mol"]], [json.loads(x) for x in G["masses"]]))
        W = pd.read_parquet(os.path.join(HERE, a.gen, f"gen_{s}_window.parquet")); W["molecule"] = W["molecule"].astype(str); WK = W.groupby("molecule").key.apply(set).to_dict()
        mols = ev[ev.set == s]
        if a.limit: mols = mols.head(a.limit)
        chk = F[F.molecule.isin(set(mols.molecule.iloc[:5]))].groupby("molecule").head(3)
        for r in chk.itertuples(index=False):
            f = _W["chem"].raw_fingerprint(str(r.smiles))
            if f is not None and np.isfinite(r.fp): parity.append(abs(float(f[_W["bits"]].astype(np.float32) @ ZL[str(r.molecule)]) - float(r.fp)))
        log(f"{s}: f.z parity max |diff| {max(parity) if parity else float('nan'):.4f}")
        tasks, MM = [], {}
        for r in mols.itertuples(index=False):
            mid, lib, tk = str(r.molecule), r.lib, str(r.scorer_key)
            if mid not in M.index or mid not in ZL: continue
            qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
            q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
            qspec = []
            for x in q:
                sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
            raw = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
            drop = raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set()))
            an = {}
            if "c1" in VIEWS: an["c1"] = store.analogs(qspec, query_rows=q, relib=(tk, lib), key_rows=key_rows)
            an["c2"] = store.analogs(qspec, query_rows=q, drop_keys=drop)
            an["u"] = store.analogs(qspec, query_rows=q, drop_keys=UNION, n_analog=max(80, 4 * a.parents))
            g2 = F[F.molecule == mid]; tr_rows = g2[g2.is_truth]
            tokeys = {tk} | set(tr_rows.official_key.astype(str))
            trraw = {rawkey(sm_) for sm_ in tr_rows.smiles.astype(str)} | {mid}
            tfp = fp_of(KEY_SMI.get(tk) or (str(tr_rows.smiles.iloc[0]) if len(tr_rows) else ""))
            def par(lst, near=False):
                out_ = []
                for k_, sv in lst:
                    smi_ = KEY_SMI.get(k_)
                    if smi_ is None: continue
                    if near and tfp is not None and fp_of(smi_) is not None and DataStructs.TanimotoSimilarity(tfp, fp_of(smi_)) >= 0.9: continue
                    out_.append((smi_, float(sv)))
                    if len(out_) >= a.parents: break
                return out_
            vpar = {}
            if "c1" in VIEWS: vpar["c1"] = par(an["c1"])
            if "c2" in VIEWS: vpar["c2"] = par(an["c2"])
            if "c3" in VIEWS: vpar["c3"] = par(an["u"])
            if "c3m" in VIEWS: vpar["c3m"] = par(an["c2"])
            if "c3n" in VIEWS: vpar["c3n"] = par(an["u"], near=True)
            if TPAR:
                tps = [(sm_, 1.0) for m_, sm_ in sorted(TPAR.get(s, {}).items()) if m_ != str(mid)]
                for v in list(vpar): vpar[v] = tps if a.tparents_mode == 'only' else vpar[v] + tps
            wk = WK.get(mid, set()); vwin, vshort = {}, {}
            for v in vpar:
                vv = "c1" if v == "c1" else "c2"
                gv = E.view_frame(F, M, mid, vv) if (vv != "c1" or bool(M.loc[mid, "c1_usable"])) else pd.DataFrame()
                ks = set(gv.official_key.astype(str)) if len(gv) else set()
                if v.startswith("c3"): ks -= tokeys; vwin[v] = wk - trraw
                else: vwin[v] = wk
                vshort[v] = ks
            Mt = float(np.median(list(MASS[mid].values())))
            MM[mid] = dict(an=an, tokeys=tokeys, qspec=qspec)
            tasks.append(((s, mid), Mt, ZL[mid], vpar, vwin, vshort))
        log(f"{s}: analogs for {len(MM)} molecules")
        GEN = {}
        with Pool(a.workers, initializer=_winit, initargs=(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))) as p:
            for key, res in p.imap_unordered(gen_job, tasks, chunksize=1): GEN[key[1]] = res
        log(f"{s}: generated")
        for mid, mm in MM.items():
            for v in VIEWS:
                vv = "c1" if v == "c1" else "c2"
                if vv == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
                g = E.view_frame(F, M, mid, vv)
                if v.startswith("c3") and len(g): g = g[~g.is_truth.values.astype(bool)]
                if FPO and len(g):
                    _ov = [FPO.get((s, mid, str(sm_)), (np.nan, np.nan)) for sm_ in g.smiles]
                    g = g.assign(fp=[o_[0] for o_ in _ov], fp_rank_window=[o_[1] for o_ in _ov])
                lst, der_keys = GEN.get(mid, {}).get(v, ([], set()))
                hit = [p_ for p_ in lst if p_[0] in mm["tokeys"]]
                base = dict(set=s, view=v, molecule=mid, n_prod=len(lst), n_novel=sum(p_[7] == "novel" for p_ in lst), n_window=sum(p_[7] == "window" for p_ in lst),
                            truth_generated=bool(hit), truth_loc=(hit[0][7] if hit else ""), truth_n_parents=(hit[0][4] if hit else 0), truth_combo=(hit[0][6] if hit else ""))
                if len(g) == 0:
                    for R_ in ROWS: R_.append(dict(base, n_cand=0, main=0.0, n_derivable=0, truth_derivable=False, **{k: 0.0 for k in RULES + FDV}))
                    continue
                fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{vv}"].values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                zgl = term(glv, True)
                S = z(fp) + (2 * zgl if zgl is not None else 0) + 0.5 * pop
                fdv = term(np.array([FPD.get((s, mid, str(sm_)), np.nan) for sm_ in g.smiles], float)) if FPD else None
                top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
                fire = bool(lib.max() >= a.tau and lib.max() - second >= a.margin); ins = np.where(lib >= a.tau, 100.0 + lib, S) if fire else S
                gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
                afp = [(fp_of(KEY_SMI.get(k)), sv) for k, sv in mm["an"][vv]]; afp = [(f_, sv) for f_, sv in afp if f_ is not None]
                feats = BA.features([fp_of(str(sm)) for sm in g.smiles], [f_ for f_, _ in afp], [sv for _, sv in afp])
                XS = {}
                if gl_ok:
                  cmp_ = None
                  if CMPX:
                    _t = [CMPX.get((s, mid, str(k_)), (0, 0, 0, 0)) for k_ in g.official_key]
                    cmp_ = dict(n_cmp_pol=[t_[0 if vv == 'c1' else 2] for t_ in _t], n_cmp_add=[t_[1 if vv == 'c1' else 3] for t_ in _t])
                  for fl_ in set(FEATS_M):
                    XS[fl_] = feature_matrix(fp, glv, np.full(len(g), np.nan), pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                       g[f"lib_same_{vv}"].values, g[f"lib_nref_{vv}"].values, g.in_tier.values, g[f"in_train_{vv}"].values, g.in_coconut.values, g.ppm_err.values,
                                       g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=list(fl_), cmp=cmp_, analog=(dict(ap=feats['ap'], mean_tan=feats['mean_tan']) if any(f_.startswith('ana_') or f_ == 'z_ana_ap' for f_ in fl_) else None))
                for mi_, bst in enumerate(BSTS):
                    pred_ = np.asarray(bst.predict(XS[FEATS_M[mi_]]), float) if gl_ok else None
                    def _final(S_, ins_):
                        sc_ = 2 * z(pred_) + z(np.asarray(S_, float)) if gl_ok else np.asarray(ins_, float)
                        x2_ = feats['ap']
                        if not a.v7f: sc_ = sc_ + a.analog_w * (x2_ - x2_.mean()) / (x2_.std() + 1e-9)
                        elif not gl_ok: sc_ = sc_ + 1.0 * (x2_ - x2_.mean()) / (x2_.std() + 1e-9) + 1.0 * (FR_ - FR_.mean()) / (FR_.std() + 1e-9)
                        return sc_
                    if gl_ok: score = 2 * z(pred_) + z(np.asarray(S, float))
                    else: score = np.asarray(ins, float)
                    x_ = feats["ap"]
                    if not a.v7f: score = score + a.analog_w * (x_ - x_.mean()) / (x_.std() + 1e-9)
                    elif not gl_ok:   # v7f fallback: insurance + 1 z(ap) + 1 z(MetFrag-lite); learned path: no outer analog term
                        if "frag" not in mm:
                            import b1_frag as BF
                            mm["frag"] = {str(sm_): BF.score(BF.fragments(str(sm_)), [dict(mz=q_["mz"], it=q_["it"], prec=q_["prec"], mode=q_["mode"]) for q_ in mm["qspec"]]) for sm_ in set(F[F.molecule == mid].smiles.astype(str))}
                        fr_ = np.array([mm["frag"][str(sm_)] for sm_ in g.smiles], float)
                        FR_ = fr_
                        score = score + 1.0 * (x_ - x_.mean()) / (x_.std() + 1e-9) + 1.0 * (fr_ - fr_.mean()) / (fr_.std() + 1e-9)
                    order = list(np.argsort(-score, kind="stable"))
                    tr = g.is_truth.values.astype(bool); okeys = g.official_key.astype(str).values
                    lst_db = [("db", int(i)) for i in order]
                    def rr_of(l):
                        for k_, (t_, i_) in enumerate(l[:25]):
                            if t_ == "db" and tr[i_]: return 1.0 / (k_ + 1)
                            if t_ == "gen" and i_ in mm["tokeys"]: return 1.0 / (k_ + 1)
                        return 0.0
                    out = dict(base, n_cand=len(g), main=rr_of(lst_db))
                    if EMODS and mi_ == 0:   # 102: second engine E-lite on the E window + identity RRF with the main order (rows = unique official keys)
                        em_ = g.in_coconut.values.astype(bool) | g[f"in_train_{vv}"].values.astype(bool) | np.fromiter((k_ in EKS for k_ in okeys), bool, len(okeys)); ei_ = np.flatnonzero(em_)
                        pos_m = np.empty(len(g), int); pos_m[np.asarray(order, int)] = np.arange(len(g))   # 0-based main position
                        out.update(nE=int(len(ei_)), e_reach=bool(tr[ei_].any()) if len(ei_) else False, rP=int(pos_m[tr].min() + 1) if tr.any() else 0)
                        def _rrf(second_, al_):
                            r2_ = np.full(len(g), np.inf)
                            if len(second_): r2_[np.asarray(second_, int)] = np.arange(1, len(second_) + 1)
                            sc_ = 1.0 / (a.rrf_k + pos_m + 1) + al_ * np.where(np.isfinite(r2_), 1.0 / (a.rrf_k + r2_), 0.0)
                            return [("db", int(i)) for i in np.lexsort((pos_m, -sc_))]   # ties -> main order
                        pe_ = [int(i) for i in order if em_[i]]; out["p_e"] = rr_of([("db", i) for i in pe_])
                        for al_ in (0.5, 1.0): out[f"rrf_pe_{al_}"] = rr_of(_rrf(pe_, al_))
                        for t_, emod_ in EMODS:
                            es_ = []
                            if len(ei_):
                                sub = lambda arr: np.asarray(arr)[ei_]; fe_ = list(emod_.feature_name())
                                XE = feature_matrix(sub(fp), sub(glv), np.full(len(ei_), np.nan), sub(pop), sub(g.lsid.values), sub(g.lpmid.values), sub(g.lsynonyms.values), sub(g["np"].values),
                                                    sub(g.src_mask.values), sub(g.lotus_refs.values), sub(lib), sub(g[f"lib_same_{vv}"].values), sub(g[f"lib_nref_{vv}"].values), sub(g.in_tier.values),
                                                    sub(g[f"in_train_{vv}"].values), sub(g.in_coconut.values), sub(g.ppm_err.values), sub(g.fp_rank_window.values), float(M.loc[mid, "n_query"]),
                                                    float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=fe_,
                                                    analog=(dict(ap=sub(feats["ap"]), mean_tan=sub(feats["mean_tan"])) if any(f_.startswith("ana_") or f_ == "z_ana_ap" for f_ in fe_) else None))
                                se_ = np.asarray(emod_.predict(XE), float)
                                if not np.isfinite(se_).all(): raise RuntimeError(f"102: non-finite E prediction ({t_}, {s}, {v}, {mid}) - stop (registered: an E failure must not turn into the p_e vote)")
                                es_ = [int(ei_[j]) for j in np.lexsort((pos_m[ei_], -se_))]   # ties -> main order
                            out[f"r_{t_}"] = next((k + 1 for k, i in enumerate(es_) if tr[i]), 0)
                            out[f"{t_}_only"] = rr_of([("db", i) for i in es_]); out[f"orc_{t_}"] = max(out["main"], out[f"{t_}_only"])
                            for al_ in (0.5, 1.0): out[f"rrf_{t_}_{al_}"] = rr_of(_rrf(es_, al_))
                    if a.dump_top and mi_ == 0:
                        for k_, i_ in enumerate(order[:25]):
                            TOPD.append(dict(set=s, view=v, molecule=mid, rank=k_ + 1, smiles=str(g.smiles.values[i_]), okey=str(g.official_key.values[i_]), fp=float(fp[i_]) if np.isfinite(fp[i_]) else np.nan,
                                             score=float(score[i_]), is_truth=bool(tr[i_]), gl_ok=bool(gl_ok)))
                    for w_ in PWS:
                        S3_ = z(fp) + (2 * zgl if zgl is not None else 0) + w_ * pop; ins3_ = np.where(lib >= a.tau, 100.0 + lib, S3_) if fire else S3_
                        out[f'pw{w_}'] = rr_of([('db', int(i)) for i in np.argsort(-_final(S3_, ins3_), kind='stable')])
                    if BMOD is not None:
                        isB = (g.in_coconut.values.astype(bool) & ~g[f'in_train_{vv}'].values.astype(bool))
                        bi = np.flatnonzero(isB); out['nB'] = int(len(bi)); out['truth_B'] = bool(tr[bi].any()) if len(bi) else False
                        ord_main = np.argsort(-score, kind='stable'); pos_ = {int(i): k for k, i in enumerate(ord_main)}
                        rb_m = [i for i in ord_main if isB[i]]
                        out['rB_main'] = next((k + 1 for k, i in enumerate(rb_m) if tr[i]), 0)
                        new_order = ord_main
                        if gl_ok and len(bi) >= 2:
                            sub = lambda arr: np.asarray(arr)[bi]
                            cmp_b = None if not CMPX else dict(n_cmp_pol=list(np.asarray(cmp_['n_cmp_pol'])[bi]), n_cmp_add=list(np.asarray(cmp_['n_cmp_add'])[bi]))
                            fb_ = list(BMOD.feature_name())
                            XB = feature_matrix(sub(fp), sub(glv), np.full(len(bi), np.nan), sub(pop), sub(g.lsid.values), sub(g.lpmid.values), sub(g.lsynonyms.values), sub(g['np'].values),
                                                sub(g.src_mask.values), sub(g.lotus_refs.values), sub(lib), sub(g[f'lib_same_{vv}'].values), sub(g[f'lib_nref_{vv}'].values), sub(g.in_tier.values),
                                                sub(g[f'in_train_{vv}'].values), sub(g.in_coconut.values), sub(g.ppm_err.values), sub(g.fp_rank_window.values), float(M.loc[mid, 'n_query']),
                                                float(M.loc[mid, 'ce_known']), n_window=float(M.loc[mid, 'n_unique']) if 'n_unique' in M.columns else np.nan, feats=fb_, cmp=cmp_b,
                                                analog=(dict(ap=sub(feats['ap']), mean_tan=sub(feats['mean_tan'])) if any(f_.startswith('ana_') or f_ == 'z_ana_ap' for f_ in fb_) else None))
                            sb = np.asarray(BMOD.predict(XB), float)
                            mp_ = np.array([pos_[int(i)] for i in bi])
                            if not np.isfinite(sb).all() or np.ptp(sb) == 0: b_sorted = [int(bi[j]) for j in np.argsort(mp_, kind='stable')]   # degenerate -> keep the main order
                            else: b_sorted = [int(bi[j]) for j in np.lexsort((mp_, -sb))]   # ties broken by the main order
                            slots = sorted(pos_[int(i)] for i in bi); new_order = ord_main.copy()
                            for k_, i_ in zip(slots, b_sorted): new_order[k_] = i_
                            out['rB_spec'] = next((k + 1 for k, i in enumerate(b_sorted) if tr[i]), 0)
                        else: out['rB_spec'] = out['rB_main']
                        out['bpp'] = rr_of([('db', int(i)) for i in new_order])
                    if fdv is not None:
                        for w_ in (0.5, 1.0):
                            S2_ = S + w_ * fdv; ins2_ = np.where(lib >= a.tau, 100.0 + lib, S2_) if fire else S2_
                            out[f'fd_s{w_}'] = rr_of([('db', int(i)) for i in np.argsort(-_final(S2_, ins2_), kind='stable')])
                            out[f'fd_o{w_}'] = rr_of([('db', int(i)) for i in np.argsort(-(score + w_ * fdv), kind='stable')])
                    nov = sorted([p_ for p_ in lst if p_[7] == "novel"], key=lambda p_: (-p_[2], -p_[3], p_[0]))
                    alln = sorted([p_ for p_ in lst if p_[7] in ("novel", "window")], key=lambda p_: (-p_[2], -p_[3], p_[0]))
                    if hit and hit[0][7] == "novel": out["truth_rank_novel_fz"] = 1 + [p_[0] for p_ in nov].index(hit[0][0])
                    ins_at = lambda k, pk: rr_of(lst_db[:k - 1] + [("gen", pk)] + lst_db[k - 1:])
                    out["gk2"] = ins_at(2, nov[0][0]) if nov else out["main"]
                    out["gk3"] = ins_at(3, nov[0][0]) if nov else out["main"]
                    fz3 = float(fp[order[2]]) if len(order) >= 3 and np.isfinite(fp[order[2]]) else -np.inf
                    out["gt3"] = ins_at(3, nov[0][0]) if (nov and nov[0][2] >= fz3) else out["main"]
                    out["gk3all"] = ins_at(3, alln[0][0]) if alln else out["main"]
                    der = np.array([k_ in der_keys for k_ in okeys], float)
                    out.update(n_derivable=int(der.sum()), truth_derivable=bool((der * tr).sum() > 0))
                    out["dv1"] = rr_of([("db", int(i)) for i in np.argsort(-(score + 1.0 * der), kind="stable")])
                    if a.dump_choice and mi_ == 0 and v in ("c1", "c2"):
                        choice.append(dict(set=s, view=v, molecule=mid, gen_okey=(nov[0][0] if nov else None), gen_smiles=(nov[0][1] if nov else None), derivable=";".join(sorted(der_keys & set(okeys)))))
                    ROWS[mi_].append(out)
        log(f"{s}: evaluated")
    if a.dump_choice: pd.DataFrame(choice).to_parquet(os.path.join(HERE, a.dump_choice), index=False)
    if a.dump_top: pd.DataFrame(TOPD).to_parquet(os.path.join(HERE, a.dump_top), index=False); log(f'top-25 dump: {len(TOPD):,} rows -> {a.dump_top}')
    for rows, OUT_ in zip(ROWS, OUTS):
        R = pd.DataFrame(rows); os.makedirs(os.path.dirname(os.path.join(HERE, OUT_)), exist_ok=True); R.to_csv(os.path.join(HERE, OUT_ + ".csv"), index=False)
        L = [f"# 042 v2 generation merge ({time.strftime('%Y-%m-%d %H:%M')}; f.z parity max {max(parity) if parity else float('nan'):.4f}; b1_gen v2)", "",
             "| set | view | n | main | truth generated | truth loc novel/window/short | median novel | truth derivable | " + " | ".join(RULES + FDV) + " |", "|---|---|---:|---:|---:|---|---:|---:|" + "---:|" * len(RULES + FDV)]
        for (s, v), g in R.groupby(["set", "view"], sort=False):
            lc = g.truth_loc.value_counts()
            L.append(f"| {s} | {v} | {len(g)} | {g.main.mean():.4f} | {g.truth_generated.mean():.3f} | {lc.get('novel', 0)}/{lc.get('window', 0)}/{lc.get('short', 0)} | {g.n_novel.median():.0f} | {g.truth_derivable.mean():.3f} | "
                     + " | ".join(f"{g[k].mean() - g.main.mean():+.4f}" for k in RULES + FDV) + " |")
        open(os.path.join(HERE, OUT_ + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
