"""W135 stage-2 preparation (139; data only): GLACIER runner input for the B products of one world.
Reads ONLY the molecule ids and the B_detail_<arm> column of the generation table (no truth, class, reach or P-rank column), the world's runner
input (query spectra) and, for a molecule without a runner entry (empty world window: no DB candidate, but products can exist), its query
spectra built from the spectra store with the world's rule (selection library, test adducts, select_queries max 8 with the raw CE, enveda-180
positive electron shift) in the runner format of b1_world.py. Writes <out>.json = [{mid, spectra, cands: B product SMILES with the heavy-atom
filter of b1_features}] for gl_runner.
v2 (2026-10-30 02:2x): runner entries for molecules without one (v1 stopped there).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_prodgl_in.py --world experiments/w135/worlds/dF1_p30 --set dF1 --arm both
       --out experiments/w135/worlds/dF1_p30/prod_runner_in.json"""
import argparse, json, os, sys
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_features import heavy_ok
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
ap = argparse.ArgumentParser(); ap.add_argument("--world", required=True); ap.add_argument("--set", required=True); ap.add_argument("--arm", default="both")
ap.add_argument("--table", default="gen_full_v2"); ap.add_argument("--out", required=True); a = ap.parse_args()
W = a.world if os.path.isabs(a.world) else os.path.join(ROOT, a.world)
G = pd.read_parquet(os.path.join(W, a.table + ".parquet"), columns=["molecule", f"B_detail_{a.arm}"]); G["molecule"] = G.molecule.astype(str)
R = {d["mid"]: d for d in json.load(open(os.path.join(W, f"b1_runner_{a.set}_in.json")))}
miss = [m for m in G.molecule if m not in R]
if miss:
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{a.set}.csv")); bt["molecule"] = bt.molecule.astype(str); LIB = dict(zip(bt.molecule, bt.lib.astype(str)))
    st = os.path.join(ROOT, "data/processed/spectra_store")
    S_MZ = np.load(f"{st}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{st}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{st}/spec_off.npy")
    meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "instrument_type"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy(); inst_of_row = meta["instrument_type"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("inchikey14").is_in(miss)).group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    for m in miss:
        lib = LIB[m]; shift = ELECTRON if lib == "enveda-180" else 0.0
        qrows = sorted(int(x) for x in ik_rows.get(m, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); rspec = []
        for x in q:
            sh = shift if mode_of_row[x] == "positive" else 0.0; s, e = int(S_OFF[x]), int(S_OFF[x + 1])
            mz = np.asarray(S_MZ[s:e], np.float64) - sh; it = np.asarray(S_IT[s:e], np.float64); ce = float(ce_of_row[x]) if np.isfinite(ce_of_row[x]) else None
            rspec.append(dict(mz=mz.tolist(), it=it.tolist(), prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x], instrument=inst_of_row[x] or "",
                              ce_ev=[ce] if ce is not None else None, ce_orig=None, ce_units="eV" if ce is not None else None))
        R[m] = dict(mid=m, spectra=rspec)
out, n = [], 0
for m, det in zip(G.molecule, G[f"B_detail_{a.arm}"]):
    cands = [d[1] for d in json.loads(det) if heavy_ok(d[1])]; n += len(cands)
    out.append(dict(mid=m, spectra=R[m]["spectra"], cands=cands))
json.dump(out, open(a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out), "w"))
print(f"{len(out)} molecules ({len(miss)} without a world runner entry: spectra from the store), {n} product candidates -> {a.out}")
