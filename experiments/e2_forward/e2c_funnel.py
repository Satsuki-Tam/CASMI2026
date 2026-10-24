"""E2c: end-to-end class-2-like funnel on the E2b v2 molecules, WITHOUT giving the formula or forcing the truth in.

Stage 1  candidate window : all PubChem-tier structures within +-10 ppm of the neutral mass from the (electron-corrected)
                            median [M+H]+ precursor; deduplicated on raw InChIKey14. Truth present only if its raw key is there.
Stage 2  fingerprint ranking: fold-safe FPNet (fold = the molecule's identity fold, never trained on it) scores every window
                            candidate by f_c . z (merged spectra, eval_ckpt protocol); truth rank recorded.
Stage 3  shortlist + forward: top-K (K = 100) by FPNet are written out for GLACIER/ICEBERG; the fused order
                            z(FP) + z(GL) inside the top-K is evaluated later by e2c_evaluate.py.

Usage: python -X utf8 e2c_funnel.py <set_name> <v2_dir> <pubchem_tier_dir> <fold_safe_dir> <v3_code_dir> <folds_dir> <out_dir> [K] [workers]
Outputs: <out_dir>/funnel_<set>.csv (per molecule), <out_dir>/e2c_<set>_in.json (runner input, truth-aware: 'truth_rank_fp')
"""
import json, os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd, torch

NAME, V2, T, FS, V3, FOLDS, OUT = sys.argv[1:8]
K = int(sys.argv[8]) if len(sys.argv) > 8 else 100
WORKERS = int(sys.argv[9]) if len(sys.argv) > 9 else 12
PROTON, PPM = 1.007276, 10.0
sys.path.insert(0, V3)
from casmi import fpnet, chem                  # noqa: E402
from casmi.spectra import merge_spectra       # noqa: E402

bits = np.load(f"{FS}/fp_bits.npy")


def _init():
    sys.path.insert(0, V3)
    global chem_w, bits_w
    from casmi import chem as chem_w
    bits_w = np.load(f"{FS}/fp_bits.npy")


def _score(args):
    """worker: fingerprint a list of SMILES and return f.z scores (nan where unparsable)."""
    smiles, zlog = args
    out = np.full(len(smiles), np.nan, np.float32)
    for i, s in enumerate(smiles):
        f = chem_w.raw_fingerprint(s)
        if f is not None:
            out[i] = float(f[bits_w].astype(np.float32) @ zlog)
    return out


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    items = json.load(open(f"{V2}/e2b_{NAME}_in.json"))
    mols = pd.read_csv(f"{V2}/e2b_{NAME}_molecules.csv").set_index("molecule")
    fold_of = pd.read_parquet(f"{FOLDS}/structures.parquet")[["inchikey14", "fold_identity"]].drop_duplicates("inchikey14").set_index("inchikey14").fold_identity
    mass = np.load(f"{T}/pc_mass.npy", mmap_mode="r"); off = np.load(f"{T}/pc_off.npy", mmap_mode="r"); buf = np.load(f"{T}/pc_smiles.npy", mmap_mode="r")
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    models, dtype = {}, fpnet.autocast_dtype("cuda")

    def model_for(k):
        if k not in models: models[k] = fpnet.load_model(f"{FS}/fpnet_fold{k}.pt", "cuda")
        return models[k]

    def window(target):
        tol = target * PPM * 1e-6
        a = int(np.searchsorted(mass, target - tol, "left")); b = int(np.searchsorted(mass, target + tol, "right"))
        if b <= a: return []
        o = np.asarray(off[a:b + 1]).astype(np.int64); raw = bytes(buf[o[0]:o[-1]]); base = o[0]
        return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(b - a)]

    rows, runner_items = [], []
    with Pool(WORKERS, initializer=_init) as pool, torch.no_grad():
        for n, it in enumerate(items):
            mid, spectra = it["mid"], it["spectra"][:8]
            truth_smi = it["cands"][0]
            tm = Chem.MolFromSmiles(truth_smi); truth_raw = Chem.MolToInchiKey(tm)[:14]
            prec = float(np.median([s["prec"] for s in spectra]))
            smis = window(prec - PROTON)
            # dedupe on raw InChIKey14 (keep first SMILES); find the truth
            keys, keep = [], []
            seen = set()
            for s in smis:
                m = Chem.MolFromSmiles(s)
                if m is None: continue
                k = Chem.MolToInchiKey(m)[:14]
                if k in seen: continue
                seen.add(k); keys.append(k); keep.append(s)
            n_window = len(keep); truth_idx = keys.index(truth_raw) if truth_raw in seen else -1
            # FPNet logits from merged spectra
            kf = int(fold_of.get(mid, 0)) if mid in fold_of.index else 0
            pairs = [(np.asarray(s["mz"], float), np.asarray(s["it"], float)) for s in spectra]
            mz, inten = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
            ces = [float(np.mean(s["ce_ev"])) for s in spectra if s.get("ce_ev")]
            nm = int(sum(max(1, len(s["ce_ev"] or [])) for s in spectra))
            pm, pi = fpnet.prep_peaks(mz, inten, prec)
            inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index("[M+H]+"), ce=float(np.mean(ces)) if ces else 0.0,
                                      ce_known=1.0 if ces else 0.0, n_merged=min(nm, 8), mode=1.0)], "cuda")
            with torch.autocast("cuda", dtype=dtype):
                zlog = model_for(kf)(*inp)[0].float()[0].cpu().numpy().astype(np.float32)
            # parallel fingerprint scoring of the whole window
            chunks = [keep[i:i + 400] for i in range(0, n_window, 400)]
            scores = np.concatenate(pool.map(_score, [(c, zlog) for c in chunks])) if chunks else np.zeros(0, np.float32)
            order = np.argsort(-np.nan_to_num(scores, nan=-1e9), kind="stable")
            fp_rank = int(np.sum(np.nan_to_num(scores, nan=-1e9) > scores[truth_idx])) + 1 if truth_idx >= 0 and np.isfinite(scores[truth_idx]) else None
            top = [keep[i] for i in order[:K]]
            truth_in_topk = truth_idx >= 0 and fp_rank is not None and fp_rank <= K
            rows.append(dict(molecule=mid, fold=kf, n_window=n_window, truth_in_window=truth_idx >= 0, fp_rank=fp_rank, truth_in_topK=truth_in_topk,
                             fp_rr25=(1.0 / fp_rank if fp_rank and fp_rank <= 25 else 0.0), truth_smiles=truth_smi))
            runner_items.append(dict(mid=mid, spectra=spectra, cands=top, truth_smiles=truth_smi, truth_rank_fp=fp_rank))
            if (n + 1) % 25 == 0: print(f"  {n+1}/{len(items)} window median so far {np.median([r['n_window'] for r in rows]):.0f} ({time.time()-t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows).set_index("molecule").join(mols[["lib", "n_window_same_formula", "instruments"]], how="left")
    df.to_csv(f"{OUT}/funnel_{NAME}.csv")
    json.dump(runner_items, open(f"{OUT}/e2c_{NAME}_in.json", "w"))
    print(f"{NAME}: {len(df)} molecules | window median {df.n_window.median():.0f} (p90 {df.n_window.quantile(.9):.0f}) | truth in window {int(df.truth_in_window.sum())} | "
          f"FP rank median {df.fp_rank.median()} | truth in top-{K} {int(df.truth_in_topK.sum())} | FP-only MRR@25 {df.fp_rr25.mean():.4f} | FP top-1 {(df.fp_rank == 1).mean():.3f} | {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
