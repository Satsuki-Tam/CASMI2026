"""DreaMS embeddings (1024-d) of spectra-store rows with the inference-only model in dreams_min.py (MIT, see its header).
Preprocessing exactly as dreams_min.preprocess_spectrum (top-100 peaks by intensity in m/z order, base-peak normalised, precursor token
[precursor_mz, 1.1]); spectra with no fragment peak get a zero vector and flag 0.
  --bench N : embed N enveda-180 rows, time fp32 vs bf16 autocast, compare with the dataset's precomputed embeddings (cosine)
  --out DIR : embed every store row -> DIR/emb_f16.npy (memmap [n_rows, 1024] float16), DIR/ok.npy, DIR/manifest.json
Usage: python -I -X utf8 dreams_embed.py --weights <embedding_model_state_dict.pt> [--bench 4096 --ref_dir <dataset dir>] [--out DIR]
"""
import argparse, json, os, sys, time
import numpy as np, polars as pl, torch
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import dreams_min as DM

ap = argparse.ArgumentParser(); ap.add_argument("--weights", required=True); ap.add_argument("--store", default=f"{ROOT}/data/processed/spectra_store")
ap.add_argument("--bench", type=int, default=0); ap.add_argument("--ref_dir", default=""); ap.add_argument("--out", default="")
ap.add_argument("--bs", type=int, default=512); ap.add_argument("--bf16", type=int, default=1); ap.add_argument("--rows", default="", help="optional .npy of store rows to embed (default all)")
a = ap.parse_args()
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet", columns=["row", "ingest_lib", "precursor_mz", "inchikey14"])
MZ = np.load(f"{a.store}/spec_mz.npy", mmap_mode="r"); IT = np.load(f"{a.store}/spec_int.npy", mmap_mode="r"); OFF = np.load(f"{a.store}/spec_off.npy")
row = meta["row"].to_numpy(); prec = meta["precursor_mz"].to_numpy().astype(np.float32)
assert np.array_equal(row, np.arange(len(row))), "store rows must be 0..n-1"
model = DM.load_model(a.weights, "cuda")

def prep(rows):
    X = np.zeros((len(rows), DM.N_HIGHEST_PEAKS + 1, 2), np.float32); ok = np.zeros(len(rows), bool)
    for j, r in enumerate(rows):
        mz = np.asarray(MZ[OFF[r]:OFF[r + 1]], np.float32); it = np.asarray(IT[OFF[r]:OFF[r + 1]], np.float32)
        if len(mz) == 0 or not np.isfinite(prec[r]) or it.max() <= 0: continue
        X[j] = DM.preprocess_spectrum(mz, it, float(prec[r])); ok[j] = True
    return X, ok

@torch.inference_mode()
def embed(X, bf16):
    x = torch.from_numpy(X).cuda()
    if bf16:
        with torch.autocast("cuda", dtype=torch.bfloat16): e = model(x)
    else: e = model(x)
    return e.float().cpu().numpy()

if a.bench:
    sel = meta.filter(pl.col("ingest_lib") == "enveda-180")["row"].to_numpy()
    rng = np.random.default_rng(0); rows = np.sort(rng.choice(sel, a.bench, replace=False))
    X, ok = prep(rows)
    for bf16 in (0, 1):
        embed(X[:a.bs], bf16); torch.cuda.synchronize(); t0 = time.time(); outs = []
        for s in range(0, len(rows), a.bs): outs.append(embed(X[s:s + a.bs], bf16))
        torch.cuda.synchronize(); dt = time.time() - t0; E = np.concatenate(outs)
        print(f"bf16={bf16}: {len(rows) / dt:,.0f} spectra/s (bs {a.bs})", flush=True)
        if bf16 == 0: E32 = E
        else: print("bf16 vs fp32 cosine: min %.4f median %.4f" % tuple(np.quantile((E * E32).sum(1) / np.linalg.norm(E, axis=1) / np.linalg.norm(E32, axis=1), [0, 0.5])))
    if a.ref_dir:
        ix = pl.read_parquet(f"{a.ref_dir}/Enveda180_DreaMS_index.parquet", columns=["train_idx", "inchikey14", "precursor_mz"]).with_row_index("i")
        R = np.load(f"{a.ref_dir}/Enveda180_DreaMS_embeddings.npy", mmap_mode="r")
        m = pl.DataFrame({"train_idx": rows.astype(np.int64), "j": np.arange(len(rows))}).join(ix.with_columns(pl.col("train_idx").cast(pl.Int64)), on="train_idx", how="inner")
        ik = meta["inchikey14"].to_numpy()
        same_key = np.mean([ik[rows[j]] == k for j, k in zip(m["j"], m["inchikey14"])])
        Rm = np.asarray(R[m["i"].to_numpy()]); Em = E32[m["j"].to_numpy()]
        cos = (Rm * Em).sum(1) / np.linalg.norm(Rm, axis=1) / np.linalg.norm(Em, axis=1)
        print(f"matched {m.height}/{len(rows)} rows by train_idx, same inchikey14 {same_key:.4f}, cosine to precomputed: min {cos.min():.4f} median {np.median(cos):.4f}")
    sys.exit(0)

if a.out:
    os.makedirs(a.out, exist_ok=True)
    rows = np.load(a.rows) if a.rows else row
    E = np.lib.format.open_memmap(f"{a.out}/emb_f16.npy", mode="w+", dtype=np.float16, shape=(len(row), 1024))
    OK = np.zeros(len(row), bool); t0 = time.time(); chunk = a.bs * 16
    for s in range(0, len(rows), chunk):
        rr = rows[s:s + chunk]; X, ok = prep(rr)
        outs = [embed(X[b:b + a.bs], a.bf16) for b in range(0, len(rr), a.bs)]
        e = np.concatenate(outs); e[~ok] = 0; E[rr] = e.astype(np.float16); OK[rr] = ok
        if (s // chunk) % 20 == 0: print(f"{s + len(rr):,}/{len(rows):,} {time.time() - t0:.0f}s", flush=True)
    E.flush(); np.save(f"{a.out}/ok.npy", OK)
    json.dump(dict(n_rows=int(len(row)), embedded=int(len(rows)), ok=int(OK.sum()), bf16=int(a.bf16), weights=os.path.basename(a.weights),
                   seconds=round(time.time() - t0, 1)), open(f"{a.out}/manifest.json", "w"), indent=1)
    print("DONE", OK.sum(), f"{time.time() - t0:.0f}s")
