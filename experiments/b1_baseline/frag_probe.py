"""MetFrag-lite fragmentation scores (b1_frag) for the shortlists of the evaluation views (label-free; the score depends only on the
candidate structure and the query spectra, so it is computed once per (molecule, candidate) and written for both views).
Query spectra = b1_features' selection (selection library, test adducts, select_queries max 8, enveda-180 positive electron shift).
Usage: python -X utf8 frag_probe.py --runs RUN:EVAL_CSV:SET1,SET2 ... --out diag/frag_<name>.parquet [--workers 16]
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries  # noqa: E402
import b1_frag as BF  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--workers", type=int, default=16); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64)
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
S_MZ = S_IT = S_OFF = None


def _init():
    global S_MZ, S_IT, S_OFF
    S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")


def job(args):
    s, mid, lib, smiles = args
    qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
    q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
    spec = []
    for x in q:
        sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
        spec.append(dict(mz=np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], float) - sh, it=np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], float), prec=float(prec_of_row[x]) - sh, mode=mode_of_row[x]))
    return [(s, mid, smi, BF.score(BF.fragments(smi), spec)) for smi in smiles]


tasks = []
for spec_ in a.runs:
    run, eval_csv, sets = spec_.split(":")
    ev = pd.read_csv(os.path.join(HERE, eval_csv)); ev["molecule"] = ev["molecule"].astype(str)
    for s in sets.split(","):
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "in_short_c1", "in_short_c2"]); F["molecule"] = F["molecule"].astype(str)
        F = F[F.in_short_c1 | F.in_short_c2]
        mols = ev[ev.set == s]
        if a.limit: mols = mols.head(a.limit)
        lib_of = dict(zip(mols.molecule, mols.lib))
        for mid, g in F[F.molecule.isin(set(mols.molecule))].groupby("molecule"):
            tasks.append((s, mid, lib_of[mid], sorted(set(g.smiles.astype(str)))))
print(f"[frag] {len(tasks)} molecules, {sum(len(t[3]) for t in tasks):,} candidates", flush=True)
rows = []
with Pool(a.workers, initializer=_init) as p:
    for n_, res in enumerate(p.imap_unordered(job, tasks, chunksize=2)):
        rows += res
        if n_ % 100 == 0: print(f"[frag {time.time() - T0:5.0f}s] {n_ + 1}/{len(tasks)}", flush=True)
out = pd.DataFrame(rows, columns=["set", "molecule", "smiles", "frag"])
out = pd.concat([out.assign(view="c1"), out.assign(view="c2")], ignore_index=True)
out.to_parquet(os.path.join(HERE, a.out), index=False); print(f"[frag {time.time() - T0:5.0f}s] saved {a.out}: {len(out):,} rows", flush=True)
