"""091: FPNet scored as the mean of PER-SPECTRUM logits (Fs) instead of the production polarity-merged input (F), on the FIXED candidate rows of a
b1_features run (the shortlist union stored in b1_features_<set>.parquet). Per molecule the query spectra are selected exactly as b1_features does
(selection library, test adducts, select_queries round-robin, max 8, electron shift for enveda-180 positive), with the SAME checkpoint that built the
table. Outputs per candidate row: fp_tab (table value), fp_m (recomputed merged = parity check against fp_tab), fp_s (single-spectrum logit mean;
polarity groups weighted by their size, i.e. the mean over all query spectra), fprw_s (window-rank transfer: the shortlist candidates sorted by fp_s
receive, in order, the table window ranks fp_rank_window sorted ascending -- an approximation, the full window is not re-scored).
Usage: python -X utf8 fp_mean_score.py --run run_np053_f1dev --eval_csv np053_f1dev/p2_molecules.csv --sets NP_H NP_X NP_N
       --ckpt ../../data/external/fold_safe_fpnet/fpnet_fold1.pt --out diag/fpmean_np053f1dev.parquet
"""
import argparse, os, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl, torch
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
V3 = f"{ROOT}/data/external/v3_models/code"


def _init():
    global CH, BITS
    sys.path.insert(0, V3)
    from casmi import chem as CH_
    CH = CH_; BITS = np.load(f"{ROOT}/data/external/fold_safe_fpnet/fp_bits.npy")


