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
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity

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
    ap = argparse.ArgumentParser()
    for k in ("eval_csv", "store", "tier", "pop", "pool", "coco", "fold_safe", "v3", "out"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--k", type=int, default=100); ap.add_argument("--workers", type=int, default=12); ap.add_argument("--max_spectra", type=int, default=8)
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); t0 = time.time(); os.makedirs(a.out, exist_ok=True)
    import torch
    sys.path.insert(0, a.v3)
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    mols = pd.read_csv(a.eval_csv)
    dtype = fpnet.autocast_dtype("cuda"); model = fpnet.load_model(f"{a.fold_safe}/fpnet_fold0.pt", "cuda")
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
                qrows = [int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT]
                by_add = {}
                for x in sorted(qrows, key=lambda x: (add_of_row[x] != "[M+H]+", add_of_row[x], ce_of_row[x] if np.isfinite(ce_of_row[x]) else 0)):
                    by_add.setdefault(add_of_row[x], []).append(x)
                q = []
                while len(q) < a.max_spectra and any(by_add.values()):
                    for ad in list(by_add):
                        if by_add[ad] and len(q) < a.max_spectra: q.append(by_add[ad].pop(0))
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
                        d["train"] |= int(sr_) in (1, 3); d["coco"] |= int(sr_) in (2, 3)
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
                        z = model(*inp)[0].float()[0].cpu().numpy().astype(np.float32)
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
                        rep[k] = dict(i=i, tier=d["tier"], train=d["train"], coco=d["coco"], trow=d["trow"], pid=d["pid"], pkey=d["pkey"], mass=d["mass"], fp=float(fp[i]) if np.isfinite(fp[i]) else -np.inf)
                    else:
                        p = rep[k]; p["tier"] |= d["tier"]; p["train"] |= d["train"]; p["coco"] |= d["coco"]
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
                L = {v: np.zeros(n_u) for v in ("c1", "c2", "c1_keepdup", "c2_keepdup", "same_c1", "same_c2")}; nref = {v: np.zeros(n_u, int) for v in ("c1", "c2")}
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
                        susp = any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == mode_of_row[x] and entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= DUP_SIM for s in qspec)
                        if susp: n_susp_truth += int(is_truth_cand); n_susp_other += int(not is_truth_cand); kept_susp.append(x)
                        else: kept.append(x)

                    def cap(rows_):
                        if len(rows_) > MAX_REF:
                            pri = np.array([0 if add_of_row[x] in M_by_add else 1 for x in rows_]); rows_ = [rows_[i] for i in np.argsort(pri, kind="stable")[:MAX_REF]]
                        return rows_
                    main_refs = cap(kept); keep_refs = cap(kept + kept_susp)
                    for tag, refs in (("", main_refs), ("_keepdup", keep_refs)):
                        b1 = b2 = s1 = s2 = 0.0; n1 = n2 = 0
                        for x in refs:
                            (rmz, rit), rprec = ref_cache[x]
                            k1 = not (is_truth_cand and lib_of_row[x] == lib); k2 = not is_truth_cand
                            n1 += int(k1); n2 += int(k2)
                            if not (k1 or k2): continue
                            for s in qspec:
                                if s["mode"] != mode_of_row[x]: continue
                                sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); same = add_of_row[x] == s["adduct"]
                                if k1: b1 = max(b1, sim); s1 = max(s1, sim if same else 0.0)
                                if k2: b2 = max(b2, sim); s2 = max(s2, sim if same else 0.0)
                        L["c1" + tag][ci], L["c2" + tag][ci] = b1, b2
                        if tag == "": L["same_c1"][ci], L["same_c2"][ci] = s1, s2; nref["c1"][ci], nref["c2"][ci] = n1, n2
                    if is_truth_cand: usable_truth_c1 = max(usable_truth_c1, sum(1 for x in main_refs if lib_of_row[x] != lib))
                if len(ref_cache) > 300_000: ref_cache.clear()
                # ---- per-view shortlists; stored table = union; official keys; merge duplicates
                fpz = np.nan_to_num(fpu, nan=np.nanmin(fpu) if np.isfinite(fpu).any() else 0.0); zf = (fpz - fpz.mean()) / (fpz.std() + 1e-9)
                K = min(a.k, n_u)
                top_fp = set(np.argsort(-np.nan_to_num(fpu, nan=-1e18), kind="stable")[:K].tolist()); top_fpp = set(np.argsort(-(zf + SHORTLIST_LAM * pop), kind="stable")[:K].tolist())
                top_lib = {v: {int(i) for i in np.argsort(-L[v], kind="stable")[:K_LIB] if L[v][i] > LIB_MIN} for v in ("c1", "c2")}
                short_v = {v: top_fp | top_fpp | top_lib[v] for v in ("c1", "c2")}
                short = sorted(short_v["c1"] | short_v["c2"])
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
                                         in_top_fp=bool(si & top_fp), in_top_fpprior=bool(si & top_fpp), in_top_lib_c1=bool(si & top_lib["c1"]), in_top_lib_c2=bool(si & top_lib["c2"]),
                                         **{n: float(comp[n][i]) for n in comp}, pop_public=float(pop[i])))
                runner.append(dict(mid=mid, spectra=[dict(mz=s["mz"].tolist(), it=s["it"].tolist(), prec=s["prec"], adduct=s["adduct"], mode=s["mode"], instrument=s["instrument"],
                                                          ce_ev=[s["ce"]] if s["ce"] is not None else None, ce_orig=None, ce_units="eV" if s["ce"] is not None else None) for s in qspec],
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
    json.dump(dict(k=a.k, shortlist_lam=SHORTLIST_LAM, ppm=PPM, max_spectra=a.max_spectra, max_ref=MAX_REF, dup_sim=DUP_SIM, fpnet=sha(f"{a.fold_safe}/fpnet_fold0.pt"), pool=sha(a.pool),
                   rdkit=rdkit.__version__, seconds=round(time.time() - t0)), open(f"{a.out}/b1_features_manifest.json", "w"), indent=1)
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
