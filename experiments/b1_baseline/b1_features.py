import os as _os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"): _os.environ.setdefault(_v, "1")   # one BLAS thread per process
"""B1 step 1 (v2, after Codex 006) -- unified, label-free candidate feature table for frozen evaluation molecules under the class-1
and class-2 scenario views.

Per molecule (query = up to --max_spectra spectra of its selection library with test adducts, round-robin over adducts; enveda-180
positive m/z electron-corrected):
  windows   : neutral mass per adduct (median) -> +-10 ppm windows over the PubChem tier, the v2 pool (train / COCONUT) and the prvsiyan
              COCONUT set; SMILES de-duplicated across the adduct windows BEFORE fingerprinting; workers return raw InChIKey14 + fold-0
              FPNet f.z; duplicates merged on the raw key with provenance OR-ed.
  reach     : truth reachable through an external source inside the B1 windows (raw key or tautomer-alias key of the truth found among
              candidates with tier/COCONUT provenance) -> reach_external_b1 (the strict class-2 mask).
  FPNet     : spectra merged per polarity (eval_ckpt protocol), logits averaged over polarity groups weighted by spectrum count.
  library   : entropy similarity of the query spectra against reference spectra of candidates that are train structures (same polarity).
              References are classified first: EXACT duplicates (same adduct, |dprec| < 5 mDa, identical cleaned peak lists) are never
              used; SUSPECTED duplicates (|dprec| < 5 mDa, similarity >= DUP_SIM) are excluded from the main similarity but a second
              similarity that keeps them is also stored (lib_sim_*_keepdup). MAX_REF is applied AFTER the duplicate classification,
              preferring references with the query adducts. Views: C2 removes every reference of the truth and hides its train
              membership; C1 removes only the truth's references from the SELECTION library.
  priors    : popularity dataset components (tier / pool rows).
  shortlist : per view -- top-K by FP, top-K by z(FP)+SHORTLIST_LAM*pop, top-20 by that view's library similarity; the stored table is the
              union (forward models are run once) with membership flags in_short_c1 / in_short_c2; official scorer keys for the union,
              duplicates merged; truth identified by official key.
Outputs: <out>/b1_features_<set>.parquet, <out>/b1_molecules_<set>.csv (incl. reach_external_b1, duplicate counts, usable C1 refs),
         <out>/b1_runner_<set>_in.json, <out>/b1_features_manifest.json
Usage: python -X utf8 b1_features.py --eval_csv p1_molecules.csv --store DIR --tier DIR --pop DIR --pool pool_meta.parquet --coco DIR
                                     --fold_safe DIR --v3 DIR --out DIR [--k 100] [--workers 12] [--sets A_timstof B_nplib] [--limit N]
"""
import argparse, hashlib, json, os, pickle, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity, forward_proxies, select_queries

PPM, SHORTLIST_LAM, MAX_REF, DUP_SIM, K_LIB, LIB_MIN = 10.0, 0.15, 24, 0.98, 20, 0.2
MAX_HEAVY_FORWARD = 100   # structures above this are not sent to the forward models (GLACIER rejects them; ICEBERG crashed a CUDA context)


def _init(v3, fs):
    global chem_w, bits_w, Chem, TAUT
    sys.path.insert(0, v3)
    from casmi import chem as chem_w
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    bits_w = np.load(f"{fs}/fp_bits.npy")


def _feat(args):
    smiles, zlog = args
    keys = [None] * len(smiles); sc = np.full(len(smiles), np.nan, np.float32)
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(s)
        if m is None: continue
        try: keys[i] = Chem.MolToInchiKey(m)[:14]
        except Exception: continue
        f = chem_w.raw_fingerprint(s)
        if f is not None: sc[i] = float(f[bits_w].astype(np.float32) @ zlog)
    return keys, sc


def _okey(smiles):
    out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s); Chem.RemoveStereochemistry(m); out.append(Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14])
        except Exception:
            out.append(None)
    return out


def heavy_ok(smiles):
    try:
        from rdkit import Chem
        m = Chem.MolFromSmiles(smiles); return m is not None and m.GetNumHeavyAtoms() <= MAX_HEAVY_FORWARD
    except Exception:
        return False


def rank_of(scores, idx):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    return int(np.sum(s >= s[idx])) if idx is not None and idx >= 0 else None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""): h.update(chunk)
    return h.hexdigest()


