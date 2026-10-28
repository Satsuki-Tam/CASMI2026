"""111 (Codex 111): per-candidate scores for the B1 development tables, label-free.
Query spectra = exactly the b1_features policy (selection library, test adducts, select_queries round-robin, max 8, electron correction for
enveda-180 positive spectra); each spectrum is one FPNet input (n_merged 1, own precursor / adduct / CE).
  N  = mean over the query spectra of cos(s_spectrum, m_candidate) with the 111 model (= m . mean of the unit spectrum embeddings; no FP term)
  Fs = f_candidate . mean over the query spectra of the BASE FPNet logits (single-spectrum mean of the same base checkpoint; input-format control)
  Fm = f_candidate . the BASE FPNet logits of the b1_features merged input (spectra of a polarity merged, size-weighted mean over polarities) on
       the SAME representative SMILES (Codex 112: separates the single-spectrum input from the table's spelling aggregation)
Candidates = every row of b1_features_<set>.parquet (one row per official key; its representative SMILES; bits = casmi.chem.raw_fingerprint[fp_bits]).
fph = 64-bit hash of the candidate's bit vector (FP-collision diagnostics). Missing values are kept as NaN and counted (never dropped).
Writes <out>/n111_<tag>_<set>.parquet (set, molecule, smiles, official_key, N, Fs, Fm, fph, n_query) and <out>/n111_<tag>_manifest.json.
Usage: python n111_score.py --model M.pt --base BASE.pt --code <casmi code> --bits fp_bits.npy --store <spectra_store> --run <table dir> --eval_csv CSV
       --tag T --sets S1 S2 ... --out DIR [--device cuda] [--limit N]"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
ap = argparse.ArgumentParser()
for k in ("model", "base", "code", "bits", "store", "run", "eval_csv", "tag", "out"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--device", default="cuda"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--max_spectra", type=int, default=8)
ap.add_argument("--workers", type=int, default=8)
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); B1 = os.path.abspath(os.path.join(HERE, "..", "b1_baseline"))
sys.path.insert(0, a.code); sys.path.insert(0, HERE); sys.path.insert(0, B1)
import torch
from multiprocessing import Pool
from casmi import fpnet, chem
from casmi.spectra import merge_spectra
from collections import Counter
from b1_common import select_queries, ADDUCT_SHIFT, ELECTRON
import n111_model as NM

BITS = None
def _init(code, bits):
    global BITS, chem_w
    sys.path.insert(0, code)
    from casmi import chem as chem_w
    BITS = np.load(bits)


def _fp(smiles):
    out = []
    for s in smiles:
        f = chem_w.raw_fingerprint(s)
        out.append(None if f is None else np.packbits(np.asarray(f[BITS], np.uint8)))
    return out


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


def main():
    t0 = time.time(); os.makedirs(a.out, exist_ok=True); dev = a.device
    model, mck = NM.load(a.model, fpnet, dev)
    bck = torch.load(a.base, map_location="cpu", weights_only=True)
    base = fpnet.FPNet(bck["nbits"], d=bck["d"], layers=bck["layers"], heads=bck.get("heads", 8)); base.load_state_dict(bck["model"]); base = base.to(dev).eval()
    nbits = base.nbits; assert model.cfg["nbits"] == nbits == len(np.load(a.bits))
    dtype = fpnet.autocast_dtype(dev) if dev == "cuda" else torch.float32
    S_MZ = np.load(f"{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    mols = pd.read_csv(a.eval_csv); mols["molecule"] = mols.molecule.astype(str)
    man = dict(model=a.model, model_sha256=sha(a.model), model_step=int(mck.get("step", -1)), base=a.base, base_sha256=sha(a.base), bits_sha256=sha(a.bits), eval_csv=a.eval_csv,
               run=a.run, sets={}, max_spectra=a.max_spectra, device=dev)
    with Pool(a.workers, initializer=_init, initargs=(a.code, a.bits)) as wp, torch.no_grad():
        for s in a.sets:
            T = pd.read_parquet(os.path.join(a.run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "official_key"]); T["molecule"] = T.molecule.astype(str)
            ms = mols[mols.set == s]
            if a.limit: ms = ms.head(a.limit); T = T[T.molecule.isin(set(ms.molecule))]
            smis = T.smiles.astype(str).unique().tolist()
            res = wp.map(_fp, [smis[i:i + 400] for i in range(0, len(smis), 400)]) if smis else []
            PK = dict(zip(smis, [x for r in res for x in r]))
            rows = []; n_noq = 0
            for r in ms.itertuples(index=False):
                mid = str(r.molecule); lib = r.lib; shift = ELECTRON if lib == "enveda-180" else 0.0
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
                q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
                cand = T[T.molecule == mid]
                if not q:
                    n_noq += 1
                    for c in cand.itertuples(index=False): rows.append(dict(set=s, molecule=mid, smiles=c.smiles, official_key=c.official_key, N=np.nan, Fs=np.nan, Fm=np.nan, fph=0, n_query=0))
                    continue
                items = []; qsp = []
                for x in q:
                    sh = shift if mode_of_row[x] == "positive" else 0.0
                    so, eo = int(S_OFF[x]), int(S_OFF[x + 1]); mz = np.asarray(S_MZ[so:eo], np.float64) - sh; it = np.asarray(S_IT[so:eo], np.float64)
                    prec = float(prec_of_row[x]) - sh; ce = float(ce_of_row[x]) if np.isfinite(ce_of_row[x]) else None
                    qsp.append(dict(mz=mz, it=it, prec=prec, adduct=add_of_row[x], mode=mode_of_row[x], ce=ce))
                    pm, pi = fpnet.prep_peaks(mz, it, prec)
                    items.append(dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(add_of_row[x]), ce=ce if ce is not None else 0.0, ce_known=1.0 if ce is not None else 0.0,
                                      n_merged=1, mode=1.0 if mode_of_row[x] == "positive" else -1.0))
                inp = fpnet.collate(items, dev)
                with torch.autocast(dev, dtype=dtype, enabled=dev == "cuda"):
                    _, _, sv = model.spectrum(*inp); zb = base(*inp)[0]
                sbar = sv.float().mean(0); zbar = zb.float().mean(0)
                zl, wsum = None, 0.0   # b1_features merged input: merge per polarity, size-weighted mean over polarities
                for mode in ("positive", "negative"):
                    grp = [g for g in qsp if g["mode"] == mode]
                    if not grp: continue
                    pairs = [(g["mz"], g["it"]) for g in grp]; mz_, it_ = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                    prec_ = float(np.median([g["prec"] for g in grp])); ces = [g["ce"] for g in grp if g["ce"] is not None]; ad = Counter(g["adduct"] for g in grp).most_common(1)[0][0]
                    pm_, pi_ = fpnet.prep_peaks(mz_, it_, prec_)
                    inp_m = fpnet.collate([dict(mz=pm_, it=pi_, prec=prec_, adduct_ix=chem.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                                n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)], dev)
                    with torch.autocast(dev, dtype=dtype, enabled=dev == "cuda"):
                        zm = base(*inp_m)[0].float().mean(0)
                    zl = zm * len(grp) if zl is None else zl + zm * len(grp); wsum += len(grp)
                zmerged = zl / wsum
                pk = [PK.get(str(sm)) for sm in cand.smiles]; ok = np.array([p is not None for p in pk])
                Nv = np.full(len(cand), np.nan); Fv = np.full(len(cand), np.nan); Mv = np.full(len(cand), np.nan); H = np.zeros(len(cand), np.int64)
                if ok.any():
                    P = torch.as_tensor(np.stack([p for p in pk if p is not None]), device=dev)
                    fb = fpnet.unpack_gpu(P, nbits)
                    with torch.autocast(dev, dtype=dtype, enabled=dev == "cuda"):
                        mv = model.molecule(fb)
                    Nv[ok] = (mv.float() @ sbar).cpu().numpy(); Fv[ok] = (fb @ zbar).cpu().numpy(); Mv[ok] = (fb @ zmerged).cpu().numpy()
                    H[ok] = [int.from_bytes(hashlib.blake2b(p.tobytes(), digest_size=8).digest(), "little", signed=True) for p in pk if p is not None]
                for c, nv, fv, mv_, h in zip(cand.itertuples(index=False), Nv, Fv, Mv, H):
                    rows.append(dict(set=s, molecule=mid, smiles=c.smiles, official_key=c.official_key, N=float(nv), Fs=float(fv), Fm=float(mv_), fph=int(h), n_query=len(q)))
            O = pd.DataFrame(rows)
            if len(O) != len(T) or O.duplicated(["molecule", "official_key"]).any(): raise RuntimeError(f"{s}: scored rows {len(O)} != table rows {len(T)} or duplicates")
            fin = np.isfinite(O.N.values) & np.isfinite(O.Fs.values) & np.isfinite(O.Fm.values)
            O.to_parquet(os.path.join(a.out, f"n111_{a.tag}_{s}.parquet"), index=False)
            man["sets"][s] = dict(rows=len(O), molecules=int(ms.molecule.nunique()), no_query=n_noq, nonfinite=int((~fin).sum()), sha256=sha(os.path.join(a.out, f"n111_{a.tag}_{s}.parquet")))
            print(f"{s}: {len(O)} rows, {ms.molecule.nunique()} molecules, no query {n_noq}, non-finite {int((~fin).sum())} ({time.time() - t0:.0f}s)", flush=True)
    json.dump(man, open(os.path.join(a.out, f"n111_{a.tag}_manifest.json"), "w"), indent=2); print("DONE", json.dumps(man)[:400])


if __name__ == "__main__":
    main()
