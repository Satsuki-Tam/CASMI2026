"""B1 step 1 -- unified, label-free candidate feature table for frozen evaluation molecules under class-1 and class-2 scenarios.

Per molecule (query = up to --max_spectra spectra of its selection library with test adducts; enveda-180 positive m/z electron-corrected):
  windows   : neutral mass per adduct (b1_common.ADDUCT_SHIFT, median per adduct) -> +-10 ppm windows over the PubChem tier, the v2 pool
              (train structures / COCONUT) and the prvsiyan COCONUT set; parsed once in workers (raw InChIKey14 + fold-0 FPNet f.z);
              duplicates merged on the raw key with provenance OR-ed; tier row / pool row kept for the documentation priors.
  FPNet     : spectra merged per polarity (eval_ckpt protocol), logits averaged over polarity groups weighted by spectrum count.
  library   : spectral entropy similarity of every query spectrum against the train spectra of candidates that are train structures
              (same polarity; same-adduct flag), computed once per (candidate, reference) and masked per scenario:
                C2 (class-2 proxy): all reference spectra of the truth identity removed, truth's train membership hidden;
                C1 (class-1 proxy): only the truth's spectra from the SELECTION library removed (its other-library spectra stay).
  priors    : log1p SID / PMID / synonyms, NP bits, source bits, LOTUS refs from the popularity dataset (tier or pool rows).
  shortlist : top-K by FP, top-K by z(FP)+0.15 pop, top-20 by library similarity (C1 view); official scorer keys computed for the
              shortlist, duplicates merged (max FP, OR provenance, max similarity); truth identified by official key.
Outputs: <out>/b1_features_<set>.parquet (one row per shortlist candidate, both scenario views as columns),
         <out>/b1_molecules_<set>.csv, <out>/b1_runner_<set>_in.json (GLACIER / ICEBERG input: all query spectra), manifest.
Usage: python -X utf8 b1_features.py --eval_csv p1_molecules.csv --store DIR --tier DIR --pop DIR --pool pool_meta.parquet --coco DIR
                                     --fold_safe DIR --v3 DIR --out DIR [--k 100] [--workers 12] [--sets A_timstof B_nplib] [--limit N]
"""
import os as _os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"): _os.environ.setdefault(_v, "1")   # one BLAS thread per process: 16 workers x 64 OpenBLAS threads made the Spark 30x slower
import argparse, hashlib, json, os, pickle, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import ADDUCT_SHIFT, TEST_ADDUCTS, POSITIVE, ELECTRON, clean_peaks, entropy_similarity

PPM, LAM, MAX_REF = 10.0, 0.15, 24


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