def exact_dup(q, rmz, rit, rprec, radd):
    """same adduct, precursor within 5 mDa, identical cleaned peak list (m/z within 2e-4, intensity within 1e-3)."""
    if q["adduct"] != radd or abs(q["prec"] - rprec) >= 0.005: return False
    qmz, qit = q["clean"]
    return len(qmz) == len(rmz) and len(qmz) > 0 and np.allclose(qmz, rmz, atol=2e-4) and np.allclose(qit, rit, atol=1e-3)


def main():
    global MAX_REF   # --max_ref (2026-10-26) overrides the module default; nested helpers read the global
    ap = argparse.ArgumentParser()
    for k in ("eval_csv", "store", "tier", "pop", "pool", "coco", "fold_safe", "v3", "out"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--k", type=int, default=100); ap.add_argument("--workers", type=int, default=12); ap.add_argument("--max_spectra", type=int, default=8)
    ap.add_argument("--k_fpp", type=int, default=None, help="FP+prior branch size (default = --k)"); ap.add_argument("--k_pool", type=int, default=0, help="pool-window FP branch size: FP top-k among the window's v2-pool structures (default 0 = off)"); ap.add_argument("--k_pop", type=int, default=0, help="prior-only branch size (default 0 = off)")
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--adduct_proxy", action="store_true", help="forward-model proxies for molecules without a covered positive spectrum: [M+NH4]+ / [M-H2O+H]+ scored as [M+H]+ (public N1A arm A)")
    ap.add_argument("--neg_proxy", action="store_true", help="EXPERIMENTAL: also map negative-mode spectra of such molecules onto the positive axis (see b1_common.forward_proxies)")
    ap.add_argument("--lib_conditions", action="store_true", help="Codex 030: also store, per candidate and view, the library support by query CONDITION "
                    "(adduct x 10-eV CE bucket; unknown CE = own bucket): lib_sup2_* = second-highest per-condition max similarity (NaN if < 2 comparable "
                    "conditions), lib_ncond_* = number of comparable conditions; same references, masks and caps as lib_sim_* (default off = unchanged)")
    ap.add_argument("--dup_sim", type=float, default=DUP_SIM, help="similarity threshold of the SUSPECTED-duplicate rule (default 0.98 = unchanged; > 1 keeps every non-exact "
                    "reference = the pipeline's --dup_sim 1.01 rule; Codex 032 diagnostic). Exact duplicates are always removed.")
    ap.add_argument("--sym_lib_mask", action="store_true", help="DIAGNOSTIC (Codex 030 audit): in the C1 view remove the query library's references for EVERY candidate, "
                    "not only for the truth (symmetric mask), to check that library features do not exploit the evaluation mask; never for training tables")
    ap.add_argument("--extra_ckpts", nargs="*", default=[], help="additional FPNet checkpoints; the query fingerprint logits are averaged over <fold_safe>/fpnet_fold0.pt and these "
                    "(same rule as b1_pipeline with several models); default none = single model, unchanged")
    ap.add_argument("--max_ref", type=int, default=MAX_REF, help="references kept per candidate after the duplicate rule (default 24 = unchanged; 2026-10-26 reference-cap test)")
    a = ap.parse_args(); t0 = time.time(); os.makedirs(a.out, exist_ok=True)
    MAX_REF = a.max_ref
    import torch
    sys.path.insert(0, a.v3)
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    mols = pd.read_csv(a.eval_csv)
    dtype = fpnet.autocast_dtype("cuda"); model = fpnet.load_model(f"{a.fold_safe}/fpnet_fold0.pt", "cuda")
    extra_models = [fpnet.load_model(p_, "cuda") for p_ in a.extra_ckpts]
    if extra_models: print(f"FPNet ensemble: {1 + len(extra_models)} models ({a.fold_safe}/fpnet_fold0.pt + {a.extra_ckpts}); logits averaged", flush=True)
    # ---- spectra store
    S_MZ = np.load(f"{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy(); inst_of_row = meta["instrument_type"].to_numpy()
    key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    print(f"store: {meta.height:,} spectra, {len(key_rows):,} identities ({time.time()-t0:.0f}s)", flush=True)

    def spectrum(row, shift=0.0):
        s, e = int(S_OFF[row]), int(S_OFF[row + 1])
        return np.asarray(S_MZ[s:e], np.float64) - shift, np.asarray(S_IT[s:e], np.float64)

    # ---- candidate stores
    tmass = np.load(f"{a.tier}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{a.tier}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{a.tier}/pc_smiles.npy", mmap_mode="r")
    PC = {n: np.load(f"{a.pop}/pc_{n}.npy", mmap_mode="r") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    pool = pl.read_parquet(a.pool).select("key", "smiles", "mass", "src", "pid")
    assert (pool["pid"].to_numpy() == np.arange(pool.height)).all()
    PL = {n: np.load(f"{a.pop}/pool_{n}.npy") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    order = np.argsort(pool["mass"].to_numpy(), kind="stable")
    pmass = pool["mass"].to_numpy()[order]; psmi = pool["smiles"].to_numpy()[order]; psrc = pool["src"].to_numpy()[order]; ppid = pool["pid"].to_numpy()[order]; pkey = pool["key"].to_numpy()[order]
    key2smiles = dict(zip(pool.filter(pl.col("src").is_in([1, 3]))["key"].to_list(), pool.filter(pl.col("src").is_in([1, 3]))["smiles"].to_list()))
    cmeta = pickle.load(open(f"{a.coco}/coco_meta.pkl", "rb")); cmass = np.load(f"{a.coco}/coco_mass.npy"); csmi = np.asarray(cmeta["smiles"])

    def tier_window(lo_m, hi_m):
        lo = int(np.searchsorted(tmass, lo_m, "left")); hi = int(np.searchsorted(tmass, hi_m, "right"))
        if hi <= lo: return [], np.zeros(0, np.int64), np.zeros(0)
        o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
        return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)], np.arange(lo, hi), np.asarray(tmass[lo:hi], np.float64)

    def alias_keys(smi, raw):
        keys = {raw} if raw else set()
        if not smi: return keys
        try:
            m = Chem.MolFromSmiles(smi); Chem.RemoveStereochemistry(m)
            for t in TAUT.Enumerate(m):
                try: keys.add(Chem.MolToInchiKey(t)[:14])
                except Exception: pass
        except Exception:
            pass
        return keys

    with Pool(a.workers, initializer=_init, initargs=(a.v3, a.fold_safe)) as wp, torch.no_grad():
        for set_name in a.sets:
            ms = mols[mols.set == set_name]
            if a.limit: ms = ms.head(a.limit)
            rows_out, cand_out, runner, ref_cache = [], [], [], {}
            for n_i, r in enumerate(ms.itertuples(index=False)):
                tm0 = time.time(); mid = r.molecule; truth_key = r.scorer_key; lib = r.lib; shift = ELECTRON if lib == "enveda-180" else 0.0
                truth_raw = getattr(r, "raw_key", None)
                # ---- query spectra: selection library, test adducts, round-robin over adducts (same policy as the submission pipeline)
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)   # store-row order = tie-break
                q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))   # shared policy (b1_common)
                assert all(lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT for x in q), (mid, lib, "query outside selection library / test adducts")
                if not q: print("skip", mid, "no query spectra"); continue
                qspec = []
                for x in q:
                    sh = shift if mode_of_row[x] == "positive" else 0.0
                    mz, it = spectrum(x, sh); prec = float(prec_of_row[x]) - sh
                    qspec.append(dict(row=x, mz=mz, it=it, prec=prec, adduct=add_of_row[x], mode=mode_of_row[x], instrument=inst_of_row[x] or "", ce=float(ce_of_row[x]) if np.isfinite(ce_of_row[x]) else None,
                                      clean=clean_peaks(mz, it, prec)))
                query_rows = {s["row"] for s in qspec}
                # ---- neutral masses per adduct -> windows; SMILES de-duplicated across windows before fingerprinting
                M_by_add = {}
                for s in qspec: M_by_add.setdefault(s["adduct"], []).append(s["prec"] + ADDUCT_SHIFT[s["adduct"]])
                M_by_add = {k: float(np.median(v)) for k, v in M_by_add.items()}
                src = {}
                for ad, M in M_by_add.items():
                    tol = M * PPM * 1e-6
                    ts, trows, tms = tier_window(M - tol, M + tol)
                    for s_, tr_, m_ in zip(ts, trows, tms):
                        d = src.setdefault(s_, dict(tier=False, train=False, coco=False, trow=-1, pid=-1, pkey=None, mass=float(m_))); d["tier"] = True
                        if d["trow"] < 0: d["trow"] = int(tr_)
                    lo = int(np.searchsorted(pmass, M - tol, "left")); hi = int(np.searchsorted(pmass, M + tol, "right"))
                    for s_, sr_, pi_, pk_, m_ in zip(psmi[lo:hi], psrc[lo:hi], ppid[lo:hi], pkey[lo:hi], pmass[lo:hi]):
                        d = src.setdefault(str(s_), dict(tier=False, train=False, coco=False, trow=-1, pid=-1, pkey=None, mass=float(m_)))
                        d["train"] |= int(sr_) in (1, 3); d["coco"] |= int(sr_) in (2, 3); d["psrc"] = d.get("psrc", 0) | int(sr_)   # pool source bits (1 train, 2 COCONUT)
                        if d["pid"] < 0: d["pid"] = int(pi_); d["pkey"] = str(pk_)
                    clo = int(np.searchsorted(cmass, M - tol, "left")); chi = int(np.searchsorted(cmass, M + tol, "right"))
                    for s_, m_ in zip(csmi[clo:chi], cmass[clo:chi]):
                        d = src.setdefault(str(s_), dict(tier=False, train=False, coco=False, trow=-1, pid=-1, pkey=None, mass=float(m_))); d["coco"] = True
                smiles = list(src)
                # ---- FPNet logits: merge per polarity (eval_ckpt protocol), weighted mean over polarity groups
                zl, wsum = None, 0.0
                for mode in ("positive", "negative"):
                    grp = [s for s in qspec if s["mode"] == mode]
                    if not grp: continue
                    pairs = [(s["mz"], s["it"]) for s in grp]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                    prec = float(np.median([s["prec"] for s in grp])); ces = [s["ce"] for s in grp if s["ce"] is not None]
                    ad = Counter(s["adduct"] for s in grp).most_common(1)[0][0]
                    pm, pi = fpnet.prep_peaks(mz, it, prec)
                    inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                              n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)], "cuda")
                    with torch.autocast("cuda", dtype=dtype):
                        if extra_models: z = torch.stack([m_(*inp)[0].float()[0] for m_ in [model] + extra_models]).mean(0).cpu().numpy().astype(np.float32)
                        else: z = model(*inp)[0].float()[0].cpu().numpy().astype(np.float32)
                    zl = z * len(grp) if zl is None else zl + z * len(grp); wsum += len(grp)
                zlog = (zl / wsum).astype(np.float32)
                # ---- raw keys + FP for every window structure, merge on raw key
                chunks = [smiles[i:i + 400] for i in range(0, len(smiles), 400)]
                res = wp.map(_feat, [(c, zlog) for c in chunks]) if chunks else []
                raw_keys = [k for rr in res for k in rr[0]]; fp = np.concatenate([rr[1] for rr in res]) if res else np.zeros(0, np.float32)
                rep = {}
                for i, k in enumerate(raw_keys):
                    if k is None: continue
                    d = src[smiles[i]]
                    if k not in rep:
                        rep[k] = dict(i=i, tier=d["tier"], train=d["train"], coco=d["coco"], trow=d["trow"], pid=d["pid"], pkey=d["pkey"], mass=d["mass"], fp=float(fp[i]) if np.isfinite(fp[i]) else -np.inf, psrc=d.get("psrc", 0))
                    else:
                        p = rep[k]; p["tier"] |= d["tier"]; p["train"] |= d["train"]; p["coco"] |= d["coco"]; p["psrc"] = p.get("psrc", 0) | d.get("psrc", 0)
                        if p["trow"] < 0: p["trow"] = d["trow"]
                        if p["pid"] < 0: p["pid"] = d["pid"]; p["pkey"] = d["pkey"]
                        if np.isfinite(fp[i]) and fp[i] > p["fp"]: p["fp"] = float(fp[i])
                keys = list(rep); n_u = len(keys)
                if n_u == 0:
                    rows_out.append(dict(set=set_name, molecule=mid, group=r.group, lib=lib, identity_group=int(getattr(r, "identity_group", -1)), n_query=len(qspec), n_unique=0,
                                         reach_external_b1=False, truth_in_window=False, truth_in_shortlist=False, c1_possible=False, c1_usable=False)); continue
                fpu = np.array([rep[k]["fp"] for k in keys]); fpu[~np.isfinite(fpu)] = np.nan
                trow = np.array([rep[k]["trow"] for k in keys]); pid = np.array([rep[k]["pid"] for k in keys])
                in_train = np.array([rep[k]["train"] for k in keys]); in_coco = np.array([rep[k]["coco"] for k in keys]); in_tier = np.array([rep[k]["tier"] for k in keys])
                cm = np.array([rep[k]["mass"] for k in keys], float)
                ppm_err = np.min(np.abs(np.array([[(M - m) / m * 1e6 for m in cm] for M in M_by_add.values()])), axis=0)
                # ---- truth reach inside the B1 windows (raw key or tautomer alias) via an external source; truth's train membership hidden
                aliases = alias_keys(key2smiles.get(truth_key, ""), truth_raw)
                truth_idx = [i for i, k in enumerate(keys) if k in aliases or rep[k]["pkey"] == truth_key]
                reach_external = bool(any(in_tier[i] or in_coco[i] for i in truth_idx)); truth_in_window = bool(truth_idx)
                train_flag_orig = in_train.copy()
                for i in truth_idx: in_train[i] = False
                # ---- priors
                comp = {n: np.zeros(n_u, np.float32) for n in PC}
                ht = trow >= 0; hp = (~ht) & (pid >= 0)
                for n in comp:
                    if ht.any(): comp[n][ht] = np.asarray(PC[n][np.sort(trow[ht])], dtype=np.float32)[np.argsort(np.argsort(trow[ht]))]
                    if hp.any(): comp[n][hp] = np.asarray(PL[n][pid[hp]], dtype=np.float32)
                comp["np"][(~ht) & (~hp)] = 1.0; comp["np"][in_coco] = np.maximum(comp["np"][in_coco], 1.0)
                pop = comp["lsid"] + comp["lpmid"] + 0.5 * comp["lsynonyms"] + 1.0 * (comp["np"] != 0) + 0.5 * ((comp["src_mask"].astype(np.int64) & 1) != 0) + 0.5 * np.log1p(np.maximum(comp["lotus_refs"], 0))
                # ---- library similarity (train-structure candidates); duplicate classification first, then MAX_REF
                L = {v: np.zeros(n_u) for v in ("c1", "c2", "c1_keepdup", "c2_keepdup", "same_c1", "same_c2")}; nref = {v: np.zeros(n_u, int) for v in ("c1", "c2")}; nsame = {v: np.zeros(n_u, int) for v in ("c1", "c2")}
                SUP2 = {v: np.full(n_u, np.nan) for v in ("c1", "c2")}; NCOND = {v: np.zeros(n_u, int) for v in ("c1", "c2")}
                qcond = [(q_["adduct"], int(round(q_["ce"] / 10.0)) if q_["ce"] is not None else "na") for q_ in qspec]   # query condition (label-free)
                n_exact_truth = n_susp_truth = n_exact_other = n_susp_other = 0; usable_truth_c1 = 0
                truth_set = set(truth_idx)
                for ci, k in enumerate(keys):
                    pk = rep[k]["pkey"]
                    if pk is None or pk not in key_rows or not train_flag_orig[ci]: continue
                    is_truth_cand = (pk == truth_key) or (ci in truth_set)
                    rrows = [int(x) for x in key_rows[pk] if x not in query_rows]
                    kept, kept_susp = [], []
                    for x in rrows:
                        if x not in ref_cache:
                            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                            mz, it = spectrum(x, sh); ref_cache[x] = (clean_peaks(mz, it, float(prec_of_row[x]) - sh), float(prec_of_row[x]) - sh)
                        (rmz, rit), rprec = ref_cache[x]
                        if any(exact_dup(s, rmz, rit, rprec, add_of_row[x]) for s in qspec):
                            n_exact_truth += int(is_truth_cand); n_exact_other += int(not is_truth_cand); continue
                        susp = any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == mode_of_row[x] and entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= a.dup_sim for s in qspec)
                        if susp: n_susp_truth += int(is_truth_cand); n_susp_other += int(not is_truth_cand); kept_susp.append(x)
                        else: kept.append(x)

                    def cap(rows_):
                        if len(rows_) > MAX_REF:
                            pri = np.array([0 if add_of_row[x] in M_by_add else 1 for x in rows_]); rows_ = [rows_[i] for i in np.argsort(pri, kind="stable")[:MAX_REF]]
                        return rows_
                    # Scenario exclusion FIRST, then MAX_REF (the submission pipeline's order; Codex 012 found 9/300 dev C1 molecules whose truth lost
                    # its usable other-library references because the cap used to run before the same-library exclusion). C1 view: the truth's
                    # own-library references are removed; C2 view: every reference of the truth is removed; other candidates keep all references.
                    for tag, pool in (("", kept), ("_keepdup", kept + kept_susp)):
                        refs1 = cap([x for x in pool if not ((is_truth_cand or a.sym_lib_mask) and lib_of_row[x] == lib)])
                        b1 = s1 = 0.0; n1 = ns1 = 0; cmax_ = {}
                        for x in refs1:
                            (rmz, rit), rprec = ref_cache[x]
                            n1 += 1; sa = add_of_row[x] in M_by_add; ns1 += int(sa)
                            for qi_, s in enumerate(qspec):
                                if s["mode"] != mode_of_row[x]: continue
                                sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); same = add_of_row[x] == s["adduct"]
                                b1 = max(b1, sim); s1 = max(s1, sim if same else 0.0)
                                if a.lib_conditions and tag == "": cmax_[qcond[qi_]] = max(cmax_.get(qcond[qi_], 0.0), sim)
                        if a.lib_conditions and tag == "":
                            v_ = sorted(cmax_.values(), reverse=True)
                            SUP2["c1"][ci] = v_[1] if len(v_) >= 2 else np.nan; NCOND["c1"][ci] = len(v_)
                            if not is_truth_cand: SUP2["c2"][ci], NCOND["c2"][ci] = SUP2["c1"][ci], NCOND["c1"][ci]   # C2 view: the truth has no references
                        b2, s2, n2, ns2 = (0.0, 0.0, 0, 0) if is_truth_cand else (b1, s1, n1, ns1)
                        L["c1" + tag][ci], L["c2" + tag][ci] = b1, b2
                        if tag == "": L["same_c1"][ci], L["same_c2"][ci] = s1, s2; nref["c1"][ci], nref["c2"][ci] = n1, n2; nsame["c1"][ci], nsame["c2"][ci] = ns1, ns2
                        if tag == "" and is_truth_cand: usable_truth_c1 = max(usable_truth_c1, len(refs1))
                if len(ref_cache) > 300_000: ref_cache.clear()
                # ---- per-view shortlists; stored table = union; official keys; merge duplicates
                fpz = np.nan_to_num(fpu, nan=np.nanmin(fpu) if np.isfinite(fpu).any() else 0.0); zf = (fpz - fpz.mean()) / (fpz.std() + 1e-9)
                K = min(a.k, n_u); K2 = min(a.k_fpp if a.k_fpp else a.k, n_u)
                top_fp = set(np.argsort(-np.nan_to_num(fpu, nan=-1e18), kind="stable")[:K].tolist()); top_fpp = set(np.argsort(-(zf + SHORTLIST_LAM * pop), kind="stable")[:K2].tolist())
                top_lib = {v: {int(i) for i in np.argsort(-L[v], kind="stable")[:K_LIB] if L[v][i] > LIB_MIN} for v in ("c1", "c2")}
                top_pop = set(np.argsort(-(pop + 1e-6 * zf), kind="stable")[:min(a.k_pop, n_u)].tolist()) if a.k_pop > 0 else set()   # prior-only branch (audit 2026-10-24)
                psrc_a = np.array([int(rep[k].get("psrc", 0)) for k in keys], dtype=np.int64)
                truth_mask = np.zeros(n_u, bool); truth_mask[list(truth_idx)] = True
                pool_elig = {"c1": pid >= 0, "c2": (pid >= 0) & ~(truth_mask & (psrc_a != 0) & ((psrc_a & ~1) == 0))}   # C2: no train-only pool slot for the truth
                def _top_pool_v(v, k_):
                    m_ = pool_elig[v]
                    return set(np.argsort(-np.where(m_, np.nan_to_num(fpu, nan=-1e18), -np.inf), kind="stable")[:min(k_, int(m_.sum()))].tolist()) if (k_ > 0 and m_.any()) else set()
                short_v = {v: top_fp | top_fpp | top_lib[v] | top_pop | _top_pool_v(v, a.k_pool) for v in ("c1", "c2")}
                short = sorted(short_v["c1"] | short_v["c2"])
                # shortlist audit (Codex 008 Q2): hypothetical branch allocations measured without forward models (sizes + truth membership)
                def _top(score, k_): return set(np.argsort(-score, kind="stable")[:min(k_, n_u)].tolist())
                fp_s = np.nan_to_num(fpu, nan=-1e18); fpp_s = zf + SHORTLIST_LAM * pop; pop_s = pop + 1e-6 * zf
                alt_short = {"fp200": _top(fp_s, 200) | top_fpp | top_lib["c2"], "fpp200": top_fp | _top(fpp_s, 200) | top_lib["c2"],
                             "fp200_fpp200": _top(fp_s, 200) | _top(fpp_s, 200) | top_lib["c2"], "pop50": short_v["c2"] | _top(pop_s, 50), "pop100": short_v["c2"] | _top(pop_s, 100),
                             "fpp200_pop50": top_fp | _top(fpp_s, 200) | top_lib["c2"] | _top(pop_s, 50)}
                # pool-window branch audit (2026-10-25, E0 comparison): E0's engine-1 ranks only the v2-pool structures of the window (~50-120);
                # hypothetical branch = current C2 shortlist + FP top-K among pool structures (pid >= 0). Audit only: the stored shortlist is unchanged.
                in_pool = pid >= 0; pool_fp_s = np.where(in_pool, fp_s, -np.inf); n_pool = int(in_pool.sum())
                alt_short["pool60"] = short_v["c2"] | _top_pool_v("c2", 60); alt_short["pool100"] = short_v["c2"] | _top_pool_v("c2", 100)   # C2-eligible pool (Codex 020)
                s_smiles = [smiles[rep[keys[i]]["i"]] for i in short]
                okeys = [k for rr in wp.map(_okey, [s_smiles[i:i + 25] for i in range(0, len(s_smiles), 25)]) for k in rr]
                best = {}
                for j, i in enumerate(short):
                    if okeys[j] is not None: best.setdefault(okeys[j], []).append(i)
                for ok, idxs in best.items():
                    i = max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18)); is_t = (ok == truth_key); si = set(idxs)
                    cand_out.append(dict(set=set_name, molecule=mid, smiles=smiles[rep[keys[i]]["i"]], official_key=ok, is_truth=is_t,
                                         in_short_c1=bool(si & short_v["c1"]), in_short_c2=bool(si & short_v["c2"]),
                                         in_tier=bool(any(in_tier[j] for j in idxs)), in_coconut=bool(any(in_coco[j] for j in idxs)),
                                         in_train_c1=bool(any(train_flag_orig[j] for j in idxs)), in_train_c2=bool(any(in_train[j] for j in idxs)),
                                         fp=float(fpu[i]) if np.isfinite(fpu[i]) else None, fp_rank_window=rank_of(fpu, i), ppm_err=float(np.nanmin([ppm_err[j] for j in idxs])),
                                         lib_sim_c1=float(max(L["c1"][j] for j in idxs)), lib_sim_c2=float(max(L["c2"][j] for j in idxs)),
                                         lib_sim_c1_keepdup=float(max(L["c1_keepdup"][j] for j in idxs)), lib_sim_c2_keepdup=float(max(L["c2_keepdup"][j] for j in idxs)),
                                         lib_same_c1=float(max(L["same_c1"][j] for j in idxs)), lib_same_c2=float(max(L["same_c2"][j] for j in idxs)),
                                         lib_nref_c1=int(max(nref["c1"][j] for j in idxs)), lib_nref_c2=int(max(nref["c2"][j] for j in idxs)),
                                         lib_nsame_c1=int(max(nsame["c1"][j] for j in idxs)), lib_nsame_c2=int(max(nsame["c2"][j] for j in idxs)),
                                         **({"lib_sup2_c1": float(np.nanmax([SUP2["c1"][j] for j in idxs])) if np.isfinite([SUP2["c1"][j] for j in idxs]).any() else np.nan,
                                             "lib_sup2_c2": float(np.nanmax([SUP2["c2"][j] for j in idxs])) if np.isfinite([SUP2["c2"][j] for j in idxs]).any() else np.nan,
                                             "lib_ncond_c1": int(max(NCOND["c1"][j] for j in idxs)), "lib_ncond_c2": int(max(NCOND["c2"][j] for j in idxs))} if a.lib_conditions else {}),
                                         in_top_fp=bool(si & top_fp), in_top_fpprior=bool(si & top_fpp), in_top_pop=bool(si & top_pop), in_top_lib_c1=bool(si & top_lib["c1"]), in_top_lib_c2=bool(si & top_lib["c2"]),
                                         **{n: float(comp[n][i]) for n in comp}, pop_public=float(pop[i])))
                rspec = [dict(mz=s["mz"].tolist(), it=s["it"].tolist(), prec=s["prec"], adduct=s["adduct"], mode=s["mode"], instrument=s["instrument"],
                              ce_ev=[s["ce"]] if s["ce"] is not None else None, ce_orig=None, ce_units="eV" if s["ce"] is not None else None) for s in qspec]
                if a.adduct_proxy: rspec += forward_proxies(rspec, neg=a.neg_proxy)   # proxies only when the molecule has no covered positive spectrum
                runner.append(dict(mid=mid, spectra=rspec,
                                   cands=[s_ for s_ in (smiles[rep[keys[max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18))]]["i"]] for idxs in best.values()) if heavy_ok(s_)]))
                truth_other_lib_refs = int(sum(1 for x in key_rows.get(truth_key, []) if lib_of_row[x] != lib))
                tb = best.get(truth_key, [])
                rows_out.append(dict(set=set_name, molecule=mid, group=r.group, lib=lib, identity_group=int(getattr(r, "identity_group", -1)), n_query=len(qspec), adducts="|".join(sorted(M_by_add)), n_adducts=len(M_by_add),
                                     ce_known=float(np.mean([s["ce"] is not None for s in qspec])), n_window_structures=len(smiles), n_unique=n_u, n_unique_train=int(train_flag_orig.sum()),
                                     truth_in_window=truth_in_window, reach_external_b1=reach_external, truth_in_shortlist=bool(tb),
                                     truth_in_short_c1=bool(set(tb) & short_v["c1"]), truth_in_short_c2=bool(set(tb) & short_v["c2"]),
                                     n_shortlist=len(best), n_short_c1=len(short_v["c1"]), n_short_c2=len(short_v["c2"]),
                                     lib_max_c1=float(L["c1"].max()), lib_max_c2=float(L["c2"].max()), truth_other_lib_refs=truth_other_lib_refs, c1_possible=truth_other_lib_refs > 0,
                                     c1_usable_refs=int(usable_truth_c1), c1_usable=usable_truth_c1 > 0,
                                     n_exact_dup_truth=n_exact_truth, n_susp_dup_truth=n_susp_truth, n_exact_dup_other=n_exact_other, n_susp_dup_other=n_susp_other,
                                     truth_lib_sim_c1=float(max([L["c1"][i] for i in truth_idx], default=0.0)), truth_lib_sim_c1_keepdup=float(max([L["c1_keepdup"][i] for i in truth_idx], default=0.0)),
                                     # shortlist audit: the truth's rank within the whole window under each shortlist branch score (-1 = truth not in window)
                                     truth_fp_rank=min([rank_of(fpu, i) for i in truth_idx], default=-1), truth_pop_rank=min([rank_of(pop + 1e-6 * zf, i) for i in truth_idx], default=-1),
                                     truth_fppop_rank=min([rank_of(zf + SHORTLIST_LAM * pop, i) for i in truth_idx], default=-1), truth_fppop50_rank=min([rank_of(zf + 0.5 * pop, i) for i in truth_idx], default=-1),
                                     truth_lib_rank_c2=min([rank_of(L["c2"], i) for i in truth_idx], default=-1), truth_lib_rank_c1=min([rank_of(L["c1"], i) for i in truth_idx], default=-1),
                                     n_pool_window=n_pool, truth_fp_rank_pool=min([rank_of(pool_fp_s, i) for i in truth_idx if in_pool[i]], default=-1),
                                     truth_pool_train_only=bool(truth_idx) and all(in_pool[i] and not (in_tier[i] or in_coco[i]) for i in truth_idx),
                                     truth_pool_eligible_c2=bool(any(pool_elig["c2"][i] for i in truth_idx)),
                                     **{f"n_short_{k_}": len(v_) for k_, v_ in alt_short.items()}, **{f"truth_in_short_{k_}": bool(truth_set & v_) for k_, v_ in alt_short.items()},
                                     seconds=time.time() - tm0))
                if (n_i + 1) % 20 == 0 or n_i == len(ms) - 1:
                    d = pd.DataFrame(rows_out)
                    print(f"  {set_name} {n_i+1}/{len(ms)} | window unique median {d.n_unique.median():.0f} | reach ext {int(d.reach_external_b1.sum())} | truth in shortlist {int(d.truth_in_shortlist.sum())} | "
                          f"c1 usable {int(d.c1_usable.sum())} | exact dup refs (truth) {int(d.n_exact_dup_truth.sum())} | {d.seconds.mean():.1f}s/mol ({time.time()-t0:.0f}s)", flush=True)
            pd.DataFrame(rows_out).to_csv(f"{a.out}/b1_molecules_{set_name}.csv", index=False)
            pd.DataFrame(cand_out).to_parquet(f"{a.out}/b1_features_{set_name}.parquet", index=False)
            json.dump(runner, open(f"{a.out}/b1_runner_{set_name}_in.json", "w"))
            print(f"saved {set_name}: {len(rows_out)} molecules, {len(cand_out)} shortlist rows ({time.time()-t0:.0f}s)", flush=True)
    import rdkit
    json.dump(dict(lib_conditions=bool(a.lib_conditions), sym_lib_mask=bool(a.sym_lib_mask), extra_ckpts=list(a.extra_ckpts), k=a.k, k_fpp=a.k_fpp, k_pop=a.k_pop, k_pool=a.k_pool, adduct_proxy=bool(a.adduct_proxy), neg_proxy=bool(a.neg_proxy), shortlist_lam=SHORTLIST_LAM, ppm=PPM, max_spectra=a.max_spectra, max_ref=MAX_REF, dup_sim=a.dup_sim, fpnet=sha(f"{a.fold_safe}/fpnet_fold0.pt"), pool=sha(a.pool),
                   rdkit=rdkit.__version__, seconds=round(time.time() - t0)), open(f"{a.out}/b1_features_manifest.json", "w"), indent=1)
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
