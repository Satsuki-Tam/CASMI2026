"""B1 pipeline -- label-free MS/MS -> structure identification for a test parquet, end to end, locally or on Kaggle.

Stages (all label-free; see docs/b1_baseline_design.md):
  1. test spectra per molecule (10 adducts, both polarities; electron-mass convention of b1_common)
  2. train spectra store built from train.parquet (library search references) -- in memory on Kaggle, mmap locally
  3. candidates: neutral-mass windows (+-10 ppm per observed adduct) over the PubChem tier + the v2 pool (train structures + COCONUT),
     parsed once in worker processes (raw InChIKey14 + FPNet f.z over the fold-model ensemble), merged on the raw key with provenance
  4. library similarity (spectral entropy, same polarity) for candidates that are train structures
  5. documentation priors (popularity dataset, tier / pool rows)
  6. shortlist = top-K by FP, top-K by z(FP)+0.15 pop, top-20 by library similarity; official scorer keys; duplicates merged
  7. GLACIER / ICEBERG on the shortlists (budgeted; molecules with the weakest library match first)
  8. fusion: S = z(FP) + W_GL z(GL) + W_ICE z(ICE) + LAM pop; library-priority when the best match >= TAU and beats the runner-up by MARGIN
  9. top-25 by official identity -> submission.csv; stage statistics -> b1_run_manifest.json
Usage (local): python -X utf8 b1_pipeline.py --test data/raw/test.parquet --out <dir> [--limit N] [--no_forward]
On Kaggle the paths are resolved under /kaggle/input/** (same datasets as the public E0 kernel) and /kaggle/working.
"""
import os as _os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"): _os.environ.setdefault(_v, "1")   # one BLAS thread per process: 16 workers x 64 OpenBLAS threads made the Spark 30x slower
import argparse, glob, json, os, subprocess, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity  # noqa: E402

KAGGLE = os.path.exists("/kaggle/input")
PPM, K_SHORT, K_LIB, LIB_MIN, MAX_REF, MAX_Q = 10.0, 100, 20, 0.2, 24, 16
W_GL, W_ICE, LAM, TAU, MARGIN = 2.0, 1.0, 0.15, 0.6, 0.1
ICE_BUDGET, GL_BUDGET = 5400, 4000


def find(pattern, root="/kaggle/input"):
    hits = sorted(glob.glob(os.path.join(root, "**", pattern), recursive=True))
    if not hits: raise FileNotFoundError(pattern)
    return hits[0]


def paths(args):
    if KAGGLE:
        def first(*pats):
            for pat in pats:
                try: return find(pat)
                except FileNotFoundError: pass
            raise FileNotFoundError(pats)
        pop = os.path.dirname(first("pc_lsid.npy"))
        tier = os.path.dirname(first("casmi26-pubchem-tier/pc_mass.npy", "pubchem_tier/pc_mass.npy", "pc_mass.npy"))
        return dict(train="/kaggle/input/enveda-CASMI26-molecule-id-mass-spectra/train.parquet", tier=tier, pop=pop,
                    pool=first("casmi26-v2-pool/pool_meta.parquet", "pool_meta.parquet"), fold_safe=os.path.dirname(first("fpnet_fold0.pt")),
                    v3=os.path.dirname(os.path.dirname(first("casmi26-v3-models/code/casmi/fpnet.py", "v3_models/code/casmi/fpnet.py"))),
                    glacier=os.path.dirname(first("gl_runner.py")), iceberg=os.path.dirname(first("ice_runner.py")), work="/kaggle/working", store=None, runner_python=None)
    R = os.environ.get("CASMI_ROOT", r"C:\kaggle\CASMI" if os.name == "nt" else os.path.expanduser("~/CASMI2026"))
    runner_py = f"{R}/.venv-ice/Scripts/python.exe" if os.name == "nt" else f"{R}/.venv-ice/bin/python"
    return dict(train=f"{R}/data/raw/train.parquet", tier=f"{R}/data/external/pubchem_tier", pop=f"{R}/data/external/pubchem_popularity", pool=f"{R}/data/external/v2_pool/pool_meta.parquet",
                fold_safe=f"{R}/data/external/fold_safe_fpnet", v3=f"{R}/data/external/v3_models/code", glacier=f"{R}/data/external/glacier", iceberg=f"{R}/data/external/iceberg",
                work=args.out, store=f"{R}/data/processed/spectra_store", runner_python=runner_py)