def _fps(smiles):
    out = np.zeros((len(smiles), len(BITS)), np.uint8); ok = np.zeros(len(smiles), bool)
    for i, s in enumerate(smiles):
        f = CH.raw_fingerprint(s)
        if f is not None: out[i] = f[BITS]; ok[i] = True
    return out, ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--sets", nargs="+", required=True)
    ap.add_argument("--ckpt", required=True); ap.add_argument("--out", required=True); ap.add_argument("--max_spectra", type=int, default=8); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(); t0 = time.time(); dev = "cuda"
    sys.path.insert(0, V3)
    from casmi import fpnet as FPN, chem as CHM
    from casmi.spectra import merge_spectra
    model = FPN.load_model(a.ckpt, dev); dt = FPN.autocast_dtype(dev)
    ST = f"{ROOT}/data/processed/spectra_store"
    meta = pl.read_parquet(f"{ST}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "ce_mean", "precursor_mz"]).sort("row")
    ik = meta["inchikey14"].to_numpy(); libr = meta["ingest_lib"].to_numpy(); addr = meta["adduct"].to_numpy(); moder = meta["ionization_mode"].to_numpy()
    cer = meta["ce_mean"].to_numpy().astype(np.float64); precr = meta["precursor_mz"].to_numpy().astype(np.float64)
    ik_rows = {}
    for r, k in enumerate(ik): ik_rows.setdefault(k, []).append(r)
    MZ = np.load(f"{ST}/spec_mz.npy", mmap_mode="r"); IT = np.load(f"{ST}/spec_int.npy", mmap_mode="r"); OFF = np.load(f"{ST}/spec_off.npy")
    def spec(r, sh): return np.asarray(MZ[OFF[r]:OFF[r + 1]], np.float64) - sh, np.asarray(IT[OFF[r]:OFF[r + 1]], np.float64)
    mols = pd.read_csv(a.eval_csv); out = []
    with Pool(a.workers, initializer=_init) as wp:
        for set_name in a.sets:
            F = pd.read_parquet(f"{a.run}/b1_features_{set_name}.parquet", columns=["set", "molecule", "smiles", "fp", "fp_rank_window"])
            ZM, ZS, NQ = {}, {}, {}
            for r in mols[mols.set == set_name].itertuples(index=False):
                mid = str(r.molecule); lib = r.lib; shift = ELECTRON if lib == "enveda-180" else 0.0
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if libr[x] == lib and addr[x] in ADDUCT_SHIFT)
                q = select_queries(qrows, a.max_spectra, lambda x: addr[x], lambda x: float(cer[x]))
                if not q: continue
                zl_m, zl_s, wsum = None, None, 0.0
                for mode in ("positive", "negative"):
                    grp = [x for x in q if moder[x] == mode]
                    if not grp: continue
                    sh = shift if mode == "positive" else 0.0
                    pairs = [spec(x, sh) for x in grp]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                    pr = float(np.median([precr[x] - sh for x in grp])); ces = [cer[x] for x in grp if np.isfinite(cer[x])]
                    ad = Counter(addr[x] for x in grp).most_common(1)[0][0]; pm, pi = FPN.prep_peaks(mz, it, pr)
                    items = [dict(mz=pm, it=pi, prec=pr, adduct_ix=CHM.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                  n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)]
                    for x in grp:
                        m1, i1 = spec(x, sh); pm1, pi1 = FPN.prep_peaks(m1, i1, precr[x] - sh); ck = bool(np.isfinite(cer[x]))
                        items.append(dict(mz=pm1, it=pi1, prec=precr[x] - sh, adduct_ix=CHM.adduct_index(addr[x]), ce=float(cer[x]) if ck else 0.0, ce_known=1.0 if ck else 0.0,
                                          n_merged=1, mode=1.0 if mode == "positive" else -1.0))
                    inp = FPN.collate(items, dev)
                    with torch.no_grad(), torch.autocast("cuda", dtype=dt): Z = model(*inp)[0].float()
                    zm = Z[0].cpu().numpy(); zs = Z[1:].mean(0).cpu().numpy()
                    zl_m = zm * len(grp) if zl_m is None else zl_m + zm * len(grp); zl_s = zs * len(grp) if zl_s is None else zl_s + zs * len(grp); wsum += len(grp)
                ZM[mid] = (zl_m / wsum).astype(np.float32); ZS[mid] = (zl_s / wsum).astype(np.float32); NQ[mid] = len(q)
            smi = F.smiles.astype(str).unique().tolist(); chunks = [smi[i:i + 500] for i in range(0, len(smi), 500)]
            fpm = {}
            for c, (fp_, ok_) in zip(chunks, wp.map(_fps, chunks)):
                for s_, f_, o_ in zip(c, fp_, ok_):
                    if o_: fpm[s_] = f_.astype(np.float32)
            fm = np.full(len(F), np.nan, np.float32); fs = np.full(len(F), np.nan, np.float32)
            for i, (m, s_) in enumerate(zip(F.molecule.astype(str), F.smiles.astype(str))):
                if m in ZM and s_ in fpm: fm[i] = float(fpm[s_] @ ZM[m]); fs[i] = float(fpm[s_] @ ZS[m])
            F = F.assign(fp_m=fm, fp_s=fs, nq=F.molecule.astype(str).map(NQ).fillna(0).astype(int))
            # window-rank transfer within each molecule
            rw = np.full(len(F), np.nan)
            for m, idx in F.groupby("molecule").indices.items():
                v = F.fp_s.values[idx]; ranks = np.sort(F.fp_rank_window.values[idx].astype(float))
                o = np.argsort(-np.nan_to_num(v, nan=-1e18), kind="stable"); rr_ = np.empty(len(idx)); rr_[o] = ranks; rw[idx] = rr_
            F["fprw_s"] = rw; out.append(F.rename(columns={"fp": "fp_tab"}))
            ok = np.isfinite(F.fp.values) & np.isfinite(fm)
            rel = np.abs(F.fp.values[ok] - fm[ok]) / (np.abs(F.fp.values[ok]) + 1.0)
            print(f"{set_name}: molecules {len(ZM)}, rows {len(F)}, parity |fp_tab - fp_m|/(|fp|+1): median {np.median(rel):.2e} max {rel.max():.2e} ({time.time() - t0:.0f}s)", flush=True)
    pd.concat(out, ignore_index=True).to_parquet(os.path.join(HERE, a.out) if not os.path.isabs(a.out) else a.out); print("saved", a.out)
