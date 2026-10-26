"""042: generated analog derivatives merged into the registered main output, evaluated in the C1 / C2 / C3 views (2026-10-26).

Views: c1 / c2 as the registered evaluator (b1_locked_eval.view_frame); c3 = the c2 view with every truth row removed (the truth is in no
structure database, class-3 proxy; the registered main scores 0 there by construction).
Main = the working baseline anaw0.5: blend21 (2 z(rank_v4b) + z(fixed rule)) on GL-covered molecules, the insurance list otherwise, + 0.5 z(ap).
Generated candidates: parents = the top-P analogs of the view (c1: truth references re-selected outside the query library; c2/c3: truth key,
raw keys and identity group removed), target = the molecule's neutral mass (median over its adducts, from the query precursors), products of
b1_gen.derive whose raw key is not in the molecule's window (c3: the truth keys removed from the window first) = novel structures.
Their FPNet score f.z uses the same logits and bits as the feature tables (b1_features --dump_gen; parity checked on shortlist candidates).
Merge variants (label-free): gk<k> = best novel structure (by f.z) inserted at rank k; gd<d>_k<k> = at rank 1 if its f.z exceeds the best
shortlist f.z by >= d, else at rank k (k=26: not inserted).
Usage: python -X utf8 gen_eval.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --out diag/geneval_panel
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

ap_ = argparse.ArgumentParser()
ap_.add_argument("--run", required=True); ap_.add_argument("--gen", required=True); ap_.add_argument("--sets", nargs="+", required=True)
ap_.add_argument("--eval_csv", required=True); ap_.add_argument("--out", required=True)
ap_.add_argument("--model", default="rank_v4b/lambdarank.txt"); ap_.add_argument("--analog_w", type=float, default=0.5)
ap_.add_argument("--dump_choice", default="", help="parity: write per (molecule, view) the chosen novel structure and the derivable official keys (parquet)")
ap_.add_argument("--parents", type=int, default=10); ap_.add_argument("--workers", type=int, default=16); ap_.add_argument("--limit", type=int, default=0)
ap_.add_argument("--store", default="data/processed/spectra_store")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap_.add_argument("--v3", default="data/external/v3_models/code"); ap_.add_argument("--fold_safe", default="data/external/fpnet_fulleval_as_fold0")
ap_.add_argument("--tau", type=float, default=0.9); ap_.add_argument("--margin", type=float, default=0.2); ap_.add_argument("--min_gl_cover", type=float, default=0.5)
a = ap_.parse_args()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
def log(*x): print(f"[geneval {time.time() - T0:6.0f}s]", *x, flush=True)

_W = {}


def _winit(v3, fs):
    sys.path.insert(0, v3)
    from casmi import chem
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*"); _W["chem"] = chem; _W["bits"] = np.load(f"{fs}/fp_bits.npy")


def gen_job(t):
    """(key, target_mass, parents [(smiles, sim)], zlog, window_keys) -> list of novel products (raw_key, smiles, fz, apsc, n_par, steps)."""
    import b1_gen as BG
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdFingerprintGenerator, Descriptors
    gen = _W.get("mg") or rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048); _W["mg"] = gen
    key, M, parents, zlog, wkeys = t
    prods, inwin = {}, {}
    for psmi, sim in parents:
        pm = Chem.MolFromSmiles(psmi)
        if pm is None: continue
        pfp = gen.GetFingerprint(pm)
        for smi, combo in BG.derive(psmi, M - Descriptors.ExactMolWt(pm)).items():
            m = Chem.MolFromSmiles(smi)
            if m is None: continue
            try: k = Chem.MolToInchiKey(m)[:14]
            except Exception: continue
            if not k: continue
            if k in wkeys:
                inwin[k] = max(inwin.get(k, 0.0), sim); continue
            sc = sim ** 3 * DataStructs.TanimotoSimilarity(gen.GetFingerprint(m), pfp)
            d = prods.get(k)
            if d is None:
                f = _W["chem"].raw_fingerprint(smi)
                if f is None: continue
                d = prods[k] = dict(smiles=smi, fz=float(f[_W["bits"]].astype(np.float32) @ zlog), apsc=0.0, n=0, steps=len(combo))
            d["n"] += 1; d["apsc"] = max(d["apsc"], sc); d["steps"] = min(d["steps"], len(combo))
    return key, ([(k, d["smiles"], d["fz"], d["apsc"], d["n"], d["steps"]) for k, d in prods.items()], inwin)


if __name__ == "__main__":
    import b1_locked_eval as E
    import b1_analog as BA
    from b1_evaluate import z, term
    from b1_rankfeats import feature_matrix
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
    from numba import set_num_threads
    import lightgbm as lgb
    from numba import config as _ncfg; set_num_threads(min(16, int(_ncfg.NUMBA_NUM_THREADS)))
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
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*"); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    _RK = {}
    def rawkey(smi):
        if smi not in _RK:
            m = Chem.MolFromSmiles(smi) if smi else None
            try: _RK[smi] = Chem.MolToInchiKey(m)[:14] if m is not None else None
            except Exception: _RK[smi] = None
        return _RK[smi]
    _FP = {}
    def fp_of(smi):
        if smi not in _FP:
            m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = MG.GetFingerprint(m) if m is not None else None
        return _FP[smi]
    _idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
    GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
    _winit(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))
    rows, parity, choice = [], [], []
    VARIANTS = [f"gk{k}" for k in (1, 2, 3, 6, 11)] + [f"gd{d:g}_k{k}" for d in (0, 2, 5, 10) for k in (6, 26)]
    DV = (0.5, 1.0, 2.0)
    VARIANTS += [f"dv{w:g}" for w in DV]
    HEDGE = [(k, x) for k in (2, 3) for x in ("fp", "ap", "gl", "pop", "lib")]   # exploratory: an independent signal's top-1 inserted at rank k
    VARIANTS += [f"h{k}_{x}" for k, x in HEDGE]
    for s in a.sets:
        F = pd.read_parquet(os.path.join(HERE, a.run, f"b1_features_{s}.parquet")); F["molecule"] = F["molecule"].astype(str)
        M = pd.read_csv(os.path.join(HERE, a.run, f"b1_molecules_{s}.csv")).set_index("molecule"); M.index = M.index.astype(str)
        gl, _, _ = E.runner(os.path.join(HERE, a.run), s, "gl"); gl = gl or {}
        G = np.load(os.path.join(HERE, a.gen, f"gen_{s}.npz")); ZL = dict(zip([str(x) for x in G["mol"]], G["zlog"])); MASS = dict(zip([str(x) for x in G["mol"]], [json.loads(x) for x in G["masses"]]))
        W = pd.read_parquet(os.path.join(HERE, a.gen, f"gen_{s}_window.parquet")); W["molecule"] = W["molecule"].astype(str); WK = W.groupby("molecule").key.apply(set).to_dict()
        mols = ev[ev.set == s]
        if a.limit: mols = mols.head(a.limit)
        # ---- parity of f.z on shortlist candidates (the dumped logits reproduce the table's fp)
        chk = F[F.molecule.isin(set(mols.molecule.iloc[:5]))].groupby("molecule").head(3)
        for r in chk.itertuples(index=False):
            f = _W["chem"].raw_fingerprint(str(r.smiles))
            if f is not None and np.isfinite(r.fp): parity.append(abs(float(f[_W["bits"]].astype(np.float32) @ ZL[str(r.molecule)]) - float(r.fp)))
        log(f"{s}: f.z parity max |diff| {max(parity) if parity else float('nan'):.4f} over {len(parity)} candidates")
        tasks, meta_m = [], {}
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
            an = {"c1": store.analogs(qspec, query_rows=q, relib=(tk, lib), key_rows=key_rows), "c2": store.analogs(qspec, query_rows=q, drop_keys=drop)}
            Mt = float(np.median(list(MASS[mid].values())))
            g2 = F[(F.molecule == mid)]; tkeys = set(g2[g2.is_truth].official_key.astype(str)) | {tk, mid} | raw | {rawkey(sm_) for sm_ in g2[g2.is_truth].smiles.astype(str)}
            wk = WK.get(mid, set())
            meta_m[mid] = dict(an=an, tkeys=tkeys, lib=lib)
            for v in ("c1", "c2", "c3"):
                par = [(KEY_SMI[k], float(sv)) for k, sv in an["c1" if v == "c1" else "c2"] if k in KEY_SMI][:a.parents]
                tasks.append(((s, mid, v), Mt, par, ZL[mid], (wk - tkeys) if v == "c3" else wk))
        log(f"{s}: analogs + generation tasks for {len(meta_m)} molecules")
        GEN = {}
        with Pool(a.workers, initializer=_winit, initargs=(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))) as p:
            for key, res in p.imap_unordered(gen_job, tasks, chunksize=1): GEN[key] = res
        log(f"{s}: generated")
        for mid, mm in meta_m.items():
            for v in ("c1", "c2", "c3"):
                vv = "c2" if v == "c3" else v
                if v == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
                g = E.view_frame(F, M, mid, vv)
                if v == "c3" and len(g): g = g[~g.is_truth.values.astype(bool)]
                base = dict(set=s, view=v, molecule=mid)
                prods, inwin = GEN.get((s, mid, v), ([], {}))
                hit = [p_ for p_ in prods if p_[0] in mm["tkeys"]]
                base.update(n_novel=len(prods), truth_generated=bool(hit))
                if len(g) == 0:
                    rows.append(dict(base, n_cand=0, main=0.0, n_derivable=0, truth_derivable=False, **{k: 0.0 for k in VARIANTS})); continue
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
                                       g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=FEATS)
                    score = 2 * z(np.asarray(bst.predict(X), float)) + z(np.asarray(S, float))
                else: score = np.asarray(ins, float)
                x_ = feats["ap"]; score = score + a.analog_w * (x_ - x_.mean()) / (x_.std() + 1e-9)
                order = list(np.argsort(-score, kind="stable"))
                tr = g.is_truth.values.astype(bool)
                lst = [("db", int(i)) for i in order]
                def rr_of(l):
                    for k_, (t_, i_) in enumerate(l[:25]):
                        if t_ == "db" and tr[i_]: return 1.0 / (k_ + 1)
                        if t_ == "gen" and i_ in mm["tkeys"]: return 1.0 / (k_ + 1)
                    return 0.0
                out = dict(base, n_cand=len(g), main=rr_of(lst), best_db_fz=float(np.nanmax(fp)) if np.isfinite(fp).any() else np.nan)
                pr = sorted(prods, key=lambda p_: (-p_[2], -p_[3], p_[0]))
                if pr:
                    out.update(best_gen_fz=pr[0][2], truth_gen_rank_fz=(1 + [p_[0] for p_ in pr].index(hit[0][0])) if hit else np.nan)
                der = np.array([rawkey(sm_) in inwin for sm_ in g.smiles.astype(str)], float)
                out.update(n_derivable=int(der.sum()), truth_derivable=bool((der * tr).sum() > 0))
                choice.append(dict(set=s, view=v, molecule=mid, gen_key=(pr[0][0] if pr else None), gen_smiles=(pr[0][1] if pr else None), gen_fz=(pr[0][2] if pr else None), derivable=";".join(sorted(set(g.official_key.astype(str)[der > 0])))))
                for w in DV:
                    o2 = list(np.argsort(-(score + w * der), kind="stable")); out[f"dv{w:g}"] = rr_of([("db", int(i)) for i in o2])
                alt = dict(fp=fp, ap=feats["ap"], gl=glv, pop=pop, lib=lib)
                for k, x in HEDGE:
                    xv = np.nan_to_num(np.asarray(alt[x], float), nan=-1e18)
                    if not np.isfinite(alt[x]).any(): out[f"h{k}_{x}"] = out["main"]; continue
                    b_ = int(np.argmax(xv))
                    o3 = [int(i) for i in order]
                    if b_ not in o3[:k]: o3 = [i for i in o3[:k - 1] if i != b_] + [b_] + [i for i in o3[k - 1:] if i != b_]
                    out[f"h{k}_{x}"] = rr_of([("db", i) for i in o3])
                for vn in VARIANTS:
                    if vn.startswith("dv") or vn.startswith("h"): continue
                    if not pr: out[vn] = out["main"]; continue
                    if vn.startswith("gk"): k = int(vn[2:])
                    else:
                        d_, k_s = vn[2:].split("_k"); d_ = float(d_); k = 1 if (np.isfinite(out["best_db_fz"]) and pr[0][2] - out["best_db_fz"] >= d_) else int(k_s)
                    out[vn] = rr_of(lst[:k - 1] + [("gen", pr[0][0])] + lst[k - 1:]) if k <= 25 else out["main"]
                rows.append(out)
        log(f"{s}: evaluated")
    if a.dump_choice: pd.DataFrame(choice).to_parquet(os.path.join(HERE, a.dump_choice), index=False)
    R = pd.DataFrame(rows); os.makedirs(os.path.dirname(os.path.join(HERE, a.out)), exist_ok=True); R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
    L = [f"# 042 generation merge ({time.strftime('%Y-%m-%d %H:%M')}; f.z parity max {max(parity) if parity else float('nan'):.4f})", "",
         "| set | view | n | main | truth generated | truth derivable | derivable cands (mean) | " + " | ".join(VARIANTS) + " |", "|---|---|---:|---:|---:|---:|---:|" + "---:|" * len(VARIANTS)]
    for (s, v), g in R.groupby(["set", "view"], sort=False):
        L.append(f"| {s} | {v} | {len(g)} | {g.main.mean():.4f} | {g.truth_generated.mean():.3f} | {g.truth_derivable.mean():.3f} | {g.n_derivable.mean():.1f} | " + " | ".join(f"{g[vn].mean() - g.main.mean():+.4f}" for vn in VARIANTS) + " |")
    open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
