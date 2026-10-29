"""W135 world builder (135_decision.md; Codex 135 Q2 (ii)): the B1 candidate feature table of a BATCH under ONE common knowledge environment.
A copy of b1_features.py (windows, FPNet, priors, library, shortlist, official keys, runner input and the generation dump are the same code
paths and constants, imported from b1_features where possible); only the masks differ. Proxy classes come from the batch CSV column
--wclass_col (C1 / C2 / C3) and are applied to EVERY query of the batch (the algorithm never sees a class; the classes only change assets):
  C3 : every key of the identity (raw key, scorer key, all keys of its identity group, tautomer-alias raw keys of its structure, scorer keys
       of its spectra) is removed from every candidate source (PubChem tier, v2 pool, COCONUT store); a window structure whose OFFICIAL key
       is a C3 key is removed too (checked whenever a C3 identity has the window's mass); its train membership and references are gone;
  C2 : the structure stays in the non-train sources; its train membership is hidden and it has no library references for any query;
  C1 : the structure and train membership stay; its references from its own selection library and the exact / suspected duplicates
       (b1_features rule) of its query spectra in other libraries are removed for EVERY query (independent acquisitions stay).
Every other structure keeps its references (with the usual per-query duplicate rule). One view: the c1_* and c2_* columns are written
identical (the world view) so the downstream view code (b1_locked_eval.view_frame 'c2') reads the world. No truth-specific rule is used.
--parity_c2: per-molecule masks exactly as b1_features' C2 view (no batch mask) -- for the parity check against an existing run.
Usage: python -X utf8 b1_world.py --eval_csv BATCH.csv --wclass_col wclass_p30 --store ... --tier ... --pop ... --pool ... --coco ... --fold_safe DIR
       --v3 DIR --folds structures.parquet --out DIR [--k 100 --k_fpp 200 --k_pop 50 --k_pool 0] --sets dF1 [--dump_gen DIR]"""
import os as _os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"): _os.environ.setdefault(_v, "1")
import argparse, json, os, pickle, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "b1_baseline")); sys.path.insert(0, B)
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity, select_queries
import b1_features as BF
from b1_features import PPM, SHORTLIST_LAM, K_LIB, LIB_MIN, heavy_ok, rank_of, sha, exact_dup