# ------------------------------------------------------------------------------------------------------------ workers
def _init(v3, fs):
    global chem_w, bits_w, Chem, TAUT
    sys.path.insert(0, v3)
    from casmi import chem as chem_w
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator(); bits_w = np.load(f"{fs}/fp_bits.npy")


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


def _rawkey(smiles):
    out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s); out.append(Chem.MolToInchiKey(m)[:14] if m is not None else None)
        except Exception:
            out.append(None)
    return out


def _okey(smiles):
    out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s); Chem.RemoveStereochemistry(m); out.append(Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14])
        except Exception:
            out.append(None)
    return out


# ------------------------------------------------------------------------------------------------------------ forward-model site (Kaggle)
def _compatible_rdkit_wheel(pkg):
    """RDKit 2025.3.6 wheel compatible with this interpreter (bundled in the ICEBERG package or attached as a dataset)."""
    from pip._vendor.packaging.tags import sys_tags
    from pip._vendor.packaging.utils import parse_wheel_filename
    compatible = set(sys_tags())
    for path in sorted(glob.glob(os.path.join(pkg, "wheels", "rdkit-2025.3.6-*.whl*"))) + sorted(glob.glob("/kaggle/input/**/rdkit-2025.3.6-*.whl", recursive=True)):
        name = os.path.basename(path).removesuffix(".ice")
        _, version, _, tags = parse_wheel_filename(name)
        if str(version) == "2025.3.6" and compatible.intersection(tags): return path
    raise FileNotFoundError("no compatible RDKit 2025.3.6 wheel for the ICEBERG/GLACIER site")


def preseed_site(pkg, site):
    """install the ICEBERG wheels (+ a compatible RDKit) into `site` with pip --target and write the runner's marker (same procedure as E0)."""
    import shutil
    srcs = sorted(glob.glob(os.path.join(pkg, "wheels", "*.whl.ice")) + glob.glob(os.path.join(pkg, "wheels", "*.whl")))
    keep = [w for w in srcs if not os.path.basename(w).lower().startswith("rdkit")] + [_compatible_rdkit_wheel(pkg)]
    os.makedirs(site, exist_ok=True); wdir = os.path.join(site, ".wheels"); os.makedirs(wdir, exist_ok=True); whl = []
    for w in keep:
        dst = os.path.join(wdir, os.path.basename(w)[:-4] if w.endswith(".ice") else os.path.basename(w)); shutil.copyfile(w, dst); whl.append(dst)
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-index", "--no-deps", "--no-compile", "--disable-pip-version-check", "--upgrade", "--target", site] + whl,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print("[b1] site preseed rc", r.returncode, (r.stdout or "")[-300:], flush=True)
    if r.returncode != 0: raise RuntimeError("site preseed failed: " + (r.stdout or "")[-500:])
    shutil.rmtree(wdir, ignore_errors=True)
    open(os.path.join(site, ".ice_site_ok"), "w").write(chr(10).join(os.path.basename(w) for w in srcs))


