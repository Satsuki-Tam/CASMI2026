"""156 (v2 prep; copy of b1_ewin.py 143) -- the E-WINDOW table of a W135 WORLD: the E sources under the world's batch-level masks
(world_masks.json written by experiments/w135/b1_world.py = the single source of truth): C3 identities leave every E source (raw / pool /
official key), C2 / C3 identities lose train membership and every reference for every query, C1 identities lose their selection-library
references and the duplicates of their query spectra (c1_excl) for every query; a structure left with no source after the masks
(a hidden train-only structure) leaves the window (Codex 156). No truth-specific rule; the c1_* and c2_* columns are
written identical (the world view). is_truth is written for labels only. Original 143 description below.
143 E2 (independent second engine) step 1: the E-WINDOW candidate table of a molecule table, per view (C1 / C2), WITHOUT any shortlist.
E window of a query = every structure within +-10 ppm (per query adduct, median neutral mass, as b1_features) of the E sources:
  v2 pool (train structures src 1, COCONUT src 2), the COCONUT store, PubChemLite structures that have a PubChem-tier row (annotation tier_row),
  and BIO (ChEBI / LIPID MAPS not in COCONUT; shipped SMILES and monoisotopic mass) -- the source family of E0's engine 2 (069 §2.3), our own code.
Per structure: FPNet f.z (the --fold_safe checkpoint's query logits, merged per polarity as b1_features), raw key, provenance (train / coconut /
pcl / bio), exact-mass ppm error; structures are merged on the OFFICIAL key (best f.z representative). Views (b1_features rules): C2 hides the
truth's train membership and every reference of the truth; C1 removes only the truth's references from its selection library; library
similarity (entropy, exact duplicates never used, suspected duplicates excluded, MAX_REF after the exclusion) for train-structure candidates.
No popularity, no GL, no shortlist. Writes <out>/ewin_<set>.parquet (one row per molecule x official key, both views' columns) and
<out>/ewin_molecules_<set>.csv (window sizes, truth in the E window, query counts) + manifest.
Usage (Spark): python -X utf8 experiments/e2/b1_ewin.py --eval_csv CSV --sets S1 S2 --fold_safe DIR --out DIR [--workers 12]"""
import os as _os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"): _os.environ.setdefault(_v, "1")
import argparse, json, os, pickle, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity, select_queries
import b1_features as BF
from b1_features import PPM, sha, exact_dup
K = os.path.join(ROOT, "data/external_kaggle")
PCLP = f"{K}/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet"
BIOP = f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi-chebi-lmsd-structures/casmi-chebi-lmsd-structures/bio_structures.parquet"