def main():
    ap = argparse.ArgumentParser()
    for k in ("eval_csv", "store", "tier", "pop", "pool", "coco", "fold_safe", "v3", "out", "folds"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--wclass_col", default=""); ap.add_argument("--parity_c2", action="store_true")
    ap.add_argument("--k", type=int, default=100); ap.add_argument("--k_fpp", type=int, default=None); ap.add_argument("--k_pool", type=int, default=0); ap.add_argument("--k_pop", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12); ap.add_argument("--max_spectra", type=int, default=8); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dup_sim", type=float, default=BF.DUP_SIM); ap.add_argument("--max_ref", type=int, default=BF.MAX_REF); ap.add_argument("--dump_gen", default="")
    a = ap.parse_args(); t0 = time.time(); os.makedirs(a.out, exist_ok=True)
    if not a.parity_c2 and not a.wclass_col: sys.exit("world mode needs --wclass_col")
    MAX_REF = a.max_ref
    import torch
    sys.path.insert(0, a.v3)
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Descriptors import ExactMolWt
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    mols = pd.read_csv(a.eval_csv); mols["molecule"] = mols.molecule.astype(str)
    dtype = fpnet.autocast_dtype("cuda"); model = fpnet.load_model(f"{a.fold_safe}/fpnet_fold0.pt", "cuda")
    S_MZ = np.load(f"{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy(); inst_of_row = meta["instrument_type"].to_numpy(); skey_of_row = meta["scorer_ik14"].to_numpy()
    key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    print(f"store: {meta.height:,} spectra, {len(key_rows):,} identities ({time.time()-t0:.0f}s)", flush=True)

    def spectrum(row, shift=0.0):
        s, e = int(S_OFF[row]), int(S_OFF[row + 1])
        return np.asarray(S_MZ[s:e], np.float64) - shift, np.asarray(S_IT[s:e], np.float64)

    tmass = np.load(f"{a.tier}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{a.tier}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{a.tier}/pc_smiles.npy", mmap_mode="r")
    PC = {n: np.load(f"{a.pop}/pc_{n}.npy", mmap_mode="r") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    pool = pl.read_parquet(a.pool).select("key", "smiles", "mass", "src", "pid")
    assert (pool["pid"].to_numpy() == np.arange(pool.height)).all()
    PL = {n: np.load(f"{a.pop}/pool_{n}.npy") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    order = np.argsort(pool["mass"].to_numpy(), kind="stable")
    pmass = pool["mass"].to_numpy()[order]; psmi = pool["smiles"].to_numpy()[order]; psrc = pool["src"].to_numpy()[order]; ppid = pool["pid"].to_numpy()[order]; pkey = pool["key"].to_numpy()[order]
    key2smiles = dict(zip(pool.filter(pl.col("src").is_in([1, 3]))["key"].to_list(), pool.filter(pl.col("src").is_in([1, 3]))["smiles"].to_list()))
    cmeta = pickle.load(open(f"{a.coco}/coco_meta.pkl", "rb")); cmass = np.load(f"{a.coco}/coco_mass.npy"); csmi = np.asarray(cmeta["smiles"])   # own file (our COCONUT prep), as b1_features

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

    def official(smi):
        try:
            m = Chem.MolFromSmiles(smi); Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]
        except Exception:
            return None

    def query_spectra(mid, lib):
        shift = ELECTRON if lib == "enveda-180" else 0.0
        qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        out = []
        for x in q:
            sh = shift if mode_of_row[x] == "positive" else 0.0
            mz, it = spectrum(x, sh); prec = float(prec_of_row[x]) - sh
            out.append(dict(row=x, mz=mz, it=it, prec=prec, adduct=add_of_row[x], mode=mode_of_row[x], instrument=inst_of_row[x] or "", ce=float(ce_of_row[x]) if np.isfinite(ce_of_row[x]) else None,
                            clean=clean_peaks(mz, it, prec)))
        return out

    # ---- the world: batch-level masks (built once, applied to every query)
    st = pl.read_parquet(a.folds).select("inchikey14", "scorer_key", "identity_group", "smiles")
    G_ALL = {}
    for ik, sk, g in st.select("inchikey14", "scorer_key", "identity_group").iter_rows():
        if g is None: continue
        G_ALL.setdefault(g, set()).update(x for x in (ik, sk) if x)
    G_SK = {}
    for sk, g in st.select("scorer_key", "identity_group").iter_rows():
        if g is not None and sk: G_SK.setdefault(g, set()).add(sk)
    IK_SMI = dict(zip(st["inchikey14"].to_list(), st["smiles"].to_list()))
    STRUCT_DROP, TRAIN_HIDE, C3_OKEYS, C3_MASS, C1_EXCL, WCLASS = set(), set(), set(), [], {}, {}
    mask_stats = dict(C1=0, C2=0, C3=0, c1_rows_excluded_lib=0, c1_rows_excluded_dup=0)
    if not a.parity_c2:
        for r in mols[mols.set.isin(a.sets)].itertuples(index=False):
            mid, tk, g, cls, lib = str(r.molecule), str(r.scorer_key), int(r.identity_group), str(getattr(r, a.wclass_col)), str(r.lib)
            assert cls in ("C1", "C2", "C3"), (mid, cls); WCLASS[mid] = cls; mask_stats[cls] += 1
            smi = IK_SMI.get(mid) or key2smiles.get(tk) or ""
            ids = {mid, tk} | G_ALL.get(g, set()) | alias_keys(smi, mid) | {skey_of_row[x] for x in ik_rows.get(mid, []) if skey_of_row[x] is not None}
            if cls == "C3":
                STRUCT_DROP |= ids; TRAIN_HIDE |= ids; C3_OKEYS |= {tk} | G_SK.get(g, set())
                try: C3_MASS.append(ExactMolWt(Chem.MolFromSmiles(smi)))
                except Exception: C3_MASS.append(np.nan)
            elif cls == "C2":
                TRAIN_HIDE |= ids
            else:   # C1: own-library references and duplicates of its query spectra removed for every query
                qs = query_spectra(mid, lib); ex = set()
                for k in {tk} | G_SK.get(g, set()):
                    for x in key_rows.get(k, []):
                        x = int(x)
                        if lib_of_row[x] == lib: ex.add(x); mask_stats["c1_rows_excluded_lib"] += 1; continue
                        sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                        mz, it = spectrum(x, sh); rprec = float(prec_of_row[x]) - sh; rmz, rit = clean_peaks(mz, it, rprec)
                        dup = any(exact_dup(s, rmz, rit, rprec, add_of_row[x]) for s in qs) or any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == mode_of_row[x] and
                                                                                               entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= a.dup_sim for s in qs)
                        if dup: ex.add(x); mask_stats["c1_rows_excluded_dup"] += 1
                    C1_EXCL[k] = C1_EXCL.get(k, set()) | ex
        C3_MASS = np.array([m for m in C3_MASS if np.isfinite(m)])
        C1_LIB = {str(r.molecule): (str(r.scorer_key), str(r.lib), sorted(G_SK.get(int(r.identity_group), set()) | {str(r.scorer_key)})) for r in mols[mols.set.isin(a.sets)].itertuples(index=False) if WCLASS.get(str(r.molecule)) == "C1"}
        json.dump(dict(wclass_col=a.wclass_col, sets=a.sets, wclass=WCLASS, struct_drop=sorted(STRUCT_DROP), train_hide=sorted(TRAIN_HIDE), c3_okeys=sorted(C3_OKEYS),
                       c1_excl={k: sorted(int(x) for x in v) for k, v in C1_EXCL.items()}, c1_lib=C1_LIB, mask_stats=mask_stats), open(f"{a.out}/world_masks.json", "w"))   # read by w135_p.py (one source of truth)
        print(f"world {a.wclass_col}: {mask_stats}; struct-drop keys {len(STRUCT_DROP):,}, train-hide keys {len(TRAIN_HIDE):,}, C3 official keys {len(C3_OKEYS):,} ({time.time()-t0:.0f}s)", flush=True)

    with Pool(a.workers, initializer=BF._init, initargs=(a.v3, a.fold_safe)) as wp, torch.no_grad():
        for set_name in a.sets:
            ms = mols[mols.set == set_name]
            if a.limit: ms = ms.head(a.limit)
            rows_out, cand_out, runner, ref_cache = [], [], [], {}
            gen_dump = dict(mol=[], zlog=[], masses=[], wkeys=[])
            for n_i, r in enumerate(ms.itertuples(index=False)):
                tm0 = time.time(); mid = r.molecule; truth_key = str(r.scorer_key); lib = r.lib; truth_raw = getattr(r, "raw_key", None)
                qspec = query_spectra(mid, lib)
                if not qspec: print("skip", mid, "no query spectra"); continue
                query_rows = {s["row"] for s in qspec}
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
                        d["train"] |= int(sr_) in (1, 3); d["coco"] |= int(sr_) in (2, 3); d["psrc"] = d.get("psrc", 0) | int(sr_)
                        if d["pid"] < 0: d["pid"] = int(pi_); d["pkey"] = str(pk_)
                    clo = int(np.searchsorted(cmass, M - tol, "left")); chi = int(np.searchsorted(cmass, M + tol, "right"))
                    for s_, m_ in zip(csmi[clo:chi], cmass[clo:chi]):
                        d = src.setdefault(str(s_), dict(tier=False, train=False, coco=False, trow=-1, pid=-1, pkey=None, mass=float(m_))); d["coco"] = True
                smiles = list(src)
                zl, wsum = None, 0.0
                for mode in ("positive", "negative"):
                    grp = [s for s in qspec if s["mode"] == mode]
                    if not grp: continue
                    pairs = [(s["mz"], s["it"]) for s in grp]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                    prec = float(np.median([s["prec"] for s in grp])); ces = [s["ce"] for s in grp if s["ce"] is not None]
                    ad = Counter(s["adduct"] for s in grp).most_common(1)[0][0]
                    pm, pi = fpnet.prep_peaks(mz, it, prec)
                    items_ = [dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                   n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)]
                    inp = fpnet.collate(items_, "cuda")
                    with torch.autocast("cuda", dtype=dtype):
                        z = model(*inp)[0].float().mean(0).cpu().numpy().astype(np.float32)
                    zl = z * len(grp) if zl is None else zl + z * len(grp); wsum += len(grp)
                zlog = (zl / wsum).astype(np.float32)
                chunks = [smiles[i:i + 400] for i in range(0, len(smiles), 400)]
                res = wp.map(BF._feat, [(c, zlog) for c in chunks]) if chunks else []
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
                # ---- WORLD: C3 structures leave every source (raw / pool key, then official key when a C3 identity has this window's mass)
                n_drop_raw = n_drop_ok = 0
                if not a.parity_c2:
                    keep = {k: v for k, v in rep.items() if k not in STRUCT_DROP and (v["pkey"] is None or v["pkey"] not in STRUCT_DROP)}; n_drop_raw = len(rep) - len(keep); rep = keep
                    if len(C3_MASS) and any(np.any(np.abs(C3_MASS - M) <= max(0.002, M * PPM * 1e-6) + 0.01) for M in M_by_add.values()):
                        ks_ = list(rep); sm_ = [smiles[rep[k]["i"]] for k in ks_]
                        oks = dict(zip(ks_, [k for rr in wp.map(BF._okey, [sm_[i:i + 200] for i in range(0, len(sm_), 200)]) for k in rr]))
                        keep = {k: v for k, v in rep.items() if oks[k] not in C3_OKEYS}; n_drop_ok = len(rep) - len(keep); rep = keep
                keys = list(rep); n_u = len(keys)
                if a.dump_gen:
                    gen_dump["mol"].append(str(mid)); gen_dump["zlog"].append(zlog); gen_dump["masses"].append(json.dumps(M_by_add)); gen_dump["wkeys"].append(keys)
                if n_u == 0:
                    rows_out.append(dict(set=set_name, molecule=mid, group=r.group, lib=lib, identity_group=int(getattr(r, "identity_group", -1)), wclass=WCLASS.get(mid, ""), n_query=len(qspec), n_unique=0,
                                         truth_in_window=False, truth_in_shortlist=False, n_drop_raw=n_drop_raw, n_drop_official=n_drop_ok)); continue
                fpu = np.array([rep[k]["fp"] for k in keys]); fpu[~np.isfinite(fpu)] = np.nan
                trow = np.array([rep[k]["trow"] for k in keys]); pid = np.array([rep[k]["pid"] for k in keys])
                in_train = np.array([rep[k]["train"] for k in keys]); in_coco = np.array([rep[k]["coco"] for k in keys]); in_tier = np.array([rep[k]["tier"] for k in keys])
                cm = np.array([rep[k]["mass"] for k in keys], float)
                ppm_err = np.min(np.abs(np.array([[(M - m) / m * 1e6 for m in cm] for M in M_by_add.values()])), axis=0)
                aliases = alias_keys(key2smiles.get(truth_key, ""), truth_raw)
                truth_idx = [i for i, k in enumerate(keys) if k in aliases or rep[k]["pkey"] == truth_key]
                truth_in_window = bool(truth_idx)
                if a.parity_c2:   # b1_features: the truth's train membership hidden in C2; the original flag drives the library channel
                    train_flag_orig = in_train.copy()
                    for i in truth_idx: in_train[i] = False
                else:             # world: C2 / C3 identities are not train structures for anybody (no references either)
                    hid = np.array([(k in TRAIN_HIDE) or (rep[k]["pkey"] is not None and rep[k]["pkey"] in TRAIN_HIDE) for k in keys], bool)
                    in_train = in_train & ~hid; train_flag_orig = in_train.copy()
                comp = {n: np.zeros(n_u, np.float32) for n in PC}
                ht = trow >= 0; hp = (~ht) & (pid >= 0)
                for n in comp:
                    if ht.any(): comp[n][ht] = np.asarray(PC[n][np.sort(trow[ht])], dtype=np.float32)[np.argsort(np.argsort(trow[ht]))]
                    if hp.any(): comp[n][hp] = np.asarray(PL[n][pid[hp]], dtype=np.float32)
                comp["np"][(~ht) & (~hp)] = 1.0; comp["np"][in_coco] = np.maximum(comp["np"][in_coco], 1.0)
                pop = comp["lsid"] + comp["lpmid"] + 0.5 * comp["lsynonyms"] + 1.0 * (comp["np"] != 0) + 0.5 * ((comp["src_mask"].astype(np.int64) & 1) != 0) + 0.5 * np.log1p(np.maximum(comp["lotus_refs"], 0))
                L = {v: np.zeros(n_u) for v in ("c1", "c2", "c1_keepdup", "c2_keepdup", "same_c1", "same_c2")}; nref = {v: np.zeros(n_u, int) for v in ("c1", "c2")}; nsame = {v: np.zeros(n_u, int) for v in ("c1", "c2")}
                truth_set = set(truth_idx)
                for ci, k in enumerate(keys):
                    pk = rep[k]["pkey"]
                    if pk is None or pk not in key_rows or not train_flag_orig[ci]: continue
                    is_truth_cand = ((pk == truth_key) or (ci in truth_set)) if a.parity_c2 else False   # world: no truth-specific rule
                    excl = C1_EXCL.get(pk, ())
                    rrows = [int(x) for x in key_rows[pk] if x not in query_rows and int(x) not in excl]
                    kept, kept_susp = [], []
                    for x in rrows:
                        if x not in ref_cache:
                            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                            mz, it = spectrum(x, sh); ref_cache[x] = (clean_peaks(mz, it, float(prec_of_row[x]) - sh), float(prec_of_row[x]) - sh)
                        (rmz, rit), rprec = ref_cache[x]
                        if any(exact_dup(s, rmz, rit, rprec, add_of_row[x]) for s in qspec): continue
                        susp = any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == mode_of_row[x] and entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= a.dup_sim for s in qspec)
                        if susp: kept_susp.append(x)
                        else: kept.append(x)

                    def cap(rows_):
                        if len(rows_) > MAX_REF:
                            pri = np.array([0 if add_of_row[x] in M_by_add else 1 for x in rows_]); rows_ = [rows_[i] for i in np.argsort(pri, kind="stable")[:MAX_REF]]
                        return rows_
                    for tag, pool_ in (("", kept), ("_keepdup", kept + kept_susp)):
                        refs1 = cap([x for x in pool_ if not (is_truth_cand and lib_of_row[x] == lib)])
                        b1 = s1 = 0.0; n1 = ns1 = 0
                        for x in refs1:
                            (rmz, rit), rprec = ref_cache[x]
                            n1 += 1; sa = add_of_row[x] in M_by_add; ns1 += int(sa)
                            for s in qspec:
                                if s["mode"] != mode_of_row[x]: continue
                                sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); same = add_of_row[x] == s["adduct"]
                                b1 = max(b1, sim); s1 = max(s1, sim if same else 0.0)
                        b2, s2, n2, ns2 = (0.0, 0.0, 0, 0) if is_truth_cand else (b1, s1, n1, ns1)
                        if not a.parity_c2: b1, s1, n1, ns1 = b2, s2, n2, ns2   # one world view
                        L["c1" + tag][ci], L["c2" + tag][ci] = b1, b2
                        if tag == "": L["same_c1"][ci], L["same_c2"][ci] = s1, s2; nref["c1"][ci], nref["c2"][ci] = n1, n2; nsame["c1"][ci], nsame["c2"][ci] = ns1, ns2
                if len(ref_cache) > 300_000: ref_cache.clear()
                fpz = np.nan_to_num(fpu, nan=np.nanmin(fpu) if np.isfinite(fpu).any() else 0.0); zf = (fpz - fpz.mean()) / (fpz.std() + 1e-9)
                K = min(a.k, n_u); K2 = min(a.k_fpp if a.k_fpp else a.k, n_u)
                top_fp = set(np.argsort(-np.nan_to_num(fpu, nan=-1e18), kind="stable")[:K].tolist()); top_fpp = set(np.argsort(-(zf + SHORTLIST_LAM * pop), kind="stable")[:K2].tolist())
                top_lib = {v: {int(i) for i in np.argsort(-L[v], kind="stable")[:K_LIB] if L[v][i] > LIB_MIN} for v in ("c1", "c2")}
                top_pop = set(np.argsort(-(pop + 1e-6 * zf), kind="stable")[:min(a.k_pop, n_u)].tolist()) if a.k_pop > 0 else set()
                psrc_a = np.array([int(rep[k].get("psrc", 0)) for k in keys], dtype=np.int64)
                truth_mask = np.zeros(n_u, bool); truth_mask[list(truth_idx)] = True
                pool_elig = {"c1": pid >= 0, "c2": (pid >= 0) & ~(truth_mask & (psrc_a != 0) & ((psrc_a & ~1) == 0))} if a.parity_c2 else {"c1": pid >= 0, "c2": (pid >= 0) & in_train | (pid >= 0) & ((psrc_a & ~1) != 0)}
                def _top_pool_v(v, k_):
                    m_ = pool_elig[v]
                    return set(np.argsort(-np.where(m_, np.nan_to_num(fpu, nan=-1e18), -np.inf), kind="stable")[:min(k_, int(m_.sum()))].tolist()) if (k_ > 0 and m_.any()) else set()
                short_v = {v: top_fp | top_fpp | top_lib[v] | top_pop | _top_pool_v(v, a.k_pool) for v in ("c1", "c2")}
                if not a.parity_c2: short_v["c1"] = short_v["c2"]
                short = sorted(short_v["c1"] | short_v["c2"])
                s_smiles = [smiles[rep[keys[i]]["i"]] for i in short]
                okeys = [k for rr in wp.map(BF._okey, [s_smiles[i:i + 25] for i in range(0, len(s_smiles), 25)]) for k in rr]
                if not a.parity_c2:
                    bad = [okeys[j] for j in range(len(short)) if okeys[j] in C3_OKEYS]
                    if bad: raise RuntimeError(f"{mid}: C3 official key in the world shortlist after the mask: {bad[:3]}")
                best = {}
                for j, i in enumerate(short):
                    if okeys[j] is not None: best.setdefault(okeys[j], []).append(i)
                for ok, idxs in best.items():
                    i = max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18)); is_t = (ok == truth_key); si = set(idxs)
                    iv = {"c1": idxs, "c2": idxs}
                    cand_out.append(dict(set=set_name, molecule=mid, smiles=smiles[rep[keys[i]]["i"]], official_key=ok, is_truth=is_t,
                                         in_short_c1=bool(si & short_v["c1"]), in_short_c2=bool(si & short_v["c2"]),
                                         in_tier=bool(any(in_tier[j] for j in idxs)), in_coconut=bool(any(in_coco[j] for j in idxs)),
                                         in_train_c1=bool(any(train_flag_orig[j] for j in iv['c1'])), in_train_c2=bool(any(in_train[j] for j in iv['c2'])),
                                         fp=float(fpu[i]) if np.isfinite(fpu[i]) else None, fp_rank_window=rank_of(fpu, i), ppm_err=float(np.nanmin([ppm_err[j] for j in idxs])),
                                         lib_sim_c1=float(max(L["c1"][j] for j in iv["c1"])), lib_sim_c2=float(max(L["c2"][j] for j in iv["c2"])),
                                         lib_sim_c1_keepdup=float(max(L["c1_keepdup"][j] for j in iv["c1"])), lib_sim_c2_keepdup=float(max(L["c2_keepdup"][j] for j in iv["c2"])),
                                         lib_same_c1=float(max(L["same_c1"][j] for j in iv["c1"])), lib_same_c2=float(max(L["same_c2"][j] for j in iv["c2"])),
                                         lib_nref_c1=int(max(nref["c1"][j] for j in iv["c1"])), lib_nref_c2=int(max(nref["c2"][j] for j in iv["c2"])),
                                         lib_nsame_c1=int(max(nsame["c1"][j] for j in iv["c1"])), lib_nsame_c2=int(max(nsame["c2"][j] for j in iv["c2"])),
                                         in_top_fp=bool(si & top_fp), in_top_fpprior=bool(si & top_fpp), in_top_pop=bool(si & top_pop), in_top_lib_c1=bool(si & top_lib["c1"]), in_top_lib_c2=bool(si & top_lib["c2"]),
                                         **{n: float(comp[n][i]) for n in comp}, pop_public=float(pop[i])))
                rspec = [dict(mz=s["mz"].tolist(), it=s["it"].tolist(), prec=s["prec"], adduct=s["adduct"], mode=s["mode"], instrument=s["instrument"],
                              ce_ev=[s["ce"]] if s["ce"] is not None else None, ce_orig=None, ce_units="eV" if s["ce"] is not None else None) for s in qspec]
                runner.append(dict(mid=mid, spectra=rspec,
                                   cands=[s_ for s_ in (smiles[rep[keys[max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18))]]["i"]] for idxs in best.values()) if heavy_ok(s_)]))
                tb = best.get(truth_key, [])
                rows_out.append(dict(set=set_name, molecule=mid, group=r.group, lib=lib, identity_group=int(getattr(r, "identity_group", -1)), wclass=WCLASS.get(mid, ""), n_query=len(qspec),
                                     adducts="|".join(sorted(M_by_add)), n_adducts=len(M_by_add), ce_known=float(np.mean([s["ce"] is not None for s in qspec])), n_window_structures=len(smiles), n_unique=n_u,
                                     n_unique_train=int(train_flag_orig.sum()), truth_in_window=truth_in_window, truth_in_shortlist=bool(tb), truth_in_short_c1=bool(set(tb) & short_v["c1"]),
                                     truth_in_short_c2=bool(set(tb) & short_v["c2"]), n_shortlist=len(best), n_short_c1=len(short_v["c1"]), n_short_c2=len(short_v["c2"]),
                                     lib_max_c1=float(L["c1"].max()), lib_max_c2=float(L["c2"].max()), c1_usable=bool(WCLASS.get(mid) == "C1") if not a.parity_c2 else False,
                                     n_drop_raw=n_drop_raw, n_drop_official=n_drop_ok, seconds=time.time() - tm0))
                if (n_i + 1) % 20 == 0 or n_i == len(ms) - 1:
                    d = pd.DataFrame(rows_out)
                    print(f"  {set_name} {n_i+1}/{len(ms)} | window unique median {d.n_unique.median():.0f} | truth in shortlist {int(d.truth_in_shortlist.sum())} | dropped raw {int(d.n_drop_raw.sum())} "
                          f"official {int(d.n_drop_official.sum())} | {d.seconds.mean():.1f}s/mol ({time.time()-t0:.0f}s)", flush=True)
            pd.DataFrame(rows_out).to_csv(f"{a.out}/b1_molecules_{set_name}.csv", index=False)
            pd.DataFrame(cand_out).to_parquet(f"{a.out}/b1_features_{set_name}.parquet", index=False)
            json.dump(runner, open(f"{a.out}/b1_runner_{set_name}_in.json", "w"))
            if a.dump_gen and gen_dump["mol"]:
                os.makedirs(a.dump_gen, exist_ok=True)
                np.savez_compressed(f"{a.dump_gen}/gen_{set_name}.npz", mol=np.array(gen_dump["mol"]), zlog=np.stack(gen_dump["zlog"]).astype(np.float32), masses=np.array(gen_dump["masses"]))
                pd.DataFrame([(m_, k_) for m_, ks_ in zip(gen_dump["mol"], gen_dump["wkeys"]) for k_ in ks_], columns=["molecule", "key"]).to_parquet(f"{a.dump_gen}/gen_{set_name}_window.parquet", index=False)
            print(f"saved {set_name}: {len(rows_out)} molecules, {len(cand_out)} shortlist rows ({time.time()-t0:.0f}s)", flush=True)
    import rdkit
    json.dump(dict(mode=("parity_c2" if a.parity_c2 else "world"), wclass_col=a.wclass_col, mask_stats=mask_stats, k=a.k, k_fpp=a.k_fpp, k_pop=a.k_pop, k_pool=a.k_pool, shortlist_lam=SHORTLIST_LAM, ppm=PPM,
                   max_spectra=a.max_spectra, max_ref=MAX_REF, dup_sim=a.dup_sim, fpnet=sha(f"{a.fold_safe}/fpnet_fold0.pt"), pool=sha(a.pool), eval_csv=sha(a.eval_csv), script=sha(os.path.abspath(__file__)),
                   b1_features=sha(os.path.join(B, "b1_features.py")), rdkit=rdkit.__version__, seconds=round(time.time() - t0)), open(f"{a.out}/b1_features_manifest.json", "w"), indent=1)
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