# ------------------------------------------------------------------------------------------------------------ data
def load_test(path, limit=0):
    t = pl.read_parquet(path)
    cols = ["molecule_id", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type", "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units"]
    t = t.select([c for c in cols if c in t.columns])
    mols = {}
    for r in t.iter_rows(named=True):
        ce = r.get("collision_energy_ev"); ce = [float(x) for x in ce] if ce is not None and len(ce) else None
        mols.setdefault(str(r["molecule_id"]), []).append(dict(mz=np.asarray(r["ms2_mzs"], np.float64), it=np.asarray(r["ms2_normalized_intensities"], np.float64), prec=float(r["precursor_mz"]),
                                                                 adduct=r["adduct"], mode=r["ionization_mode"], instrument=r.get("instrument_type") or "", ce=float(np.mean(ce)) if ce else None,
                                                                 ce_ev=ce, ce_orig=r.get("collision_energy_orig"), ce_units=r.get("collision_energy_orig_units")))
    ids = list(mols)
    if limit: ids = ids[:limit]
    return {m: mols[m] for m in ids}, t["molecule_id"].unique().to_list()


def build_store(train_parquet, scorer_keys_parquet=None):
    """flat spectra arrays + meta from train.parquet (in memory); returns dict."""
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(train_parquet); mz_parts, it_parts, lens, metas = [], [], [], []
    for b in pf.iter_batches(batch_size=100_000, columns=["inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "collision_energy_ev", "ms2_mzs", "ms2_normalized_intensities"]):
        mz = b.column("ms2_mzs"); it = b.column("ms2_normalized_intensities")
        for cm, ci in zip(mz.chunks if hasattr(mz, "chunks") else [mz], it.chunks if hasattr(it, "chunks") else [it]):
            lens.append(np.diff(np.asarray(cm.offsets)).astype(np.int64)); mz_parts.append(np.asarray(cm.flatten(), np.float32)); it_parts.append(np.asarray(ci.flatten(), np.float32))
        tb = pl.from_arrow(b.select(["inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "collision_energy_ev"]))
        metas.append(tb.with_columns(pl.col("collision_energy_ev").list.mean().alias("ce_mean")).drop("collision_energy_ev"))
    lens = np.concatenate(lens); off = np.zeros(len(lens) + 1, np.int64); np.cumsum(lens, out=off[1:])
    meta = pl.concat(metas).with_row_index("row")
    return dict(mz=np.concatenate(mz_parts), it=np.concatenate(it_parts), off=off, meta=meta)


def load_store(store_dir):
    return dict(mz=np.load(f"{store_dir}/spec_mz.npy", mmap_mode="r"), it=np.load(f"{store_dir}/spec_int.npy", mmap_mode="r"), off=np.load(f"{store_dir}/spec_off.npy"),
                meta=pl.read_parquet(f"{store_dir}/spec_meta.parquet"))


def official_keys_of_train(store, pool):
    """map train structures (inchikey14) -> official scorer key through the pool (pool keys are official; src 1/3 rows carry train_sid) --
    falls back to canonicalising structures absent from the pool."""
    return None


# ------------------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--test", default=None); ap.add_argument("--out", default="experiments/b1_baseline/pipeline_local"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no_forward", action="store_true"); ap.add_argument("--workers", type=int, default=0); ap.add_argument("--folds", default="0")
    args = ap.parse_args(); P = paths(args); os.makedirs(P["work"], exist_ok=True); T0 = time.time(); log = lambda *x: print(f"[b1 {time.time()-T0:7.0f}s]", *x, flush=True)
    test_path = args.test or ("/kaggle/input/enveda-CASMI26-molecule-id-mass-spectra/test.parquet" if KAGGLE else os.path.join(os.path.dirname(P["train"]), "test.parquet"))
    workers = args.workers or max(2, (os.cpu_count() or 4) - 1)
    import torch
    sys.path.insert(0, P["v3"])
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    mols, all_ids = load_test(test_path, args.limit); log(f"test: {len(mols)} molecules of {len(all_ids)}; {sum(len(v) for v in mols.values())} spectra")
    # ---- stores
    store = load_store(P["store"]) if P["store"] and os.path.exists(P["store"]) else build_store(P["train"])
    meta = store["meta"]; S_MZ, S_IT, S_OFF = store["mz"], store["it"], store["off"]
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy(); prec_of_row = meta["precursor_mz"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    log(f"store: {meta.height:,} spectra, {len(ik_rows):,} train structures")
    pool = pl.read_parquet(P["pool"]).select("key", "smiles", "mass", "src", "pid")
    tmass = np.load(f"{P['tier']}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{P['tier']}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{P['tier']}/pc_smiles.npy", mmap_mode="r")
    PC = {n: np.load(f"{P['pop']}/pc_{n}.npy", mmap_mode="r") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    PL = {n: np.load(f"{P['pop']}/pool_{n}.npy") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    assert all(v.shape[0] == tmass.shape[0] for v in PC.values()), 'popularity arrays are not aligned to the tier'
    assert all(v.shape[0] == pool.height for v in PL.values()), 'pool popularity arrays are not aligned to the pool'
    log(f"paths: {json.dumps({k: str(v) for k, v in P.items()})}")
    order = np.argsort(pool["mass"].to_numpy(), kind="stable")
    pmass = pool["mass"].to_numpy()[order]; psmi = pool["smiles"].to_numpy()[order]; psrc = pool["src"].to_numpy()[order]; ppid = pool["pid"].to_numpy()[order]; pkey = pool["key"].to_numpy()[order]
    folds = [int(x) for x in args.folds.split(",")]
    models = [fpnet.load_model(f"{P['fold_safe']}/fpnet_fold{k}.pt", dev) for k in folds]; dtype = fpnet.autocast_dtype(dev)
    log(f"FPNet folds {folds} loaded on {dev}; tier rows {tmass.shape[0]:,}; pool {pool.height:,}")

    def spectrum(row, shift=0.0):
        s, e = int(S_OFF[row]), int(S_OFF[row + 1]); return np.asarray(S_MZ[s:e], np.float64) - shift, np.asarray(S_IT[s:e], np.float64)

    def tier_window(lo_m, hi_m):
        lo = int(np.searchsorted(tmass, lo_m, "left")); hi = int(np.searchsorted(tmass, hi_m, "right"))
        if hi <= lo: return [], np.zeros(0, np.int64), np.zeros(0)
        o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
        return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)], np.arange(lo, hi), np.asarray(tmass[lo:hi], np.float64)

    stats, feats, runner, ref_cache = [], {}, [], {}
    with Pool(workers, initializer=_init, initargs=(P["v3"], P["fold_safe"])) as wp, torch.no_grad():
        # (official key -> reference rows) for train structures: scorer keys from the store meta when available (local), else raw
        # InChIKey14 of the pool's train SMILES computed in the workers and matched to the store's inchikey14
        if "scorer_ik14" in meta.columns:
            key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
        else:
            tr = pool.filter(pl.col("src").is_in([1, 3])); tsmi = tr["smiles"].to_list(); tkey = tr["key"].to_list()
            rk = [k for rr_ in wp.map(_rawkey, [tsmi[i:i + 2000] for i in range(0, len(tsmi), 2000)]) for k in rr_]
            ik_to_key = {ik: key for ik, key in zip(rk, tkey) if ik}
            key_rows = {}
            for ik, rows in ik_rows.items():
                k = ik_to_key.get(ik)
                if k: key_rows.setdefault(k, []).append(rows)
            key_rows = {k: np.concatenate(v) for k, v in key_rows.items()}
        log(f"library index: {len(key_rows):,} official identities with reference spectra")
        for n_i, (mid, spectra) in enumerate(mols.items()):
            tm0 = time.time()
            q = [dict(s, clean=clean_peaks(s["mz"], s["it"], s["prec"])) for s in spectra if s["adduct"] in ADDUCT_SHIFT][:MAX_Q]
            if not q:                                         # unknown adducts only: fall back to [M+H]+ / [M-H]- by polarity
                q = [dict(s, adduct=("[M+H]+" if s["mode"] == "positive" else "[M-H]-"), clean=clean_peaks(s["mz"], s["it"], s["prec"])) for s in spectra][:MAX_Q]
            M_by_add = {}
            for s in q: M_by_add.setdefault(s["adduct"], []).append(s["prec"] + ADDUCT_SHIFT[s["adduct"]])
            M_by_add = {k: float(np.median(v)) for k, v in M_by_add.items()}
            smiles, src_train, src_coco, tier_row, pool_pid, pool_key, cmass = [], [], [], [], [], [], []
            for M in M_by_add.values():
                tol = M * PPM * 1e-6; ts, trows, tms = tier_window(M - tol, M + tol)
                lo = int(np.searchsorted(pmass, M - tol, "left")); hi = int(np.searchsorted(pmass, M + tol, "right"))
                smiles += ts + [str(s) for s in psmi[lo:hi]]; src_train += [False] * len(ts) + [bool(x in (1, 3)) for x in psrc[lo:hi]]
                src_coco += [False] * len(ts) + [bool(x in (2, 3)) for x in psrc[lo:hi]]; tier_row += list(trows) + [-1] * (hi - lo)
                pool_pid += [-1] * len(ts) + [int(x) for x in ppid[lo:hi]]; pool_key += [None] * len(ts) + [str(x) for x in pkey[lo:hi]]; cmass += list(tms) + list(pmass[lo:hi])
            # FPNet logits (polarity groups, fold ensemble)
            zl, wsum = None, 0.0
            for mode in ("positive", "negative"):
                grp = [s for s in q if s["mode"] == mode]
                if not grp: continue
                pairs = [(s["mz"], s["it"]) for s in grp]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                prec = float(np.median([s["prec"] for s in grp])); ces = [s["ce"] for s in grp if s["ce"] is not None]
                ad = Counter(s["adduct"] for s in grp).most_common(1)[0][0]; pm, pi = fpnet.prep_peaks(mz, it, prec)
                inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                          n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)], dev)
                with torch.autocast(dev, dtype=dtype, enabled=(dev == "cuda")):
                    zz = torch.stack([m(*inp)[0].float()[0] for m in models]).mean(0).cpu().numpy().astype(np.float32)
                zl = zz * len(grp) if zl is None else zl + zz * len(grp); wsum += len(grp)
            zlog = (zl / wsum).astype(np.float32)
            chunks = [smiles[i:i + 400] for i in range(0, len(smiles), 400)]
            res = wp.map(_feat, [(c, zlog) for c in chunks]) if chunks else []
            raw_keys = [k for rr_ in res for k in rr_[0]]; fp = np.concatenate([rr_[1] for rr_ in res]) if res else np.zeros(0, np.float32)
            rep = {}
            for i, k in enumerate(raw_keys):
                if k is None: continue
                if k not in rep: rep[k] = dict(i=i, train=src_train[i], coco=src_coco[i], trow=tier_row[i], pid=pool_pid[i], pkey=pool_key[i], mass=cmass[i], fp=float(fp[i]) if np.isfinite(fp[i]) else -np.inf)
                else:
                    p = rep[k]; p["train"] |= src_train[i]; p["coco"] |= src_coco[i]
                    if p["trow"] < 0: p["trow"] = tier_row[i]
                    if p["pid"] < 0: p["pid"] = pool_pid[i]; p["pkey"] = pool_key[i]
                    if np.isfinite(fp[i]) and fp[i] > p["fp"]: p["fp"] = float(fp[i])
            keys = list(rep); n_u = len(keys)
            if n_u == 0:
                stats.append(dict(molecule=mid, n_query=len(q), n_unique=0, seconds=time.time() - tm0)); feats[mid] = []; continue
            fpu = np.array([rep[k]["fp"] for k in keys]); fpu[~np.isfinite(fpu)] = np.nan
            trow = np.array([rep[k]["trow"] for k in keys]); pid = np.array([rep[k]["pid"] for k in keys]); in_train = np.array([rep[k]["train"] for k in keys]); in_coco = np.array([rep[k]["coco"] for k in keys])
            comp = {n: np.zeros(n_u, np.float32) for n in PC}; ht = trow >= 0; hp = (~ht) & (pid >= 0)
            for n in comp:
                if ht.any(): comp[n][ht] = np.asarray(PC[n][np.sort(trow[ht])], dtype=np.float32)[np.argsort(np.argsort(trow[ht]))]
                if hp.any(): comp[n][hp] = np.asarray(PL[n][pid[hp]], dtype=np.float32)
            comp["np"][in_coco] = np.maximum(comp["np"][in_coco], 1.0)
            pop = comp["lsid"] + comp["lpmid"] + 0.5 * comp["lsynonyms"] + 1.0 * (comp["np"] != 0) + 0.5 * ((comp["src_mask"].astype(np.int64) & 1) != 0) + 0.5 * np.log1p(np.maximum(comp["lotus_refs"], 0))
            # library similarity
            lib = np.zeros(n_u); lib_same = np.zeros(n_u); nref = np.zeros(n_u, int)
            for ci, k in enumerate(keys):
                pk = rep[k]["pkey"]
                if not rep[k]["train"] or pk is None or pk not in key_rows: continue
                rrows = key_rows[pk]
                if len(rrows) > MAX_REF:
                    pri = np.array([0 if add_of_row[x] in M_by_add else 1 for x in rrows]); rrows = rrows[np.argsort(pri, kind="stable")][:MAX_REF]
                best = same = 0.0
                for x in rrows:
                    if x not in ref_cache:
                        sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                        mz, it = spectrum(x, sh); ref_cache[x] = clean_peaks(mz, it, float(prec_of_row[x]) - sh)
                    rmz, rit = ref_cache[x]
                    for s in q:
                        if s["mode"] != mode_of_row[x]: continue
                        sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); best = max(best, sim)
                        if add_of_row[x] == s["adduct"]: same = max(same, sim)
                lib[ci], lib_same[ci], nref[ci] = best, same, len(rrows)
            if len(ref_cache) > 200_000: ref_cache.clear()
            # shortlist + official keys
            fpz = np.nan_to_num(fpu, nan=np.nanmin(fpu) if np.isfinite(fpu).any() else 0.0); zf = (fpz - fpz.mean()) / (fpz.std() + 1e-9)
            K = min(K_SHORT, n_u); top_fp = np.argsort(-np.nan_to_num(fpu, nan=-1e18), kind="stable")[:K]; top_fpp = np.argsort(-(zf + LAM * pop), kind="stable")[:K]
            top_lib = [i for i in np.argsort(-lib, kind="stable")[:K_LIB] if lib[i] > LIB_MIN]
            short = np.union1d(np.union1d(top_fp, top_fpp), np.array(top_lib, dtype=np.int64))
            s_smiles = [smiles[rep[keys[i]]["i"]] for i in short]
            okeys = [k for rr_ in wp.map(_okey, [s_smiles[i:i + 25] for i in range(0, len(s_smiles), 25)]) for k in rr_]
            best = {}
            for j, i in enumerate(short):
                if okeys[j] is not None: best.setdefault(okeys[j], []).append(i)
            rows = []
            for ok, idxs in best.items():
                i = max(idxs, key=lambda j: np.nan_to_num(fpu[j], nan=-1e18))
                rows.append(dict(key=ok, smiles=smiles[rep[keys[i]]["i"]], fp=float(fpu[i]) if np.isfinite(fpu[i]) else None, pop=float(pop[i]), lib=float(max(lib[j] for j in idxs)),
                                 lib_same=float(max(lib_same[j] for j in idxs)), in_train=bool(any(in_train[j] for j in idxs))))
            feats[mid] = rows
            runner.append(dict(mid=mid, lib_max=float(lib.max()), spectra=[dict(mz=s["mz"].tolist(), it=s["it"].tolist(), prec=s["prec"], adduct=s["adduct"], mode=s["mode"], instrument=s["instrument"],
                                                                                   ce_ev=s.get("ce_ev"), ce_orig=s.get("ce_orig"), ce_units=s.get("ce_units")) for s in q], cands=[r["smiles"] for r in rows]))
            stats.append(dict(molecule=mid, n_query=len(q), adducts="|".join(sorted(M_by_add)), n_window=len(smiles), n_unique=n_u, n_train=int(in_train.sum()), n_shortlist=len(rows), lib_max=float(lib.max()), seconds=time.time() - tm0))
            if (n_i + 1) % 20 == 0 or n_i == len(mols) - 1:
                d = pd.DataFrame(stats); log(f"{n_i+1}/{len(mols)} | window median {d.n_unique.median():.0f} | shortlist median {d.n_shortlist.median():.0f} | lib_max>=0.6: {int((d.lib_max >= TAU).sum())} | {d.seconds.mean():.1f}s/mol")
    pd.DataFrame(stats).to_csv(f"{P['work']}/b1_stage_stats.csv", index=False)
    # ---- forward models: weakest library match first
    runner.sort(key=lambda it: it["lib_max"]); items = [dict(mid=it["mid"], spectra=it["spectra"], cands=it["cands"]) for it in runner]
    json.dump(items, open(f"{P['work']}/b1_forward_in.json", "w"))
    GL, ICE = {}, {}
    if not args.no_forward and items:
        if KAGGLE:
            sys.path.append(P["iceberg"]); sys.path.append(P["glacier"])
            import fuse as ice_fuse, gl_fuse
            try: preseed_site(P["iceberg"], f"{P['work']}/ice_site")
            except Exception as e: log("site preseed failed (runner will try its own install):", repr(e))
            try: ICE = ice_fuse.run_ice(P["iceberg"], items, workdir=f"{P['work']}/ice_work", device=dev, budget_s=ICE_BUDGET, site=f"{P['work']}/ice_site", extra_args=["--any-rdkit"]); log("ICE done")
            except Exception as e: log("ICE failed:", repr(e))
            try: GL = gl_fuse.run_gl(P["glacier"], items, workdir=f"{P['work']}/gl_work", device=dev, budget_s=GL_BUDGET, site=f"{P['work']}/ice_site", wheels=os.path.join(P["iceberg"], "wheels"), extra_args=["--any-rdkit"]); log("GL done")
            except Exception as e: log("GL failed:", repr(e))
        else:
            for name, pkg, script in (("gl", P["glacier"], "gl_runner.py"), ("ice", P["iceberg"], "ice_runner.py")):
                out = f"{P['work']}/{name}_out.json"
                subprocess.run([P["runner_python"], f"{pkg}/{script}", pkg, f"{P['work']}/b1_forward_in.json", out, "--device", dev, "--site", "none", "--budget", str(GL_BUDGET if name == "gl" else ICE_BUDGET)],
                               stdout=open(f"{P['work']}/{name}.log", "w"), stderr=subprocess.STDOUT)
                try: (GL if name == "gl" else ICE).update(json.load(open(out))); log(f"{name} done")
                except Exception as e: log(f"{name} output missing:", repr(e))
    # ---- fusion + submission
    def z(x):
        x = np.asarray(x, float); ok = np.isfinite(x); out = np.full_like(x, np.nan)
        if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
        elif ok.sum() >= 1: out[ok] = 0.0
        out[~ok] = np.nanmin(out[ok]) if ok.any() else 0.0
        return out
    sub, fused_stats = [], Counter()
    for mid in all_ids:
        rows = feats.get(str(mid), [])
        if not rows: sub.append((mid, "CCO")); fused_stats["empty"] += 1; continue
        fp = np.array([r["fp"] if r["fp"] is not None else np.nan for r in rows]); pop = np.array([r["pop"] for r in rows]); lib = np.array([r["lib"] for r in rows])
        g = np.array([(GL.get(str(mid)) or {}).get(r["smiles"], np.nan) if (GL.get(str(mid)) or {}).get(r["smiles"]) is not None else np.nan for r in rows], float)
        ic = np.array([(ICE.get(str(mid)) or {}).get(r["smiles"], np.nan) if (ICE.get(str(mid)) or {}).get(r["smiles"]) is not None else np.nan for r in rows], float)
        S = z(fp) + LAM * pop
        if np.isfinite(g).sum() >= 2: S = S + W_GL * z(g); fused_stats["gl_used"] += 1
        if np.isfinite(ic).sum() >= 2: S = S + W_ICE * z(ic); fused_stats["ice_used"] += 1
        top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
        if lib.max() >= TAU and lib.max() - second >= MARGIN: S = np.where(lib >= TAU, 100.0 + lib, S); fused_stats["lib_priority"] += 1
        order = np.argsort(-S, kind="stable")
        sub.append((mid, ";".join(rows[i]["smiles"] for i in order[:25])))
    df = pd.DataFrame(sub, columns=["molecule_id", "smiles"]); df.to_csv(f"{P['work']}/submission.csv", index=False)
    json.dump(dict(seconds=round(time.time() - T0), molecules=len(all_ids), scored=len(feats), fusion=dict(fused_stats), gl_mols=len(GL), ice_mols=len(ICE), params=dict(K=K_SHORT, W_GL=W_GL, W_ICE=W_ICE, LAM=LAM, TAU=TAU, MARGIN=MARGIN, folds=folds)),
              open(f"{P['work']}/b1_run_manifest.json", "w"), indent=1)
    log(f"submission written: {df.shape}, fusion {dict(fused_stats)}")


if __name__ == "__main__":
    main()
