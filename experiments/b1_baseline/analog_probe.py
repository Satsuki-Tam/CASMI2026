"""Analog channel probe (2026-10-26): does library-analog evidence add class-2 signal on top of the registered B1 ranking?

B1 uses library spectra only as references of the candidate's OWN structure (lib_sim). The public analog-propagation baseline (and E0's
engine 2) also uses the library as a neighbourhood: train spectra similar to the query (mass shift allowed, modified-cosine idea) are
"analogs", and a candidate is scored by its structural similarity to them. This is our own implementation of that idea for a probe:
  * reference store = up to --reps representative spectra per (official key, polarity) among test adducts (preference: [M+H]+ / [M-H]-,
    collision energy closest to 35 eV, store row), cleaned like B1 (clean_peaks, floor/top below) and entropy-weighted once;
  * per query spectrum (B1's query selection), shifted entropy similarity = max(plain, reference peaks shifted by the precursor difference)
    against every reference of the same polarity with |neutral mass difference| <= --win;
  * per view the masks of b1_features: query rows never; C1 view: the truth key's references from the query's own library are removed
    (its representatives are re-selected from its other-library spectra by the same rule); C2 view: the truth key is removed entirely;
  * analogs = top --n_analog keys by similarity; candidate features from Morgan (r2, 2048) Tanimoto to the analog structures:
    ap = max_a tan * sim^3, a1 = max_a tan * sim, best_tan, top_tan (to the best analog), mean_tan = sum tan sim^3 / sum sim^3.
Labels are used only for the masks (as in the evaluator), never for the features themselves.
Output: one parquet row per (set, view, molecule, candidate smiles) of the view's shortlist (b1_locked_eval.view_frame).
Usage: python -X utf8 analog_probe.py --runs RUN:EVAL_CSV:SET1,SET2 ... --out diag/analog_<name>.parquet
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
from numba import njit, prange, set_num_threads
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_weight, select_queries  # noqa: E402

ap_ = argparse.ArgumentParser()
ap_.add_argument("--store", default="data/processed/spectra_store")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--runs", nargs="+", required=True, help="RUN_DIR:EVAL_CSV:SET1,SET2 (paths relative to experiments/b1_baseline)")
ap_.add_argument("--out", required=True); ap_.add_argument("--win", type=float, default=200.0); ap_.add_argument("--n_analog", type=int, default=80)
ap_.add_argument("--reps", type=int, default=3); ap_.add_argument("--top", type=int, default=64); ap_.add_argument("--floor", type=float, default=0.005)
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet", help="identity groups: every key of the truth's group is removed in the C2 view")
ap_.add_argument("--max_spectra", type=int, default=8); ap_.add_argument("--threads", type=int, default=8); ap_.add_argument("--limit", type=int, default=0)
a = ap_.parse_args()
set_num_threads(a.threads)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
T0 = time.time()
def log(*x): print(f"[analog {time.time() - T0:6.0f}s]", *x, flush=True)


@njit(cache=True, fastmath=True)
def _sim(qmz, qp, qS, rmz, rp, rS, shift):
    i = 0; j = 0; n = len(qmz); m = len(rmz); Sm = 0.0
    while i < n and j < m:
        rm = rmz[j] + shift; tol = max(0.01, qmz[i] * 20e-6); d = qmz[i] - rm
        if abs(d) <= tol:
            v = 0.5 * (qp[i] + rp[j]); i += 1; j += 1
        elif d < 0:
            v = 0.5 * qp[i]; i += 1
        else:
            v = 0.5 * rp[j]; j += 1
        if v > 0: Sm -= v * np.log(v)
    while i < n:
        v = 0.5 * qp[i]; i += 1
        if v > 0: Sm -= v * np.log(v)
    while j < m:
        v = 0.5 * rp[j]; j += 1
        if v > 0: Sm -= v * np.log(v)
    s = 1.0 - (2.0 * Sm - qS - rS) / np.log(4.0)
    return min(1.0, max(0.0, s))


@njit(cache=True, fastmath=True, parallel=True)
def _search(qmz, qp, qS, qprec, lo, hi, roff, rmz, rp, rS, rprec):
    out = np.zeros(hi - lo, np.float32)
    for k in prange(hi - lo):
        r = lo + k; s0 = _sim(qmz, qp, qS, rmz[roff[r]:roff[r + 1]], rp[roff[r]:roff[r + 1]], rS[r], 0.0)
        sh = qprec - rprec[r]
        if abs(sh) > 0.001:
            s1 = _sim(qmz, qp, qS, rmz[roff[r]:roff[r + 1]], rp[roff[r]:roff[r + 1]], rS[r], sh)
            if s1 > s0: s0 = s1
        out[k] = s0
    return out


# ---------------------------------------------------------------- spectra store and representatives
S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}


def shift_of(x): return ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
def spectrum(x):
    o0, o1 = S_OFF[x], S_OFF[x + 1]; sh = shift_of(x)
    return np.asarray(S_MZ[o0:o1], np.float64) - sh, np.asarray(S_IT[o0:o1], np.float64)
def cleaned(x):
    mz, it = spectrum(x); prec = float(prec_of_row[x]) - shift_of(x)
    cm, ci = clean_peaks(mz, it, prec, floor=a.floor, top=a.top)
    if len(ci) == 0: return None
    p = entropy_weight(ci); S = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    return cm.astype(np.float64), p.astype(np.float64), S, prec


ok_add = meta["adduct"].is_in(list(ADDUCT_SHIFT)) & meta["scorer_ik14"].is_not_null()
cand_rows = meta.filter(ok_add).with_columns(
    pl.when(pl.col("adduct").is_in(["[M+H]+", "[M-H]-"])).then(0).otherwise(1).alias("pri"),
    (pl.col("ce_mean") - 35.0).abs().fill_nan(999.0).fill_null(999.0).alias("ced"))


def pick_reps(df):
    return df.sort(["pri", "ced", "row"]).group_by(["scorer_ik14", "ionization_mode"], maintain_order=True).head(a.reps)


reps = pick_reps(cand_rows)
log(f"representatives: {reps.height:,} spectra for {reps['scorer_ik14'].n_unique():,} keys (from {cand_rows.height:,} test-adduct spectra)")
KEYS = sorted(set(reps["scorer_ik14"].to_list())); KIX = {k: i for i, k in enumerate(KEYS)}
STORE = {}
for mode in ("positive", "negative"):
    rr = reps.filter(pl.col("ionization_mode") == mode)["row"].to_numpy()
    items, Ms = [], []
    for x in rr:
        c = cleaned(int(x))
        if c is None: continue
        items.append((int(x), c)); Ms.append(c[3] + ADDUCT_SHIFT[add_of_row[x]])
    o = np.argsort(np.asarray(Ms), kind="stable"); items = [items[i] for i in o]; Ms = np.asarray(Ms)[o]
    lens = np.array([len(c[0]) for _, c in items], np.int64); off = np.zeros(len(items) + 1, np.int64); np.cumsum(lens, out=off[1:])
    STORE[mode] = dict(M=Ms, row=np.array([x for x, _ in items], np.int64), off=off, mz=np.concatenate([c[0] for _, c in items]), p=np.concatenate([c[1] for _, c in items]),
                       S=np.array([c[2] for _, c in items]), prec=np.array([c[3] for _, c in items]), key=np.array([KIX[key_of_row[x]] for x, _ in items], np.int64),
                       lib=np.array([lib_of_row[x] for x, _ in items], dtype=object))
    log(f"store {mode}: {len(items):,} spectra, {len(STORE[mode]['mz']):,} peaks")

# ---------------------------------------------------------------- structures and fingerprints
from rdkit import Chem, DataStructs, RDLogger  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
RDLogger.DisableLog("rdApp.*")
GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
_FP = {}
_idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
def fp_of(smi):
    if smi not in _FP:
        m = Chem.MolFromSmiles(smi); _FP[smi] = GEN.GetFingerprint(m) if m is not None else None
    return _FP[smi]

sys.path.insert(0, HERE)
import b1_locked_eval as E  # noqa: E402

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
            qset = set(q)
            best = {}   # (mode-independent) key index -> max similarity, from representatives
            for x in q:
                c = cleaned(x)
                if c is None: continue
                qmz, qp, qS, qprec = c; Mq = qprec + ADDUCT_SHIFT[add_of_row[x]]; st = STORE[mode_of_row[x]]
                lo = int(np.searchsorted(st["M"], Mq - a.win, "left")); hi = int(np.searchsorted(st["M"], Mq + a.win, "right"))
                if hi <= lo: continue
                sims = _search(qmz, qp, qS, qprec, lo, hi, st["off"], st["mz"], st["p"], st["S"], st["prec"])
                keep = np.flatnonzero(sims > 0.05)
                for kk in keep:
                    ridx = lo + kk
                    if int(st["row"][ridx]) in qset: continue
                    ki = int(st["key"][ridx]); v = float(sims[kk])
                    lib_r = st["lib"][ridx]
                    # C1 view needs the truth key without its own-library references: tag such hits
                    tag = (ki, lib_r == lib)
                    if v > best.get(tag, 0.0): best[tag] = v
            # truth key, C1 view: representatives re-selected from its other-library spectra (same rule)
            truth_c1 = 0.0
            tk = KIX.get(truth_key)
            tr = cand_rows.filter((pl.col("scorer_ik14") == truth_key) & (pl.col("ingest_lib") != lib) & ~pl.col("row").is_in(list(qset)))
            if tr.height:
                trep = pick_reps(tr)["row"].to_numpy()
                for x in q:
                    c = cleaned(x)
                    if c is None: continue
                    qmz, qp, qS, qprec = c
                    for y in trep:
                        if mode_of_row[y] != mode_of_row[x]: continue
                        cy = cleaned(int(y))
                        if cy is None: continue
                        s0 = _sim(qmz, qp, qS, cy[0], cy[1], cy[2], 0.0); sh = qprec - cy[3]
                        if abs(sh) > 0.001: s0 = max(s0, _sim(qmz, qp, qS, cy[0], cy[1], cy[2], sh))
                        truth_c1 = max(truth_c1, s0)
            raw_truth_keys = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
            grp_keys = set(GROUP_KEYS.get(KEY_GROUP.get(truth_key), set()))
            drop_c2 = {KIX[k] for k in raw_truth_keys | {truth_key} | grp_keys if k in KIX}
            for v in ("c1", "c2"):
                agg = {}
                for (ki, samelib), val in best.items():
                    if v == "c2" and ki in drop_c2: continue
                    if v == "c1" and ki == tk: continue   # replaced by the re-selected other-library value below
                    if val > agg.get(ki, 0.0): agg[ki] = val
                if v == "c1" and tk is not None and truth_c1 > 0: agg[tk] = truth_c1
                top = sorted(agg.items(), key=lambda kv: -kv[1])[:a.n_analog]
                afps, asim = [], []
                for ki, val in top:
                    f_ = fp_of(KEY_SMI.get(KEYS[ki], "")) if KEYS[ki] in KEY_SMI else None
                    if f_ is not None: afps.append(f_); asim.append(val)
                g = E.view_frame(F, M, mid, v) if mid in M.index else pd.DataFrame()
                if len(g) == 0: continue
                w = np.asarray(asim, np.float64); w3 = w ** 3
                for smi in g.smiles.astype(str):
                    f_ = fp_of(smi)
                    if f_ is None or not afps:
                        rows_out.append(dict(set=s, view=v, molecule=mid, smiles=smi, ap=0.0, a1=0.0, best_tan=0.0, top_tan=0.0, mean_tan=0.0, n_analog=len(afps), top_sim=float(w[0]) if len(w) else 0.0)); continue
                    tan = np.asarray(DataStructs.BulkTanimotoSimilarity(f_, afps), np.float64)
                    rows_out.append(dict(set=s, view=v, molecule=mid, smiles=smi, ap=float((tan * w3).max()), a1=float((tan * w).max()), best_tan=float(tan.max()), top_tan=float(tan[0]),
                                         mean_tan=float((tan * w3).sum() / (w3.sum() + 1e-9)), n_analog=len(afps), top_sim=float(w[0])))
            if n_i % 25 == 0: log(f"{run} {s} {n_i + 1}/{len(mols)} | rows {len(rows_out):,}")
out = pd.DataFrame(rows_out); os.makedirs(os.path.dirname(os.path.join(HERE, a.out)) or ".", exist_ok=True); out.to_parquet(os.path.join(HERE, a.out), index=False)
log(f"saved {a.out}: {len(out):,} rows")
