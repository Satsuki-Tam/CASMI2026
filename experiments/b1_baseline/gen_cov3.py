"""Stage-2 exploration (2026-10-26, development only): class-3 coverage of analog-derivative generation by parent source.

C3 proxy as gen_eval2's c3 view (the truth is in no database; the union of every evaluated identity is removed from the parents).
Parent sources (label-free):
  ana  : the top-P train analogs by spectral similarity (b1_analog; = gen_eval2 c3)
  db   : database relatives = pool structures (train + COCONUT, v2 pool) whose mass equals the target neutral mass minus the formula change of
         one edit of b1_gen (within the b1_gen tolerance), ranked by FPNet f.z with the query logits (a one-edit relative shares most bits)
  both : ana + db (P each)
Measures per molecule: the truth (official key) among the novel products, the number of novel products, the truth's rank among them by f.z.
Usage: python -X utf8 gen_cov3.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets C_np_crosslib ... --eval_csv eval_set2/v2/p2_molecules.csv --out diag/gencov3_p2dev
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

ap_ = argparse.ArgumentParser()
ap_.add_argument("--run", required=True); ap_.add_argument("--gen", required=True); ap_.add_argument("--sets", nargs="+", required=True)
ap_.add_argument("--eval_csv", required=True); ap_.add_argument("--out", required=True); ap_.add_argument("--parents", type=int, default=10)
ap_.add_argument("--workers", type=int, default=16); ap_.add_argument("--limit", type=int, default=0)
ap_.add_argument("--store", default="data/processed/spectra_store"); ap_.add_argument("--pool", default="data/external/v2_pool/pool_meta.parquet")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap_.add_argument("--v3", default="data/external/v3_models/code"); ap_.add_argument("--fold_safe", default="data/external/fpnet_fulleval_as_fold0")
a = ap_.parse_args()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
def log(*x): print(f"[gencov3 {time.time() - T0:6.0f}s]", *x, flush=True)
_W = {}


def _winit(v3, fs):
    sys.path.insert(0, v3)
    from casmi import chem
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*"); _W["chem"] = chem; _W["bits"] = np.load(f"{fs}/fp_bits.npy")


def load_pool(pool_path):   # in the PARENT before the fork (polars must not be used again in forked workers: deadlock)
    P = pl.read_parquet(pool_path, columns=["key", "smiles", "mass"]).sort("mass")
    _W["pm"] = P["mass"].to_numpy(); _W["psmi"] = P["smiles"].to_numpy(); _W["pkey"] = P["key"].to_numpy()


def fz_of(smi, zlog):
    f = _W["chem"].raw_fingerprint(smi)
    return None if f is None else float(f[_W["bits"]].astype(np.float32) @ zlog)


def job(t):
    import b1_gen as BG
    from rdkit import Chem
    key, Mt, zlog, ana_par, wkeys, tokeys, mask = t
    tol = BG.tol_for(Mt)
    # database relatives: pool structures at Mt - (one-edit formula change)
    deltas = sorted({round(BG._mass(v[1]), 6) for v in BG.EDITS.values()})
    cand = {}
    for d in deltas:
        lo = np.searchsorted(_W["pm"], Mt - d - tol, "left"); hi = np.searchsorted(_W["pm"], Mt - d + tol, "right")
        for i in range(lo, hi):
            k = str(_W["pkey"][i])
            if k in mask or k in cand: continue
            cand[k] = str(_W["psmi"][i])
    scored = []
    for k, smi in cand.items():
        fz = fz_of(smi, zlog)
        if fz is not None: scored.append((fz, k, smi))
    scored.sort(key=lambda x: (-x[0], x[1]))
    db_par = [(smi, 1.0) for fz, k, smi in scored[:a.parents]]
    out = {}
    for src, par in (("ana", ana_par), ("db", db_par), ("both", ana_par + db_par)):
        prods = {}
        for psmi, sim in par:
            for smi in BG.derive(psmi, Mt):
                m = Chem.MolFromSmiles(smi)
                if m is None: continue
                try: rk = Chem.MolToInchiKey(m)[:14]
                except Exception: continue
                if not rk or rk in wkeys: continue
                ok = BG.official_key(smi)
                if ok is None: continue
                fz = fz_of(smi, zlog)
                if fz is None: continue
                if ok not in prods or fz > prods[ok]: prods[ok] = fz
        order = sorted(prods, key=lambda k: (-prods[k], k))
        hit = [i for i, k in enumerate(order) if k in tokeys]
        out[src] = dict(n_novel=len(order), gen=bool(hit), rank=(hit[0] + 1) if hit else np.nan, n_par=len(par), n_dbcand=len(cand))
    return key, out


if __name__ == "__main__":
    import b1_analog as BA
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
    from numba import set_num_threads, config as _ncfg
    set_num_threads(min(16, int(_ncfg.NUMBA_NUM_THREADS)))
    ev = pd.read_csv(os.path.join(HERE, a.eval_csv)); ev["molecule"] = ev["molecule"].astype(str)
    S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
    store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=log)
    ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    _idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
    GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
    allm = ev[ev.set.isin(a.sets)]; UNION = set()
    for r in allm.itertuples(index=False):
        tk = str(r.scorer_key); raw = {key_of_row[x] for x in ik_rows.get(str(r.molecule), []) if key_of_row[x] is not None}
        UNION |= raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set()))
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    load_pool(os.path.join(ROOT, a.pool)); log(f"pool: {len(_W['pm']):,} structures")
    rows = []
    for s in a.sets:
        F = pd.read_parquet(os.path.join(HERE, a.run, f"b1_features_{s}.parquet")); F["molecule"] = F["molecule"].astype(str)
        G = np.load(os.path.join(HERE, a.gen, f"gen_{s}.npz")); ZL = dict(zip([str(x) for x in G["mol"]], G["zlog"])); MASS = dict(zip([str(x) for x in G["mol"]], [json.loads(x) for x in G["masses"]]))
        W = pd.read_parquet(os.path.join(HERE, a.gen, f"gen_{s}_window.parquet")); W["molecule"] = W["molecule"].astype(str); WK = W.groupby("molecule").key.apply(set).to_dict()
        mols = ev[ev.set == s]
        if a.limit: mols = mols.head(a.limit)
        tasks = []
        for r in mols.itertuples(index=False):
            mid, lib, tk = str(r.molecule), r.lib, str(r.scorer_key)
            if mid not in ZL: continue
            qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
            q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
            qspec = []
            for x in q:
                sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
            an = store.analogs(qspec, query_rows=q, drop_keys=UNION)
            par = [(KEY_SMI[k], float(v)) for k, v in an if k in KEY_SMI][:a.parents]
            g2 = F[F.molecule == mid]; tr = g2[g2.is_truth]
            tokeys = {tk} | set(tr.official_key.astype(str))
            trraw = {mid} | {Chem.MolToInchiKey(Chem.MolFromSmiles(x))[:14] for x in tr.smiles.astype(str) if Chem.MolFromSmiles(x) is not None}
            tasks.append(((s, mid), float(np.median(list(MASS[mid].values()))), ZL[mid], par, WK.get(mid, set()) - trraw, tokeys, UNION))
        log(f"{s}: {len(tasks)} molecules")
        with Pool(a.workers, initializer=_winit, initargs=(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))) as p:
            for key, out in p.imap_unordered(job, tasks, chunksize=1):
                for src, d in out.items(): rows.append(dict(set=key[0], molecule=key[1], src=src, **d))
        log(f"{s}: done")
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
    L = [f"# Stage-2 coverage by parent source (C3, union mask; {time.strftime('%Y-%m-%d %H:%M')})", "", "| set | source | n | truth generated | truth top-1 novel (f.z) | top-3 | median novel | median db parents searched |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for (s, src), g in R.groupby(["set", "src"], sort=False):
        L.append(f"| {s} | {src} | {len(g)} | {g.gen.mean():.3f} | {(g['rank'] == 1).mean():.3f} | {(g['rank'] <= 3).mean():.3f} | {g.n_novel.median():.0f} | {g.n_dbcand.median():.0f} |")
    open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
