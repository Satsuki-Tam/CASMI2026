"""Analog channel probe (2026-10-26): does library-analog evidence add class-2 signal on top of the registered B1 ranking?

The channel itself lives in b1_analog.py (shared with the submission pipeline). This script computes the features for the shortlist of
each evaluation view with the evaluator's masks:
  * query rows never; C1 view: the truth key's representatives are re-selected from its spectra outside the query library;
  * C2 view: the truth key, the raw keys of the query molecule and the truth's identity group are removed entirely.
Labels are used only for the masks (as in the evaluator), never for the features themselves.
Output: one parquet row per (set, view, molecule, candidate smiles) of the view's shortlist (b1_locked_eval.view_frame).
Usage: python -X utf8 analog_probe.py --runs RUN:EVAL_CSV:SET1,SET2 ... --out diag/analog_<name>.parquet
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
from numba import set_num_threads
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries  # noqa: E402
import b1_analog as BA  # noqa: E402
import b1_locked_eval as E  # noqa: E402

ap_ = argparse.ArgumentParser()
ap_.add_argument("--store", default="data/processed/spectra_store")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet", help="identity groups: every key of the truth's group is removed in the C2 view")
ap_.add_argument("--runs", nargs="+", required=True, help="RUN_DIR:EVAL_CSV:SET1,SET2 (paths relative to experiments/b1_baseline)")
ap_.add_argument("--out", required=True); ap_.add_argument("--max_spectra", type=int, default=8); ap_.add_argument("--threads", type=int, default=8); ap_.add_argument("--limit", type=int, default=0)
a = ap_.parse_args()
set_num_threads(a.threads)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
T0 = time.time()
def log(*x): print(f"[analog {time.time() - T0:6.0f}s]", *x, flush=True)

S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
assert (meta["row"].to_numpy() == np.arange(meta.height)).all()
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=log)

from rdkit import Chem, RDLogger  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
RDLogger.DisableLog("rdApp.*"); GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
_FP = {}
def fp_of(smi):
    if smi not in _FP:
        m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = GEN.GetFingerprint(m) if m is not None else None
    return _FP[smi]
_idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))

rows_out = []
for spec in a.runs:
    run, eval_csv, sets = spec.split(":"); sets = sets.split(",")
    ev = pd.read_csv(os.path.join(HERE, eval_csv)); ev["molecule"] = ev["molecule"].astype(str)
    for s in sets:
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet")); F["molecule"] = F["molecule"].astype(str)
        M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")).set_index("molecule"); M.index = M.index.astype(str)
        mols = ev[ev.set == s]
        if a.limit: mols = mols.head(a.limit)
        for n_i, r in enumerate(mols.itertuples(index=False)):
            mid, lib, truth_key = str(r.molecule), r.lib, str(r.scorer_key)
            qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
            q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
            qspec = []
            for x in q:
                sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
            raw_truth_keys = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
            drop_c2 = raw_truth_keys | {truth_key} | set(GROUP_KEYS.get(KEY_GROUP.get(truth_key), set()))
            views = {"c1": store.analogs(qspec, query_rows=q, relib=(truth_key, lib), key_rows=key_rows),
                     "c2": store.analogs(qspec, query_rows=q, drop_keys=drop_c2)}
            for v, an in views.items():
                g = E.view_frame(F, M, mid, v) if mid in M.index else pd.DataFrame()
                if len(g) == 0: continue
                afp, asim, akey = [], [], []
                for k_, s_ in an:
                    f_ = fp_of(KEY_SMI.get(k_, ""))
                    if f_ is not None: afp.append(f_); asim.append(s_); akey.append(k_)
                smis = g.smiles.astype(str).tolist(); feat = BA.features([fp_of(x) for x in smis], afp, asim, cand_keys=g.official_key.astype(str).tolist(), analog_keys=akey)
                for i, smi in enumerate(smis):
                    rows_out.append(dict(set=s, view=v, molecule=mid, smiles=smi, **{k: float(feat[k][i]) for k in feat}, n_analog=len(afp), top_sim=float(asim[0]) if asim else 0.0))
            if n_i % 25 == 0: log(f"{run} {s} {n_i + 1}/{len(mols)} | rows {len(rows_out):,}")
out = pd.DataFrame(rows_out); out.to_parquet(os.path.join(HERE, a.out), index=False)
log(f"saved {a.out}: {len(out):,} rows")
