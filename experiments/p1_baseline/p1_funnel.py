"""P1 step 2 -- label-free candidate funnel on the frozen P1 molecules (class-2 proxy, [M+H]+), fixed fold-0 FPNet.

Per molecule (no formula, no forced truth):
  window    : all structures within +-10 ppm of the measured neutral mass in the PubChem tier, the public v2 pool (train structures =
              src 1/3, COCONUT = src 2/3) and the prvsiyan COCONUT set; parsed once, raw InChIKey14 + fold-0 FPNet score f.z computed
              for every structure in worker processes; duplicates merged on the raw key with provenance OR-ed
              (in_tier / in_train / in_coconut) and the tier row / pool row kept for the documentation priors.
  class-2 masking: the truth's own train-structure membership is hidden (in_train = False), everything else is left as is.
  priors    : per-candidate documentation components from the public popularity dataset aligned to the tier rows (pc_*.npy) or the
              pool rows (pool_*.npy): log1p SID, log1p PMID, log1p synonyms, NP membership, depositor-source bit, LOTUS refs.
              COCONUT-only candidates (no tier/pool row) get zeros with NP membership = 1.
  shortlist : union of the top-K by FPNet and the top-K by z(FP) + 0.15 * pop_public (the public pipeline's lambda); official scorer
              keys are computed for the shortlist, duplicates merged (max FP, provenance OR-ed); the truth is identified by official key.
  outputs   : <out>/p1_funnel_<set>.csv (per molecule), <out>/p1_shortlist_<set>.parquet (per shortlist candidate),
              <out>/p1_runner_<set>_in.json (GLACIER / ICEBERG runner input: mid, spectra, cands), <out>/p1_funnel_manifest.json
Usage: python -X utf8 p1_funnel.py --run DIR --tier DIR --pop DIR --pool pool_meta.parquet --coco DIR --fold_safe DIR --v3 DIR
                                   [--k 100] [--workers 10] [--sets A_timstof B_nplib] [--limit N]
"""
import argparse, hashlib, json, os, pickle, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl

PROTON, PPM, LAM_PUBLIC = 1.007276, 10.0, 0.15


def _init(v3, fs):
    global chem_w, bits_w, Chem, TAUT
    sys.path.insert(0, v3)
    from casmi import chem as chem_w
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    bits_w = np.load(f"{fs}/fp_bits.npy")


