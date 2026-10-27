"""DreaMS-FP scores for the candidate rows of a b1_features run (stage (b) of 089): per molecule, the query spectra are selected exactly as
b1_features does (selection library, test adducts, select_queries round-robin, max 8), their DreaMS embeddings (dreams_embed.py output) go
through a DreaMS-FP head (dreams_fp_train.py) and the logits are averaged (all query spectra, i.e. the polarity groups weighted by size);
every candidate row gets fpD = raw_fingerprint(smiles)[fp_bits] . zD (same form as the FPNet column fp).
Usage: python -X utf8 dreams_fp_score.py --run run_np053_f1dev --eval_csv np053_f1dev/p2_molecules.csv --sets NP_H NP_X NP_N
       --head dreams_fp_f1/head.pt --out diag/fpD_np053f1dev.parquet
"""
import argparse, os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl, torch, torch.nn as nn
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, select_queries
V3 = f"{ROOT}/data/external/v3_models/code"
BITS = None


def _init():
    global BITS, CH
    sys.path.insert(0, V3)
    from casmi import chem as CH_
    CH = CH_; BITS = np.load(f"{ROOT}/data/external/fold_safe_fpnet/fp_bits.npy")


def _fps(smiles):
    out = np.zeros((len(smiles), len(BITS)), np.uint8); ok = np.zeros(len(smiles), bool)
    for i, s in enumerate(smiles):
        f = CH.raw_fingerprint(s)
        if f is not None: out[i] = f[BITS]; ok[i] = True
    return out, ok


class Head(nn.Module):
    def __init__(s, din, h, nout, drop):
        super().__init__(); s.ln = nn.LayerNorm(din)
        s.net = nn.Sequential(nn.Linear(din, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, nout))
    def forward(s, x): return s.net(s.ln(x))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--sets", nargs="+", required=True)
    ap.add_argument("--head", required=True); ap.add_argument("--out", required=True); ap.add_argument("--emb_dir", default=f"{ROOT}/data/processed/dreams_emb")
    ap.add_argument("--max_spectra", type=int, default=8); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(); t0 = time.time(); dev = "cuda"
    ck = torch.load(a.head, map_location="cpu", weights_only=True)
    model = Head(ck["din"], ck["hidden"], ck["nbits"], ck["drop"]); model.load_state_dict(ck["state"]); model.to(dev).eval()
    ADD = list(ck["adducts"]); assert ADD == list(ADDUCT_SHIFT)
    ST = f"{ROOT}/data/processed/spectra_store"
    meta = pl.read_parquet(f"{ST}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "ce_mean"]).sort("row")
    ik = meta["inchikey14"].to_numpy(); libr = meta["ingest_lib"].to_numpy(); addr = meta["adduct"].to_numpy(); moder = meta["ionization_mode"].to_numpy()
    cer = meta["ce_mean"].to_numpy().astype(np.float64)
    ik_rows = {}
    for r, k in enumerate(ik): ik_rows.setdefault(k, []).append(r)
    EMB = np.load(f"{a.emb_dir}/emb_f16.npy", mmap_mode="r"); OK = np.load(f"{a.emb_dir}/ok.npy")
    def side(rows):
        S = np.zeros((len(rows), len(ADD) + 4), np.float32)
        for j, r in enumerate(rows):
            S[j, ADD.index(addr[r]) if addr[r] in ADD else len(ADD)] = 1.0
            S[j, len(ADD) + 1] = -1.0 if moder[r] == "negative" else 1.0
            if np.isfinite(cer[r]): S[j, len(ADD) + 2] = 1.0; S[j, len(ADD) + 3] = cer[r] / 100.0
        return S
    mols = pd.read_csv(a.eval_csv); out = []
    with Pool(a.workers, initializer=_init) as wp:
        for set_name in a.sets:
            F = pd.read_parquet(f"{a.run}/b1_features_{set_name}.parquet", columns=["set", "molecule", "smiles"])
            ms = mols[mols.set == set_name]; zD = {}; nq = {}
            for r in ms.itertuples(index=False):
                mid = str(r.molecule); lib = r.lib
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if libr[x] == lib and addr[x] in ADDUCT_SHIFT)
                q = [x for x in select_queries(qrows, a.max_spectra, lambda x: addr[x], lambda x: float(cer[x])) if OK[x]]
                if not q: continue
                x = torch.cat([torch.from_numpy(np.asarray(EMB[q], np.float32)), torch.from_numpy(side(q))], 1).to(dev)
                with torch.no_grad(): zD[mid] = model(x).float().mean(0).cpu().numpy()
                nq[mid] = len(q)
            smi = F.smiles.astype(str).unique().tolist(); chunks = [smi[i:i + 500] for i in range(0, len(smi), 500)]
            res = wp.map(_fps, chunks); fpm = {}
            for c, (fp_, ok_) in zip(chunks, res):
                for s, f, o in zip(c, fp_, ok_):
                    if o: fpm[s] = f
            vals = np.full(len(F), np.nan, np.float32)
            for i, (m, s) in enumerate(zip(F.molecule.astype(str), F.smiles.astype(str))):
                if m in zD and s in fpm: vals[i] = float(fpm[s].astype(np.float32) @ zD[m])
            F = F.assign(fpD=vals, nqD=F.molecule.astype(str).map(nq).fillna(0).astype(int)); out.append(F)
            print(f"{set_name}: {F.molecule.nunique()} molecules, zD for {len(zD)}, fpD finite {np.isfinite(vals).mean():.4f} ({time.time() - t0:.0f}s)", flush=True)
    pd.concat(out, ignore_index=True).to_parquet(a.out); print("saved", a.out)