def rank_of(scores, idx):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    return int(np.sum(s >= s[idx])) if idx is not None and idx >= 0 else None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""): h.update(chunk)
    return h.hexdigest()


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
    cmeta = pickle.load(open(f"{a.coco}/coco_meta.pkl", "rb")); cmass = np.load(f"{a.coco}/coco_mass.npy"); csmi = np.asarray(cmeta["smiles"])

    def tier_window(lo_m, hi_m):
        lo = int(np.searchsorted(tmass, lo_m, "left")); hi = int(np.searchsorted(tmass, hi_m, "right"))
        if hi <= lo: return [], np.zeros(0, np.int64), np.zeros(0)
        o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
        return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)], np.arange(lo, hi), np.asarray(tmass[lo:hi], np.float64)

    with Pool(a.workers, initializer=_init, initargs=(a.v3, a.fold_safe)) as wp, torch.no_grad():
        for set_name in a.sets:
            ms = mols[mols.set == set_name]
            if a.limit: ms = ms.head(a.limit)
            rows_out, cand_out, runner = [], [], []
            for n_i, r in enumerate(ms.itertuples(index=False)):
                tm0 = time.time(); mid = r.molecule; truth_key = r.scorer_key; lib = r.lib
                shift = ELECTRON if lib == "enveda-180" else 0.0
                # ---- query spectra: selection library, test adducts, up to max_spectra (adduct-diverse: round-robin over adducts)
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
                # ---- neutral masses per adduct -> windows
                M_by_add = {}
                for s in qspec: M_by_add.setdefault(s["adduct"], []).append(s["prec"] + ADDUCT_SHIFT[s["adduct"]])
                M_by_add = {k: float(np.median(v)) for k, v in M_by_add.items()}
                smiles, src_tier, src_train, src_coco, tier_row, pool_pid, pool_key, cmass_list = [], [], [], [], [], [], [], []
                for ad, M in M_by_add.items():
                    tol = M * PPM * 1e-6
                    ts, trows, tms = tier_window(M - tol, M + tol)
                    lo = int(np.searchsorted(pmass, M - tol, "left")); hi = int(np.searchsorted(pmass, M + tol, "right"))
                    clo = int(np.searchsorted(cmass, M - tol, "left")); chi = int(np.searchsorted(cmass, M + tol, "right"))
                    smiles += ts + [str(s) for s in psmi[lo:hi]] + [str(s) for s in csmi[clo:chi]]
                    src_tier += [True] * len(ts) + [False] * (hi - lo) + [False] * (chi - clo)
                    src_train += [False] * len(ts) + [bool(x in (1, 3)) for x in psrc[lo:hi]] + [False] * (chi - clo)
                    src_coco += [False] * len(ts) + [bool(x in (2, 3)) for x in psrc[lo:hi]] + [True] * (chi - clo)
                    tier_row += list(trows) + [-1] * (hi - lo) + [-1] * (chi - clo)
                    pool_pid += [-1] * len(ts) + [int(x) for x in ppid[lo:hi]] + [-1] * (chi - clo)
                    pool_key += [None] * len(ts) + [str(x) for x in pkey[lo:hi]] + [None] * (chi - clo)
                    cmass_list += list(tms) + list(pmass[lo:hi]) + list(cmass[clo:chi])
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
                    if k not in rep:
                        rep[k] = dict(i=i, tier=src_tier[i], train=src_train[i], coco=src_coco[i], trow=tier_row[i], pid=pool_pid[i], pkey=pool_key[i], mass=cmass_list[i],
                                      fp=float(fp[i]) if np.isfinite(fp[i]) else -np.inf)
                    else:
                        p = rep[k]; p["tier"] |= src_tier[i]; p["train"] |= src_train[i]; p["coco"] |= src_coco[i]
                        if p["trow"] < 0: p["trow"] = tier_row[i]
                        if p["pid"] < 0: p["pid"] = pool_pid[i]; p["pkey"] = pool_key[i]
                        if np.isfinite(fp[i]) and fp[i] > p["fp"]: p["fp"] = float(fp[i])
                keys = list(rep); n_u = len(keys)
                if n_u == 0:
                    rows_out.append(dict(set=set_name, molecule=mid, group=r.group, n_query=len(qspec), n_unique=0)); continue
                fpu = np.array([rep[k]["fp"] for k in keys]); fpu[~np.isfinite(fpu)] = np.nan
                trow = np.array([rep[k]["trow"] for k in keys]); pid = np.array([rep[k]["pid"] for k in keys])
                in_train = np.array([rep[k]["train"] for k in keys]); in_coco = np.array([rep[k]["coco"] for k in keys]); in_tier = np.array([rep[k]["tier"] for k in keys])
                cm = np.array([rep[k]["mass"] for k in keys], float)
                ppm_err = np.min(np.abs(np.array([[(M - m) / m * 1e6 for m in cm] for M in M_by_add.values()])), axis=0) if M_by_add else np.full(n_u, np.nan)
                # ---- priors
                comp = {n: np.zeros(n_u, np.float32) for n in PC}
                ht = trow >= 0; hp = (~ht) & (pid >= 0)
                for n in comp:
                    if ht.any(): comp[n][ht] = np.asarray(PC[n][np.sort(trow[ht])], dtype=np.float32)[np.argsort(np.argsort(trow[ht]))]
                    if hp.any(): comp[n][hp] = np.asarray(PL[n][pid[hp]], dtype=np.float32)
                comp["np"][(~ht) & (~hp)] = 1.0; comp["np"][in_coco] = np.maximum(comp["np"][in_coco], 1.0)
                pop = comp["lsid"] + comp["lpmid"] + 0.5 * comp["lsynonyms"] + 1.0 * (comp["np"] != 0) + 0.5 * ((comp["src_mask"].astype(np.int64) & 1) != 0) + 0.5 * np.log1p(np.maximum(comp["lotus_refs"], 0))
                # ---- library similarity for train-structure candidates (once per (candidate, reference)); scenario masks
                lib_c1 = np.zeros(n_u); lib_c2 = np.zeros(n_u); lib_same_c1 = np.zeros(n_u); lib_same_c2 = np.zeros(n_u); nref_c1 = np.zeros(n_u, int); nref_c2 = np.zeros(n_u, int)
                ref_cache = {}
                for ci, k in enumerate(keys):
                    pk = rep[k]["pkey"]
                    if not rep[k]["train"] or pk is None or pk not in key_rows: continue
                    rrows = key_rows[pk]
                    is_truth_cand = (pk == truth_key)
                    # C2 removes every reference of the truth; C1 removes only its selection-library references
                    keep_c1 = np.array([not (is_truth_cand and lib_of_row[x] == lib) for x in rrows]); keep_c2 = np.array([not is_truth_cand] * len(rrows))
                    cand_rows = rrows[keep_c1 | keep_c2]
                    if len(cand_rows) > MAX_REF:          # prefer references with the query adducts, then spread
                        pri = np.array([0 if add_of_row[x] in M_by_add else 1 for x in cand_rows]); cand_rows = cand_rows[np.argsort(pri, kind="stable")][:MAX_REF]
                    best1 = best2 = same1 = same2 = 0.0; n1 = n2 = 0
                    for x in cand_rows:
                        if x not in ref_cache:
                            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                            mz, it = spectrum(x, sh); ref_cache[x] = clean_peaks(mz, it, float(prec_of_row[x]) - sh)
                        rmz, rit = ref_cache[x]
                        for s in qspec:
                            if s["mode"] != mode_of_row[x]: continue
                            sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); same = add_of_row[x] == s["adduct"]
                            k1 = not (is_truth_cand and lib_of_row[x] == lib); k2 = not is_truth_cand
                            if k1: best1 = max(best1, sim); same1 = max(same1, sim if same else 0.0)
                            if k2: best2 = max(best2, sim); same2 = max(same2, sim if same else 0.0)
                        n1 += int(not (is_truth_cand and lib_of_row[x] == lib)); n2 += int(not is_truth_cand)
                    lib_c1[ci], lib_c2[ci], lib_same_c1[ci], lib_same_c2[ci], nref_c1[ci], nref_c2[ci] = best1, best2, same1, same2, n1, n2
                # ---- shortlist
                fpz = np.nan_to_num(fpu, nan=np.nanmin(fpu) if np.isfinite(fpu).any() else 0.0); zf = (fpz - fpz.mean()) / (fpz.std() + 1e-9)
                K = min(a.k, n_u)
                top_fp = np.argsort(-np.nan_to_num(fpu, nan=-1e18), kind="stable")[:K]; top_fpp = np.argsort(-(zf + LAM * pop), kind="stable")[:K]
                top_lib = [i for i in np.argsort(-lib_c1, kind="stable")[:20] if lib_c1[i] > 0.2]
                short = np.union1d(np.union1d(top_fp, top_fpp), np.array(top_lib, dtype=np.int64))
                s_smiles = [smiles[rep[keys[i]]["i"]] for i in short]
                okeys = [k for rr in wp.map(_okey, [s_smiles[i:i + 25] for i in range(0, len(s_smiles), 25)]) for k in rr]
                best = {}
                for j, i in enumerate(short):
                    ok = okeys[j]
                    if ok is None: continue
                    if ok not in best: best[ok] = [i]
                    else: best[ok].append(i)
                truth_raw_in_window = any(rep[k]["pkey"] == truth_key for k in keys) or (truth_key in best)
                for ok, idxs in best.items():
                    i = max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18)); is_t = (ok == truth_key)
                    cand_out.append(dict(set=set_name, molecule=mid, smiles=smiles[rep[keys[i]]["i"]], official_key=ok, is_truth=is_t,
                                         in_tier=bool(any(in_tier[j] for j in idxs)), in_train_c1=bool(any(in_train[j] for j in idxs)), in_train_c2=bool(any(in_train[j] for j in idxs)) and not is_t,
                                         in_coconut=bool(any(in_coco[j] for j in idxs)), fp=float(fpu[i]) if np.isfinite(fpu[i]) else None, fp_rank_window=rank_of(fpu, i),
                                         ppm_err=float(np.nanmin([ppm_err[j] for j in idxs])), lib_sim_c1=float(max(lib_c1[j] for j in idxs)), lib_sim_c2=float(max(lib_c2[j] for j in idxs)),
                                         lib_same_c1=float(max(lib_same_c1[j] for j in idxs)), lib_same_c2=float(max(lib_same_c2[j] for j in idxs)),
                                         lib_nref_c1=int(max(nref_c1[j] for j in idxs)), lib_nref_c2=int(max(nref_c2[j] for j in idxs)),
                                         in_top_fp=bool(set(idxs) & set(top_fp.tolist())), in_top_fpprior=bool(set(idxs) & set(top_fpp.tolist())), in_top_lib=bool(set(idxs) & set(top_lib)),
                                         **{n: float(comp[n][i]) for n in comp}, pop_public=float(pop[i])))
                runner.append(dict(mid=mid, spectra=[dict(mz=s["mz"].tolist(), it=s["it"].tolist(), prec=s["prec"], adduct=s["adduct"], mode=s["mode"], instrument=s["instrument"],
                                                          ce_ev=[s["ce"]] if s["ce"] is not None else None, ce_orig=None, ce_units="eV" if s["ce"] is not None else None) for s in qspec],
                                   cands=[smiles[rep[keys[max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18))]]["i"]] for idxs in best.values()]))
                truth_other_lib_refs = int(sum(1 for x in key_rows.get(truth_key, []) if lib_of_row[x] != lib))
                rows_out.append(dict(set=set_name, molecule=mid, group=r.group, lib=lib, n_query=len(qspec), adducts="|".join(sorted(M_by_add)), n_adducts=len(M_by_add),
                                     ce_known=float(np.mean([s["ce"] is not None for s in qspec])), n_window_structures=len(smiles), n_unique=n_u, n_unique_train=int(in_train.sum()),
                                     truth_in_window=bool(truth_raw_in_window), truth_in_shortlist=bool(truth_key in best), n_shortlist=len(best),
                                     lib_max_c1=float(lib_c1.max()), lib_max_c2=float(lib_c2.max()), truth_other_lib_refs=truth_other_lib_refs, c1_possible=truth_other_lib_refs > 0,
                                     truth_lib_sim_c1=float(lib_c1[[keys.index(k) for k in keys if rep[k]["pkey"] == truth_key][0]]) if any(rep[k]["pkey"] == truth_key for k in keys) else None,
                                     seconds=time.time() - tm0))
                if (n_i + 1) % 20 == 0 or n_i == len(ms) - 1:
                    d = pd.DataFrame(rows_out)
                    print(f"  {set_name} {n_i+1}/{len(ms)} | window unique median {d.n_unique.median():.0f} | truth in shortlist {int(d.truth_in_shortlist.sum())} | c1 possible {int(d.c1_possible.sum())} | "
                          f"{d.seconds.mean():.1f}s/mol ({time.time()-t0:.0f}s)", flush=True)
            pd.DataFrame(rows_out).to_csv(f"{a.out}/b1_molecules_{set_name}.csv", index=False)
            pd.DataFrame(cand_out).to_parquet(f"{a.out}/b1_features_{set_name}.parquet", index=False)
            json.dump(runner, open(f"{a.out}/b1_runner_{set_name}_in.json", "w"))
            print(f"saved {set_name}: {len(rows_out)} molecules, {len(cand_out)} shortlist rows ({time.time()-t0:.0f}s)", flush=True)
    import rdkit
    json.dump(dict(k=a.k, lam=LAM, ppm=PPM, max_spectra=a.max_spectra, max_ref=MAX_REF, fpnet=sha(f"{a.fold_safe}/fpnet_fold0.pt"), pool=sha(a.pool), rdkit=rdkit.__version__, seconds=round(time.time() - t0)),
              open(f"{a.out}/b1_features_manifest.json", "w"), indent=1)
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