def main():
    ap = argparse.ArgumentParser()
    for k in ("eval_csv", "fold_safe", "out", "masks"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--only", default=""); ap.add_argument("--gen_dump", required=True); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--workers", type=int, default=12); ap.add_argument("--max_spectra", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--tier", default="data/external/pubchem_tier"); ap.add_argument("--pool", default="data/external/v2_pool/pool_meta.parquet")
    ap.add_argument("--coco", default="data/external/coconut"); ap.add_argument("--v3", default="data/external/v3_models/code")
    a = ap.parse_args(); t0 = time.time(); os.makedirs(a.out, exist_ok=True); MAX_REF, DUP_SIM = BF.MAX_REF, BF.DUP_SIM
    for s_ in a.sets:
        if any(os.path.exists(f"{a.out}/{n_}") for n_ in (f"ewin_{s_}.parquet", f"ewin_molecules_{s_}.csv", f"ewin_refs_{s_}.json", f"ewin_zlog_{s_}.npz")): sys.exit(f"STOP: outputs of {s_} exist in {a.out} (no overwrite)")
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    import torch
    sys.path.insert(0, P_(a.v3))
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    mols = pd.read_csv(P_(a.eval_csv)); mols["molecule"] = mols.molecule.astype(str)
    dtype = fpnet.autocast_dtype("cuda"); model = fpnet.load_model(f"{P_(a.fold_safe)}/fpnet_fold0.pt", "cuda")
    st = P_(a.store); S_MZ = np.load(f"{st}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{st}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{st}/spec_off.npy")
    meta = pl.read_parquet(f"{st}/spec_meta.parquet")
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy(); inst_of_row = meta["instrument_type"].to_numpy()
    key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    def spectrum(row, shift=0.0):
        s, e = int(S_OFF[row]), int(S_OFF[row + 1]); return np.asarray(S_MZ[s:e], np.float64) - shift, np.asarray(S_IT[s:e], np.float64)
    # ---- E stores (mass-sorted)
    tmass = np.load(f"{P_(a.tier)}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{P_(a.tier)}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{P_(a.tier)}/pc_smiles.npy", mmap_mode="r")
    pcl_rows = np.sort(pl.read_parquet(PCLP, columns=["tier_row"]).filter(pl.col("tier_row") >= 0)["tier_row"].unique().to_numpy().astype(np.int64))
    pcl_mass = np.asarray(tmass[pcl_rows], np.float64); o_ = np.argsort(pcl_mass, kind="stable"); pcl_rows, pcl_mass = pcl_rows[o_], pcl_mass[o_]
    def tier_smiles(r):
        o = np.asarray(toff[r:r + 2]).astype(np.int64); return bytes(tbuf[o[0]:o[1]]).decode("ascii")
    pool = pl.read_parquet(P_(a.pool)).select("key", "smiles", "mass", "src", "pid"); po = np.argsort(pool["mass"].to_numpy(), kind="stable")
    pmass = pool["mass"].to_numpy()[po]; psmi = pool["smiles"].to_numpy()[po]; psrc = pool["src"].to_numpy()[po]; ppid = pool["pid"].to_numpy()[po]; pkey = pool["key"].to_numpy()[po]
    key2smiles = dict(zip(pool.filter(pl.col("src").is_in([1, 3]))["key"].to_list(), pool.filter(pl.col("src").is_in([1, 3]))["smiles"].to_list()))
    cmeta = pickle.load(open(f"{P_(a.coco)}/coco_meta.pkl", "rb")); cmass = np.load(f"{P_(a.coco)}/coco_mass.npy"); csmi = np.asarray(cmeta["smiles"])   # our own COCONUT prep file, as b1_features
    bio = pl.read_parquet(BIOP, columns=["smiles", "monoisotopic_mass"]).drop_nulls(); bo = np.argsort(bio["monoisotopic_mass"].to_numpy(), kind="stable")
    bmass = bio["monoisotopic_mass"].to_numpy()[bo]; bsmi = bio["smiles"].to_numpy()[bo]
    print(f"stores: PCL tier rows {len(pcl_rows):,}, pool {pool.height:,}, COCONUT {len(cmass):,}, BIO {len(bmass):,} ({time.time()-t0:.0f}s)", flush=True)
    def alias_keys(smi, raw):
        keys = {raw} if raw else set()
        if not smi: return keys
        try:
            m = Chem.MolFromSmiles(smi); Chem.RemoveStereochemistry(m)
            for t in TAUT.Enumerate(m):
                try: keys.add(Chem.MolToInchiKey(t)[:14])
                except Exception: pass
        except Exception: pass
        return keys
    WM = json.load(open(P_(a.masks)))
    with np.load(P_(a.gen_dump), allow_pickle=False) as G_: GEN_Z = {str(m_): np.asarray(z_, np.float32) for m_, z_ in zip(G_["mol"], G_["zlog"])}
    STRUCT_DROP = set(WM["struct_drop"]); TRAIN_HIDE = set(WM["train_hide"]); C3_OKEYS = set(WM["c3_okeys"]); C1_EXCL = {k_: set(int(x) for x in v_) for k_, v_ in WM["c1_excl"].items()}
    if not set(a.sets) <= set(WM["sets"]): sys.exit(f"STOP: sets {a.sets} not in the world masks {WM['sets']}")
    print(f"world masks: struct-drop {len(STRUCT_DROP):,}, train-hide {len(TRAIN_HIDE):,}, C3 official keys {len(C3_OKEYS)}, C1 keys {len(C1_EXCL)}", flush=True)
    man = dict(eval_csv=sha(P_(a.eval_csv)), fpnet=sha(f"{P_(a.fold_safe)}/fpnet_fold0.pt"), pool=sha(P_(a.pool)), pcl=sha(PCLP), bio=sha(BIOP), script=sha(os.path.abspath(__file__)),
               masks=sha(P_(a.masks)), gen_dump=sha(P_(a.gen_dump)), version="2.1", sets={})
    with Pool(a.workers, initializer=BF._init, initargs=(P_(a.v3), P_(a.fold_safe))) as wp, torch.no_grad():
        for set_name in a.sets:
            ms = mols[mols.set == set_name]
            if a.limit: ms = ms.head(a.limit)
            if a.only: ms = ms[ms.molecule.isin(set(a.only.split(",")))]   # technical sample: score only these queries; the masks stay the full batch's
            rows_out, cand_out, ref_cache = [], [], {}
            zdump = dict(mol=[], zlog=[])
            refs_log = []   # used reference rows of every candidate that is a batch identity (C1 keys or hidden keys): checked by w135_ewin_check.py
            BATCH_KEYS = set(C1_EXCL) | TRAIN_HIDE
            for n_i, r in enumerate(ms.itertuples(index=False)):
                tm0 = time.time(); mid = r.molecule; truth_key = str(r.scorer_key); lib = r.lib; truth_raw = getattr(r, "raw_key", None); shift = ELECTRON if lib == "enveda-180" else 0.0
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
                q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
                if not q: continue
                qspec = []
                for x in q:
                    sh = shift if mode_of_row[x] == "positive" else 0.0; mz, it = spectrum(x, sh); prec = float(prec_of_row[x]) - sh
                    qspec.append(dict(row=x, mz=mz, it=it, prec=prec, adduct=add_of_row[x], mode=mode_of_row[x], ce=float(ce_of_row[x]) if np.isfinite(ce_of_row[x]) else None, clean=clean_peaks(mz, it, prec)))
                query_rows = {s["row"] for s in qspec}
                M_by_add = {}
                for s in qspec: M_by_add.setdefault(s["adduct"], []).append(s["prec"] + ADDUCT_SHIFT[s["adduct"]])
                M_by_add = {k: float(np.median(v)) for k, v in M_by_add.items()}
                src = {}
                def add(s_, m_, **fl):
                    d = src.setdefault(str(s_), dict(train=False, coco=False, pcl=False, bio=False, pid=-1, pkey=None, mass=float(m_)))
                    for k_, v_ in fl.items():
                        if k_ in ("pid", "pkey"):
                            if d[k_] in (-1, None): d[k_] = v_
                        else: d[k_] = d[k_] or v_
                for ad, M in M_by_add.items():
                    tol = M * PPM * 1e-6
                    lo, hi = np.searchsorted(pcl_mass, M - tol, "left"), np.searchsorted(pcl_mass, M + tol, "right")
                    for tr_, m_ in zip(pcl_rows[lo:hi], pcl_mass[lo:hi]): add(tier_smiles(int(tr_)), m_, pcl=True)
                    lo, hi = np.searchsorted(pmass, M - tol, "left"), np.searchsorted(pmass, M + tol, "right")
                    for s_, sr_, pi_, pk_, m_ in zip(psmi[lo:hi], psrc[lo:hi], ppid[lo:hi], pkey[lo:hi], pmass[lo:hi]): add(s_, m_, train=int(sr_) in (1, 3), coco=int(sr_) in (2, 3), pid=int(pi_), pkey=str(pk_))
                    lo, hi = np.searchsorted(cmass, M - tol, "left"), np.searchsorted(cmass, M + tol, "right")
                    for s_, m_ in zip(csmi[lo:hi], cmass[lo:hi]): add(s_, m_, coco=True)
                    lo, hi = np.searchsorted(bmass, M - tol, "left"), np.searchsorted(bmass, M + tol, "right")
                    for s_, m_ in zip(bsmi[lo:hi], bmass[lo:hi]): add(s_, m_, bio=True)
                smiles = list(src)
                zl, wsum = None, 0.0
                for mode in ("positive", "negative"):
                    grp = [s for s in qspec if s["mode"] == mode]
                    if not grp: continue
                    pairs = [(s["mz"], s["it"]) for s in grp]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                    prec = float(np.median([s["prec"] for s in grp])); ces = [s["ce"] for s in grp if s["ce"] is not None]; ad = Counter(s["adduct"] for s in grp).most_common(1)[0][0]
                    pm, pi = fpnet.prep_peaks(mz, it, prec)
                    inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                              n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)], "cuda")
                    with torch.autocast("cuda", dtype=dtype): z = model(*inp)[0].float().mean(0).cpu().numpy().astype(np.float32)
                    zl = z * len(grp) if zl is None else zl + z * len(grp); wsum += len(grp)
                zlog = (zl / wsum).astype(np.float32)
                zdump["mol"].append(str(mid)); zdump["zlog"].append(zlog)   # 156: compared with the B1 world's gen dump (same query semantics)
                zref = GEN_Z.get(str(mid)); zdiff = float(np.abs(zref - zlog).max()) if zref is not None and zref.shape == zlog.shape else float("inf")
                chunks = [smiles[i:i + 400] for i in range(0, len(smiles), 400)]
                res = wp.map(BF._feat, [(c, zlog) for c in chunks]) if chunks else []
                raw_keys = [k for rr in res for k in rr[0]]; fp = np.concatenate([rr[1] for rr in res]) if res else np.zeros(0, np.float32)
                okeys = [k for rr in wp.map(BF._okey, [smiles[i:i + 200] for i in range(0, len(smiles), 200)]) for k in rr] if smiles else []
                rep = {}; n_src_c3 = n_src_hidden = 0
                for i, (rk, ok) in enumerate(zip(raw_keys, okeys)):
                    if rk is None or ok is None: continue
                    d = dict(src[smiles[i]]); pk_ = d["pkey"]; f_ = float(fp[i]) if np.isfinite(fp[i]) else -np.inf
                    # v2.1 (Codex 158): qualify each SOURCE ROW before the merge -- C3 representations leave every source; a hidden (C2 / C3)
                    # identity's representation loses its train membership and leaves when no public source remains; the representative,
                    # f.z and mass are then chosen among the legal representations only
                    if ok in C3_OKEYS or ok in STRUCT_DROP or rk in STRUCT_DROP or (pk_ is not None and pk_ in STRUCT_DROP): n_src_c3 += 1; continue
                    if ok in TRAIN_HIDE or rk in TRAIN_HIDE or (pk_ is not None and pk_ in TRAIN_HIDE):
                        d["train"] = False
                        if not (d["coco"] or d["pcl"] or d["bio"]): n_src_hidden += 1; continue
                    if ok not in rep: rep[ok] = dict(i=i, rks={rk}, fp=f_, **{k_: d[k_] for k_ in ("train", "coco", "pcl", "bio", "pid", "pkey", "mass")})
                    else:
                        p = rep[ok]; p["rks"].add(rk)
                        for k_ in ("train", "coco", "pcl", "bio"): p[k_] = p[k_] or d[k_]
                        if p["pid"] < 0: p["pid"] = d["pid"]; p["pkey"] = d["pkey"]
                        if f_ > p["fp"]: p["fp"] = f_; p["i"] = i; p["mass"] = d["mass"]
                n_raw = len(rep)   # WORLD: C3 structures leave every E source (official key, raw / alias keys, pool key)
                rep = {k_: v_ for k_, v_ in rep.items() if k_ not in C3_OKEYS and k_ not in STRUCT_DROP and not (v_["rks"] & STRUCT_DROP)
                       and (v_["pkey"] is None or v_["pkey"] not in STRUCT_DROP)}
                n_drop = n_raw - len(rep)
                if n_drop: sys.exit(f"STOP: {mid}: {n_drop} merged structures still carried C3 keys after the source-row qualification")
                # WORLD (Codex 156): a structure whose only source was a hidden train membership (C2 / C3 identities) leaves the window --
                # keep a structure only if (train AND not hidden) OR COCONUT OR PCL OR BIO after the masks
                hid0 = lambda k_, v_: bool(v_["rks"] & TRAIN_HIDE) or v_["pkey"] in TRAIN_HIDE or k_ in TRAIN_HIDE
                n_before = len(rep)
                rep = {k_: v_ for k_, v_ in rep.items() if (v_["train"] and not hid0(k_, v_)) or v_["coco"] or v_["pcl"] or v_["bio"]}
                n_drop_trainonly = n_before - len(rep)
                if n_drop_trainonly: sys.exit(f"STOP: {mid}: {n_drop_trainonly} merged structures were hidden train-only after the source-row qualification")
                n_drop, n_drop_trainonly = n_src_c3, n_src_hidden   # ledger: source rows removed by the qualification
                keys = list(rep); n_e = len(keys)
                if n_e == 0:
                    rows_out.append(dict(set=set_name, molecule=mid, wclass=WM["wclass"].get(mid, ""), n_drop_world=n_src_c3, n_drop_trainonly=n_src_hidden, zlog_maxdiff=zdiff, n_query=len(qspec), ce_known=float(np.mean([s["ce"] is not None for s in qspec])), n_e=0, truth_in_ewin=False, lib_max_c1=0.0, lib_max_c2=0.0, seconds=time.time() - tm0)); continue
                aliases = alias_keys(key2smiles.get(truth_key, ""), truth_raw)
                tset = {i for i, k in enumerate(keys) if k == truth_key or (rep[k]["rks"] & aliases) or rep[k]["pkey"] == truth_key}
                fpu = np.array([rep[k]["fp"] for k in keys]); fpu[~np.isfinite(fpu)] = np.nan
                hid = lambda k_: bool(rep[k_]["rks"] & TRAIN_HIDE) or rep[k_]["pkey"] in TRAIN_HIDE or k_ in TRAIN_HIDE
                train_orig = np.array([bool(rep[k]["train"]) and not hid(k) for k in keys]); train_c2 = train_orig.copy()   # WORLD: one view
                cm = np.array([rep[k]["mass"] for k in keys], float); ppm_err = np.min(np.abs(np.array([[(M - m) / m * 1e6 for m in cm] for M in M_by_add.values()])), axis=0)
                L = {v: np.zeros(n_e) for v in ("c1", "c2", "same_c1", "same_c2")}; nref = {v: np.zeros(n_e, int) for v in ("c1", "c2")}
                for ci, k in enumerate(keys):   # library similarity (b1_features rules) for train-structure candidates
                    pk = rep[k]["pkey"]
                    if pk is None or pk not in key_rows or not train_orig[ci]: continue
                    excl = C1_EXCL.get(pk, set()); kept = []   # WORLD: C1 identities lose their selection-library refs and duplicates for every query
                    for x in [int(x) for x in key_rows[pk] if x not in query_rows and int(x) not in excl]:
                        if x not in ref_cache:
                            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                            mz, it = spectrum(x, sh); ref_cache[x] = (clean_peaks(mz, it, float(prec_of_row[x]) - sh), float(prec_of_row[x]) - sh)
                        (rmz, rit), rprec = ref_cache[x]
                        if any(exact_dup(s, rmz, rit, rprec, add_of_row[x]) for s in qspec): continue
                        if any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == mode_of_row[x] and entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= DUP_SIM for s in qspec): continue
                        kept.append(x)
                    refs1 = list(kept)
                    if len(refs1) > MAX_REF:
                        pri = np.array([0 if add_of_row[x] in M_by_add else 1 for x in refs1]); refs1 = [refs1[i] for i in np.argsort(pri, kind="stable")[:MAX_REF]]
                    if refs1 and (pk in BATCH_KEYS or k in BATCH_KEYS or (rep[k]["rks"] & BATCH_KEYS)):   # v2.1: the rows actually used (after MAX_REF)
                        refs_log.append(dict(molecule=mid, official_key=k, pkey=pk, rows=[int(x) for x in refs1]))
                    b1 = s1 = 0.0; n1 = 0
                    for x in refs1:
                        (rmz, rit), rprec = ref_cache[x]; n1 += 1
                        for s in qspec:
                            if s["mode"] != mode_of_row[x]: continue
                            sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); b1 = max(b1, sim); s1 = max(s1, sim if add_of_row[x] == s["adduct"] else 0.0)
                    L["c1"][ci], L["same_c1"][ci], nref["c1"][ci] = b1, s1, n1
                    L["c2"][ci], L["same_c2"][ci], nref["c2"][ci] = b1, s1, n1   # WORLD: the c2 columns equal the world view
                if len(ref_cache) > 300_000: ref_cache.clear()
                fs = np.nan_to_num(fpu, nan=-1e18); order = np.argsort(-fs, kind="stable"); frank = np.empty(n_e, int); frank[order] = np.arange(1, n_e + 1)
                for ci, k in enumerate(keys):
                    d = rep[k]
                    cand_out.append(dict(set=set_name, molecule=mid, official_key=k, smiles=smiles[d["i"]], is_truth=(k == truth_key), fp=float(fpu[ci]) if np.isfinite(fpu[ci]) else None,
                                         fp_rank_e=int(frank[ci]), n_e=n_e, ppm_err=float(ppm_err[ci]), in_train_c1=bool(train_orig[ci]), in_train_c2=bool(train_c2[ci]), in_coconut=bool(d["coco"]),
                                         in_pcl=bool(d["pcl"]), in_bio=bool(d["bio"]), lib_sim_c1=float(L["c1"][ci]), lib_sim_c2=float(L["c2"][ci]), lib_same_c1=float(L["same_c1"][ci]),
                                         lib_same_c2=float(L["same_c2"][ci]), lib_nref_c1=int(nref["c1"][ci]), lib_nref_c2=int(nref["c2"][ci])))
                rows_out.append(dict(set=set_name, molecule=mid, wclass=WM["wclass"].get(mid, ""), n_drop_world=n_drop, n_drop_trainonly=n_drop_trainonly, zlog_maxdiff=zdiff, n_query=len(qspec), ce_known=float(np.mean([s["ce"] is not None for s in qspec])), n_e=n_e, truth_in_ewin=truth_key in rep,
                                     lib_max_c1=float(L["c1"].max()), lib_max_c2=float(L["c2"].max()), seconds=time.time() - tm0))
                if (n_i + 1) % 25 == 0 or n_i == len(ms) - 1:
                    d_ = pd.DataFrame(rows_out); print(f"  {set_name} {n_i+1}/{len(ms)} | E window median {d_.n_e.median():.0f} | {d_.seconds.mean():.1f}s/mol ({time.time()-t0:.0f}s)", flush=True)
            # v2.1 (Codex 158): typed tables (an all-empty set keeps the schema), temporary names renamed at the end, hashes in the manifest
            CAND_COLS = ["set", "molecule", "official_key", "smiles", "is_truth", "fp", "fp_rank_e", "n_e", "ppm_err", "in_train_c1", "in_train_c2", "in_coconut", "in_pcl", "in_bio",
                         "lib_sim_c1", "lib_sim_c2", "lib_same_c1", "lib_same_c2", "lib_nref_c1", "lib_nref_c2"]
            outs = {f"ewin_{set_name}.parquet": lambda f_: pd.DataFrame(cand_out, columns=CAND_COLS).to_parquet(f_, index=False),
                    f"ewin_molecules_{set_name}.csv": lambda f_: pd.DataFrame(rows_out).to_csv(f_, index=False),
                    f"ewin_refs_{set_name}.json": lambda f_: json.dump(refs_log, open(f_, "w")),
                    f"ewin_zlog_{set_name}.npz": lambda f_: np.savez(open(f_, "wb"), mol=np.array(zdump["mol"]), zlog=np.stack(zdump["zlog"]) if zdump["zlog"] else np.zeros((0, 1), np.float32))}
            hashes = {}
            for name, writer in outs.items():
                tmp_ = f"{a.out}/.tmp_{name}"; writer(tmp_); hashes[name] = sha(tmp_)
            for name in outs: os.replace(f"{a.out}/.tmp_{name}", f"{a.out}/{name}")
            man["sets"][set_name] = dict(molecules=len(rows_out), rows=len(cand_out), outputs=hashes); print(f"saved {set_name}: {len(rows_out)} molecules, {len(cand_out)} rows ({time.time()-t0:.0f}s)", flush=True)
    man["seconds"] = round(time.time() - t0); json.dump(man, open(f"{a.out}/ewin_manifest.json", "w"), indent=1); print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
