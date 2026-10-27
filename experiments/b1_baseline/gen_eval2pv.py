"""[gen_eval2pv = gen_eval2p with the v7f main (039/038: rank_v7a with the analog features on the GL path, blend21, NO outer analog term;
GL-fallback = insurance + 1 z(ap) + 1 z(MetFrag-lite)); the fixed variants (EA, P2, ...) are applied on top of that main.]
[gen_eval2p = gen_eval2 + fixed diagnostic variants of the registered main (074): P2 Pc-only demotion pcd<w> (score - w * 1[tier-only,
not COCONUT, not train-in-view]); explained-away demotion ea<theta>w<w> (score - w * 1[candidate has library references in the view and
lib_sim < theta]); P5 rank-2 hedges h2_<alt> (the alternative score's top-1 inserted at rank 2 unless already at rank 1-2, main rank 1 kept,
duplicates removed, top 25 rebuilt) with oracle o2_<alt> = max(main, h2); RRF(k=60) of main and an alternative rrf_<alt>.]
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
ap_.add_argument("--views", default="c1,c2,c3,c3m,c3n"); ap_.add_argument("--dump_choice", default="")
ap_.add_argument("--store", default="data/processed/spectra_store")
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
    bst = lgb.Booster(model_file=os.path.join(HERE, a.model)); FEATS = bst.feature_name()
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
    PVARS = ["pcd0.5", "pcd1", "pcd2", "ea0.3w1", "ea0.3w2", "ea0.5w1", "ea0.5w2"] + [f"{p_}_{n_}" for n_ in ("S", "prior", "fp", "lib", "ap") for p_ in ("h2", "o2")] + ["rrf_S", "rrf_prior"]
    # ---- union mask over every evaluated molecule (all sets of this run)
    allm = ev[ev.set.isin(a.sets)]
    UNION = set()
    for r in allm.itertuples(index=False):
        tk = str(r.scorer_key); raw = {key_of_row[x] for x in ik_rows.get(str(r.molecule), []) if key_of_row[x] is not None}
        UNION |= raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set()))
    log(f"union mask: {len(UNION):,} keys over {len(allm)} molecules")
    rows, parity, choice = [], [], []
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
                lst, der_keys = GEN.get(mid, {}).get(v, ([], set()))
                hit = [p_ for p_ in lst if p_[0] in mm["tokeys"]]
                base = dict(set=s, view=v, molecule=mid, n_prod=len(lst), n_novel=sum(p_[7] == "novel" for p_ in lst), n_window=sum(p_[7] == "window" for p_ in lst),
                            truth_generated=bool(hit), truth_loc=(hit[0][7] if hit else ""), truth_n_parents=(hit[0][4] if hit else 0), truth_combo=(hit[0][6] if hit else ""))
                if len(g) == 0:
                    rows.append(dict(base, n_cand=0, main=0.0, n_derivable=0, truth_derivable=False, gl_ok=False, pos=False, truth_coco=False, **{k: 0.0 for k in RULES + PVARS})); continue
                fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{vv}"].values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                zgl = term(glv, True)
                S = z(fp) + (2 * zgl if zgl is not None else 0) + 0.5 * pop
                top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
                fire = bool(lib.max() >= a.tau and lib.max() - second >= a.margin); ins = np.where(lib >= a.tau, 100.0 + lib, S) if fire else S
                gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
                afp = [(fp_of(KEY_SMI.get(k)), sv) for k, sv in mm["an"][vv]]; afp = [(f_, sv) for f_, sv in afp if f_ is not None]
                feats = BA.features([fp_of(str(sm)) for sm in g.smiles], [f_ for f_, _ in afp], [sv for _, sv in afp])
                if gl_ok:
                    X = feature_matrix(fp, glv, np.full(len(g), np.nan), pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                       g[f"lib_same_{vv}"].values, g[f"lib_nref_{vv}"].values, g.in_tier.values, g[f"in_train_{vv}"].values, g.in_coconut.values, g.ppm_err.values,
                                       g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=FEATS,
                                       analog=dict(ap=feats["ap"], mean_tan=feats["mean_tan"]))
                    score = 2 * z(np.asarray(bst.predict(X), float)) + z(np.asarray(S, float))
                else: score = np.asarray(ins, float)
                x_ = feats["ap"]
                if not gl_ok:   # v7f: fallback = insurance + 1 z(ap) + 1 z(MetFrag-lite); the GL path has no outer analog term
                    import b1_frag as BF
                    fr_ = np.array([BF.score(BF.fragments(str(sm_)), [dict(mz=q_["mz"], it=q_["it"], prec=q_["prec"], mode=q_["mode"]) for q_ in mm["qspec"]]) for sm_ in g.smiles], float)
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
                idx_main = [int(i) for i in order]
                def rr_idx(lst_idx):
                    for k_, i_ in enumerate(lst_idx[:25]):
                        if tr[i_]: return 1.0 / (k_ + 1)
                    return 0.0
                pc_only = (g.in_tier.values.astype(bool) & ~g.in_coconut.values.astype(bool) & ~g[f"in_train_{vv}"].values.astype(bool))
                for w_ in (0.5, 1.0, 2.0):
                    out[f"pcd{w_:g}"] = rr_idx(list(np.argsort(-(score - w_ * pc_only), kind="stable")))
                has_ref = g[f"lib_nref_{vv}"].values.astype(float) > 0
                for th_ in (0.3, 0.5):
                    for w_ in (1.0, 2.0):
                        out[f"ea{th_:g}w{w_:g}"] = rr_idx(list(np.argsort(-(score - w_ * (has_ref & (lib < th_))), kind="stable")))
                alts = dict(S=np.asarray(S if gl_ok else ins, float), prior=pop.astype(float), fp=fp.astype(float), lib=lib.astype(float), ap=np.asarray(feats["ap"], float))
                rank_main = np.empty(len(g)); rank_main[np.array(idx_main)] = np.arange(1, len(g) + 1)
                for nm, sc in alts.items():
                    sc = np.where(np.isfinite(sc), sc, -np.inf)
                    if nm == "lib" and not (lib > 0).any(): out[f"h2_{nm}"] = out["main"]; out[f"o2_{nm}"] = out["main"]
                    else:
                        j = int(np.argmax(sc))
                        lst2 = idx_main if j in idx_main[:2] else [idx_main[0], j] + [i for i in idx_main[1:] if i != j]
                        out[f"h2_{nm}"] = rr_idx(lst2); out[f"o2_{nm}"] = max(out["main"], out[f"h2_{nm}"])
                    if nm in ("S", "prior"):
                        ro = np.empty(len(g)); ro[np.argsort(-sc, kind="stable")] = np.arange(1, len(g) + 1)
                        out[f"rrf_{nm}"] = rr_idx(list(np.argsort(-(1.0 / (60 + rank_main) + 1.0 / (60 + ro)), kind="stable")))
                out["gl_ok"] = bool(gl_ok); out["pos"] = bool(tr.any()); out["truth_coco"] = bool((g.in_coconut.values.astype(bool) & tr).any())
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
                if a.dump_choice and v in ("c1", "c2"):
                    choice.append(dict(set=s, view=v, molecule=mid, gen_okey=(nov[0][0] if nov else None), gen_smiles=(nov[0][1] if nov else None), derivable=";".join(sorted(der_keys & set(okeys)))))
                rows.append(out)
        log(f"{s}: evaluated")
    if a.dump_choice: pd.DataFrame(choice).to_parquet(os.path.join(HERE, a.dump_choice), index=False)
    R = pd.DataFrame(rows)
    assert not R[PVARS + ['main']].isna().any().any(), 'variant columns missing for some rows'
    os.makedirs(os.path.dirname(os.path.join(HERE, a.out)), exist_ok=True); R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
    L = [f"# 042 v2 generation merge ({time.strftime('%Y-%m-%d %H:%M')}; f.z parity max {max(parity) if parity else float('nan'):.4f}; b1_gen v2)", "",
         "| set | view | n | main | truth generated | truth loc novel/window/short | median novel | truth derivable | " + " | ".join(RULES) + " |", "|---|---|---:|---:|---:|---|---:|---:|" + "---:|" * len(RULES)]
    for (s, v), g in R.groupby(["set", "view"], sort=False):
        lc = g.truth_loc.value_counts()
        L.append(f"| {s} | {v} | {len(g)} | {g.main.mean():.4f} | {g.truth_generated.mean():.3f} | {lc.get('novel', 0)}/{lc.get('window', 0)}/{lc.get('short', 0)} | {g.n_novel.median():.0f} | {g.truth_derivable.mean():.3f} | "
                 + " | ".join(f"{g[k].mean() - g.main.mean():+.4f}" for k in RULES) + " |")
    open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
