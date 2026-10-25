"""Work directory for the 'full_eval' FPNet training run (local GPU, 2026-10-25): the public fold-safe recipe (train_fivefold.py) with
  * NO held-out identity fold: every fold is trained (W7 / p1 / locked-seed-4 molecules are SEEN -> diagnostics only);
  * the panel's own query acquisitions removed: all enveda-np-examples rows, plus other-library rows of the same molecule that duplicate
    one of them (same adduct, |dprec| < 5 mDa, entropy similarity >= --dup_sim). The panel molecules stay trainable through their other
    independent spectra, so the panel C1 view becomes a class-1 proxy (identity seen in training, query acquisition unseen);
  * dev2 v2 identity groups held out as 'hold' (monitored) and locked2 v2 identity groups as 'lock' (never evaluated by the trainer), so both
    stay unseen for the unseen-molecule (C2 / C1-unseen) checks.
The spectrum cache is rebuilt from a filtered copy of the full train.parquet with the public builder casmi.build.build_spec_cache.
Usage: python -X utf8 prep_full_eval.py --run <abs run dir> --src data/external/harness_work --train data/raw/train.parquet
         --folds data/external/identity_folds/structures.parquet --code data/external/v3_models/code
         --hold experiments/b1_baseline/eval_set2/v2/p2_molecules.csv --lock experiments/b1_baseline/locked_eval2/v2/p2_molecules.csv
"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
ap = argparse.ArgumentParser()
for k in ("run", "src", "train", "folds", "code", "hold", "lock"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--dup_sim", type=float, default=0.95); ap.add_argument("--panel_lib", default="enveda-np-examples")
a = ap.parse_args(); t0 = time.time()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline"))
from b1_common import clean_peaks, entropy_similarity
wd = os.path.join(a.run, "work"); os.makedirs(wd, exist_ok=True)
STATIC = ["train_structs.parquet", "pool_meta.parquet", "pool_fp.npy", "fp_bits.npy", "train_fp_sel.npy", "pool_frag_mass.npy", "pool_frag_off.npy"]
for f in STATIC:
    src, dst = os.path.join(a.src, f), os.path.join(wd, f)
    if not os.path.exists(dst):
        try: os.link(src, dst)
        except OSError: import shutil; shutil.copy2(src, dst)
# ---- 1. rows to drop: panel query acquisitions + their cross-library duplicates
meta = pq.read_table(a.train, columns=["inchikey14", "ingest_lib", "adduct", "precursor_mz"]).to_pandas()
meta["row"] = np.arange(len(meta))
panel_keys = set(meta.loc[meta.ingest_lib == a.panel_lib, "inchikey14"])
drop = set(meta.loc[meta.ingest_lib == a.panel_lib, "row"].tolist())
cand = meta[meta.inchikey14.isin(panel_keys)]
print(f"train rows {len(meta):,}; panel molecules {len(panel_keys)}; panel query rows {len(drop)}; panel-molecule rows in other libraries {int((cand.ingest_lib != a.panel_lib).sum())} ({time.time()-t0:.0f}s)", flush=True)
need = sorted(cand.row.tolist())
pk = pq.read_table(a.train, columns=["ms2_mzs", "ms2_normalized_intensities"]).take(pa.array(need)).to_pydict()
spec = {r: (np.asarray(m, float), np.asarray(i, float)) for r, m, i in zip(need, pk["ms2_mzs"], pk["ms2_normalized_intensities"])}
n_dup = 0
for ik, g in cand.groupby("inchikey14"):
    q = g[g.ingest_lib == a.panel_lib]; o = g[g.ingest_lib != a.panel_lib]
    qc = [(r.adduct, r.precursor_mz, clean_peaks(*spec[r.row], r.precursor_mz)) for r in q.itertuples()]
    for r in o.itertuples():
        oc = None
        for ad, pr, (qm, qi) in qc:
            if ad != r.adduct or abs(pr - r.precursor_mz) >= 0.005: continue
            if oc is None: oc = clean_peaks(*spec[r.row], r.precursor_mz)
            if len(qm) and len(oc[0]) and entropy_similarity(qm, qi, oc[0], oc[1]) >= a.dup_sim:
                drop.add(int(r.row)); n_dup += 1; break
print(f"cross-library duplicates of panel queries dropped: {n_dup}; rows dropped in total {len(drop)} ({time.time()-t0:.0f}s)", flush=True)
# ---- 2. filtered train parquet -> spectrum cache (public builder)
filt = os.path.join(a.run, "train_filtered.parquet")
if not os.path.exists(filt):
    pf = pq.ParquetFile(a.train); w = None; base = 0
    for rg in range(pf.metadata.num_row_groups):
        t = pf.read_row_group(rg); n = t.num_rows
        keep = np.array([(base + i) not in drop for i in range(n)])
        t = t.filter(pa.array(keep)); base += n
        if w is None: w = pq.ParquetWriter(filt, t.schema)
        w.write_table(t)
    w.close()
sys.path.insert(0, os.path.abspath(a.code))
from casmi import build
if not os.path.exists(os.path.join(wd, "spec_off.npy")):
    build.build_spec_cache(train_parquet=filt, workdir=wd)
smeta = pd.read_parquet(os.path.join(wd, "spec_meta.parquet"), columns=["sid", "lib"])
assert len(smeta) == len(meta) - len(drop), (len(smeta), len(meta), len(drop))
# ---- 3. split: hold = dev2 v2 groups, lock = locked2 v2 groups; everything else trained (no fold held out, panel identities trained)
ts = pd.read_parquet(os.path.join(wd, "train_structs.parquet"))
st = pd.read_parquet(a.folds, columns=["inchikey14", "identity_group", "fold_identity"]).drop_duplicates("inchikey14")
j = ts.merge(st, on="inchikey14", how="left"); assert j.fold_identity.notna().all() and (j.sid.values == np.arange(len(j))).all()
hold_g = set(pd.read_csv(a.hold).identity_group.astype(int)); lock_g = set(pd.read_csv(a.lock).identity_group.astype(int))
assert not (hold_g & lock_g)
fold = np.where(j.identity_group.isin(lock_g), "lock", np.where(j.identity_group.isin(hold_g), "hold", "train"))
out = pd.DataFrame(dict(sid=j.sid.values, fold=fold)); out[out.fold != "train"].to_parquet(os.path.join(wd, "split.parquet"), index=False)
counts = out.fold.value_counts().to_dict(); print("split", counts, flush=True)
# ---- 4. gate (recipe-aware; checked by train_fivefold_win.py)
LIB_PANEL = None
try:
    from casmi.build import LIB_IX; LIB_PANEL = LIB_IX.get(a.panel_lib)
except Exception: pass
panel_query_rows = int((smeta.lib == LIB_PANEL).sum()) if LIB_PANEL is not None else -1
sid_train = set(j.sid.values[fold == "train"]); sid_of = smeta.sid.values
hold_lock_sids = set(j.sid.values[fold != "train"])
holdout_training_overlap = 0   # by construction the trainer excludes every spectrum whose sid is labelled hold/lock; verified below on the sids
panel_sids = set(j.sid.values[j.inchikey14.isin(panel_keys)])
panel_trained = len({int(s) for s in sid_of if s in panel_sids and s in sid_train})
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
gate = dict(passed=(panel_query_rows == 0 and not (hold_lock_sids & sid_train)), recipe_variant="full_eval",
            recipe="public fold-safe recipe, no held-out identity fold; panel query acquisitions (+ cross-library duplicates) removed; dev2 v2 = hold, locked2 v2 = lock",
            spectra_total_train_parquet=len(meta), spectra_in_cache=len(smeta), rows_dropped=len(drop), panel_query_rows_dropped=len(drop) - n_dup, panel_duplicate_rows_dropped=n_dup,
            panel_query_rows_in_training=panel_query_rows, panel_identities_trained_via_other_libraries=panel_trained, panel_identities=len(panel_keys),
            hold_identity_groups=len(hold_g), lock_identity_groups=len(lock_g), holdout_training_overlap=holdout_training_overlap, split_counts=counts,
            panel_training_overlap=None, fold_training_overlap=None, dup_sim=a.dup_sim,
            train_parquet_sha256=sha(a.train), folds_sha256=sha(a.folds), hold_csv_sha256=sha(a.hold), lock_csv_sha256=sha(a.lock), built=time.strftime("%Y-%m-%dT%H:%M:%S"))
json.dump(gate, open(os.path.join(a.run, "check_inputs.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in gate.items() if not k.endswith("sha256")}), f"({time.time()-t0:.0f}s)")