def _feat(args):
    """worker: raw InChIKey14 + f.z score for a chunk of SMILES."""
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
    """worst-case-tie rank of element idx under descending scores (nan = -inf)."""
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    return int(np.sum(s >= s[idx])) if idx is not None and idx >= 0 else None


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""): h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ("run", "tier", "pop", "pool", "coco", "fold_safe", "v3"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--k", type=int, default=100); ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); t0 = time.time()
    import torch
    sys.path.insert(0, a.v3)
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    items = json.load(open(f"{a.run}/p1_items.json"))
    dtype = fpnet.autocast_dtype("cuda"); model = fpnet.load_model(f"{a.fold_safe}/fpnet_fold0.pt", "cuda")
    tmass = np.load(f"{a.tier}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{a.tier}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{a.tier}/pc_smiles.npy", mmap_mode="r")
    PC = {n: np.load(f"{a.pop}/pc_{n}.npy", mmap_mode="r") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    for n, arr in PC.items(): assert arr.shape[0] == tmass.shape[0], (n, arr.shape)
    pool = pl.read_parquet(a.pool).select("key", "smiles", "mass", "src", "pid")
    assert (pool["pid"].to_numpy() == np.arange(pool.height)).all(), "pool pid is not the row index"
    PL = {n: np.load(f"{a.pop}/pool_{n}.npy") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
    for n, arr in PL.items(): assert arr.shape[0] == pool.height, (n, arr.shape)
    order = np.argsort(pool["mass"].to_numpy(), kind="stable")
    pmass = pool["mass"].to_numpy()[order]; psmi = pool["smiles"].to_numpy()[order]; psrc = pool["src"].to_numpy()[order]; ppid = pool["pid"].to_numpy()[order]
    cmeta = pickle.load(open(f"{a.coco}/coco_meta.pkl", "rb")); cmass = np.load(f"{a.coco}/coco_mass.npy"); csmi = np.asarray(cmeta["smiles"])

    def tier_window(lo_m, hi_m):
        lo = int(np.searchsorted(tmass, lo_m, "left")); hi = int(np.searchsorted(tmass, hi_m, "right"))
        if hi <= lo: return [], np.zeros(0, np.int64)
        o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
        return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)], np.arange(lo, hi)

    os.makedirs(a.run, exist_ok=True)
    with Pool(a.workers, initializer=_init, initargs=(a.v3, a.fold_safe)) as wp, torch.no_grad():
        for set_name in a.sets:
            its = [it for it in items if it["set"] == set_name]
            if a.limit: its = its[: a.limit]
            rows, cand_rows, runner = [], [], []
            for n_i, it in enumerate(its):
                tm0 = time.time(); mid = it["mid"]; spectra = it["spectra"]; neutral = float(it["neutral_mass"]); tol = neutral * PPM * 1e-6
                # ---- sources
                t_smis, t_rows = tier_window(neutral - tol, neutral + tol)
                lo = int(np.searchsorted(pmass, neutral - tol, "left")); hi = int(np.searchsorted(pmass, neutral + tol, "right"))
                p_smis = [str(s) for s in psmi[lo:hi]]; p_src = psrc[lo:hi]; p_pid = ppid[lo:hi]
                clo = int(np.searchsorted(cmass, neutral - tol, "left")); chi = int(np.searchsorted(cmass, neutral + tol, "right"))
                c_smis = [str(s) for s in csmi[clo:chi]]
                smiles = t_smis + p_smis + c_smis
                src_tier = np.r_[np.ones(len(t_smis), bool), np.zeros(len(p_smis) + len(c_smis), bool)]
                src_train = np.r_[np.zeros(len(t_smis), bool), np.isin(p_src, [1, 3]), np.zeros(len(c_smis), bool)]
                src_coco = np.r_[np.zeros(len(t_smis), bool), np.isin(p_src, [2, 3]), np.ones(len(c_smis), bool)]
                tier_row = np.r_[t_rows, -np.ones(len(p_smis) + len(c_smis), np.int64)]
                pool_pid = np.r_[-np.ones(len(t_smis), np.int64), p_pid.astype(np.int64), -np.ones(len(c_smis), np.int64)]
                # ---- FPNet logits (fold 0, merged spectra, eval_ckpt protocol)
                pairs = [(np.asarray(s["mz"], float), np.asarray(s["it"], float)) for s in spectra]
                mz, inten = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                prec = float(np.median([s["prec"] for s in spectra]))
                ces = [float(np.mean(s["ce_ev"])) for s in spectra if s.get("ce_ev")]
                nm = int(sum(max(1, len(s["ce_ev"] or [])) for s in spectra))
                pm, pi = fpnet.prep_peaks(mz, inten, prec)
                inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index("[M+H]+"), ce=float(np.mean(ces)) if ces else 0.0,
                                          ce_known=1.0 if ces else 0.0, n_merged=min(nm, 8), mode=1.0)], "cuda")
                with torch.autocast("cuda", dtype=dtype):
                    zlog = model(*inp)[0].float()[0].cpu().numpy().astype(np.float32)
                # ---- raw keys + FP scores for every structure
                chunks = [smiles[i:i + 400] for i in range(0, len(smiles), 400)]
                res = wp.map(_feat, [(c, zlog) for c in chunks]) if chunks else []
                raw_keys = [k for r in res for k in r[0]]; fp = np.concatenate([r[1] for r in res]) if res else np.zeros(0, np.float32)
                # ---- merge on raw key
                rep, prov = {}, {}
                for i, k in enumerate(raw_keys):
                    if k is None: continue
                    if k not in rep:
                        rep[k] = i; prov[k] = [bool(src_tier[i]), bool(src_train[i]), bool(src_coco[i]), int(tier_row[i]), int(pool_pid[i]), float(fp[i]) if np.isfinite(fp[i]) else -np.inf]
                    else:
                        p = prov[k]; p[0] |= bool(src_tier[i]); p[1] |= bool(src_train[i]); p[2] |= bool(src_coco[i])
                        if p[3] < 0: p[3] = int(tier_row[i])
                        if p[4] < 0: p[4] = int(pool_pid[i])
                        if np.isfinite(fp[i]) and fp[i] > p[5]: p[5] = float(fp[i])
                keys = list(rep.keys()); n_u = len(keys)
                if n_u == 0:
                    rows.append(dict(set=set_name, molecule=mid, group=it["group"], n_window_structures=len(smiles), n_unparsable=sum(k is None for k in raw_keys), n_unique=0,
                                     truth_in_window_raw=False, seconds=time.time() - tm0)); continue
                P = np.array([prov[k] for k in keys], dtype=object)
                in_tier = P[:, 0].astype(bool); in_train = P[:, 1].astype(bool); in_coco = P[:, 2].astype(bool)
                trow = P[:, 3].astype(np.int64); ppid_u = P[:, 4].astype(np.int64); fpu = P[:, 5].astype(float); fpu[~np.isfinite(fpu)] = np.nan
                truth_i = keys.index(it["truth_raw"]) if it["truth_raw"] in rep else -1
                if truth_i >= 0: in_train[truth_i] = False                      # class-2 proxy: the truth is not a library structure
                # ---- documentation priors
                comp = {n: np.zeros(n_u, np.float32) for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")}
                ht = trow >= 0; hp = (~ht) & (ppid_u >= 0)
                for n in comp:
                    if ht.any(): comp[n][ht] = np.asarray(PC[n][np.sort(trow[ht])], dtype=np.float32)[np.argsort(np.argsort(trow[ht]))]
                    if hp.any(): comp[n][hp] = np.asarray(PL[n][ppid_u[hp]], dtype=np.float32)
                comp["np"][(~ht) & (~hp)] = 1.0                                   # COCONUT-only structures are natural products
                comp["np"][in_coco] = np.maximum(comp["np"][in_coco], 1.0)
                pop_public = comp["lsid"] + comp["lpmid"] + 0.5 * comp["lsynonyms"] + 1.0 * (comp["np"] != 0) + 0.5 * ((comp["src_mask"].astype(np.int64) & 1) != 0) + 0.5 * np.log1p(np.maximum(comp["lotus_refs"], 0))
                fpz = np.nan_to_num(fpu, nan=np.nanmin(fpu) if np.isfinite(fpu).any() else 0.0)
                zf = (fpz - fpz.mean()) / (fpz.std() + 1e-9)
                fpp = zf + LAM_PUBLIC * pop_public
                fp_rank = rank_of(fpu, truth_i); fpp_rank = rank_of(fpp, truth_i); pop_rank = rank_of(pop_public + 1e-6 * zf, truth_i)
                K = min(a.k, n_u)
                top_fp = np.argsort(-np.nan_to_num(fpu, nan=-1e18), kind="stable")[:K]; top_fpp = np.argsort(-fpp, kind="stable")[:K]
                short = np.union1d(top_fp, top_fpp); set_fp, set_fpp = set(top_fp.tolist()), set(top_fpp.tolist())
                # ---- official keys for the shortlist, merge duplicates (max FP), identify the truth
                s_smiles = [smiles[rep[keys[i]]] for i in short]
                okeys = [k for r in wp.map(_okey, [s_smiles[i:i + 25] for i in range(0, len(s_smiles), 25)]) for k in r]
                best = {}
                for j, i in enumerate(short):
                    ok = okeys[j]
                    if ok is None: continue
                    if ok not in best or (np.nan_to_num(fpu[i], nan=-1e18) > np.nan_to_num(fpu[best[ok]], nan=-1e18)):
                        if ok in best:  # OR provenance into the new representative
                            b = best[ok]; in_tier[i] |= in_tier[b]; in_train[i] |= in_train[b]; in_coco[i] |= in_coco[b]
                        best[ok] = i
                    else:
                        b = best[ok]; in_tier[b] |= in_tier[i]; in_train[b] |= in_train[i]; in_coco[b] |= in_coco[i]
                truth_key = it["truth_key"]; truth_in_short = truth_key in best
                if truth_in_short: in_train[best[truth_key]] = False
                for ok, i in best.items():
                    cand_rows.append(dict(set=set_name, molecule=mid, smiles=smiles[rep[keys[i]]], raw_key=keys[i], official_key=ok, is_truth=(ok == truth_key),
                                          in_tier=bool(in_tier[i]), in_train=bool(in_train[i]), in_coconut=bool(in_coco[i]), tier_row=int(trow[i]), pool_pid=int(ppid_u[i]),
                                          fp=float(fpu[i]) if np.isfinite(fpu[i]) else None, fp_rank_window=rank_of(fpu, i), in_top_fp=bool(i in set_fp), in_top_fpprior=bool(i in set_fpp),
                                          **{n: float(comp[n][i]) for n in comp}, pop_public=float(pop_public[i])))
                runner.append(dict(mid=mid, spectra=spectra, cands=[smiles[rep[keys[i]]] for i in best.values()]))
                rows.append(dict(set=set_name, molecule=mid, group=it["group"], lib=it["lib"], n_window_structures=len(smiles), n_tier_structures=len(t_smis), n_pool_structures=len(p_smis), n_coco_structures=len(c_smis),
                                 n_unparsable=int(sum(k is None for k in raw_keys)), n_unique=n_u, n_unique_tier=int(in_tier.sum()), n_unique_train=int(in_train.sum()), n_unique_coconut=int(in_coco.sum()),
                                 n_unique_external_only=int((~in_train).sum()), truth_in_window_raw=truth_i >= 0, truth_fp_rank_window=fp_rank, truth_fpprior_rank_window=fpp_rank, truth_pop_rank_window=pop_rank,
                                 n_shortlist_raw=len(short), n_shortlist_official=len(best), truth_in_shortlist=truth_in_short,
                                 truth_in_tier=bool(in_tier[truth_i]) if truth_i >= 0 else None, truth_in_coconut=bool(in_coco[truth_i]) if truth_i >= 0 else None,
                                 n_spectra=len(spectra), ce_known=float(np.mean([bool(s["ce_ev"]) for s in spectra])), seconds=time.time() - tm0))
                if (n_i + 1) % 20 == 0 or n_i == len(its) - 1:
                    d = pd.DataFrame(rows)
                    print(f"  {set_name} {n_i+1}/{len(its)} | window unique median {d.n_unique.median():.0f} | truth in window {int(d.truth_in_window_raw.sum())} | FP rank median {d.truth_fp_rank_window.median()} | "
                          f"in shortlist {int(d.truth_in_shortlist.sum())} | {d.seconds.mean():.1f}s/mol ({time.time()-t0:.0f}s)", flush=True)
            pd.DataFrame(rows).to_csv(f"{a.run}/p1_funnel_{set_name}.csv", index=False)
            pd.DataFrame(cand_rows).to_parquet(f"{a.run}/p1_shortlist_{set_name}.parquet", index=False)
            json.dump(runner, open(f"{a.run}/p1_runner_{set_name}_in.json", "w"))
            print(f"saved {set_name}: {len(rows)} molecules, {len(cand_rows)} shortlist candidates ({time.time()-t0:.0f}s)", flush=True)
    import rdkit, torch as _t
    man = dict(k=a.k, lam_public=LAM_PUBLIC, ppm=PPM, fpnet_checkpoint=sha(f"{a.fold_safe}/fpnet_fold0.pt"), fp_bits=sha(f"{a.fold_safe}/fp_bits.npy"),
               pop_files={n: sha(f"{a.pop}/pc_{n}.npy") for n in ("lsid", "lpmid", "lsynonyms", "np", "src_mask", "lotus_refs")},
               pool_meta=sha(a.pool), rdkit=rdkit.__version__, torch=_t.__version__, seconds=round(time.time() - t0))
    json.dump(man, open(f"{a.run}/p1_funnel_manifest.json", "w"), indent=1)
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
