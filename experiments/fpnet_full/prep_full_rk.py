"""Work directory for the 'full_rk' FPNet training run (021 proposal): the public fold-safe recipe with no held-out fold and
  * spectrum-level removal of QUERY ACQUISITIONS (identity stays trainable through independent spectra of other libraries):
      - the panel: every enveda-np-examples row;
      - the ranker C1 sets (eval_set/p1_molecules.csv = W7, eval_c1/p1_molecules.csv): every row of the molecule's selection library;
    plus, inside each molecule's whole identity group (all keys, 019b), rows of other libraries that duplicate a removed row
    (same adduct, |dprec| < 5 mDa, entropy similarity >= --dup_sim);
  * identity-group holdouts (no spectrum trained): dev2 v2 = 'hold' (monitored), locked2 v2 = 'lock', ranker fit set p1_run1 = 'rkfit'
    (never evaluated by the trainer; gives truly unseen C2 rows for the ranker tables).
The spectrum cache is rebuilt from a filtered copy of the full train.parquet with the public builder casmi.build.build_spec_cache.
Usage: python -X utf8 prep_full_rk.py --run <abs dir> --src data/external/harness_work --train data/raw/train.parquet --folds data/external/identity_folds/structures.parquet
         --code data/external/v3_models/code --query_sets eval_set/p1_molecules.csv eval_c1/p1_molecules.csv --hold dev2.csv --lock locked2.csv --rkfit p1_run1.csv
"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
ap = argparse.ArgumentParser()
for k in ("run", "src", "train", "folds", "code", "hold", "lock", "rkfit"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--query_sets", nargs="+", required=True); ap.add_argument("--dup_sim", type=float, default=0.95); ap.add_argument("--panel_lib", default="enveda-np-examples")
a = ap.parse_args(); t0 = time.time()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline"))
from b1_common import clean_peaks, entropy_similarity
wd = os.path.join(a.run, "work"); os.makedirs(wd, exist_ok=True)
for f in ["train_structs.parquet", "pool_meta.parquet", "pool_fp.npy", "fp_bits.npy", "train_fp_sel.npy", "pool_frag_mass.npy", "pool_frag_off.npy"]:
    src, dst = os.path.join(a.src, f), os.path.join(wd, f)
    if not os.path.exists(dst):
        try: os.link(src, dst)
        except OSError: import shutil; shutil.copy2(src, dst)
meta = pq.read_table(a.train, columns=["inchikey14", "ingest_lib", "adduct", "precursor_mz"]).to_pandas(); meta["row"] = np.arange(len(meta))
st = pd.read_parquet(a.folds, columns=["inchikey14", "identity_group", "fold_identity"]).drop_duplicates("inchikey14")
meta = meta.merge(st[["inchikey14", "identity_group"]], on="inchikey14", how="left")
# ---- query acquisitions: (molecule raw key, selection library) pairs
pairs = [(ik, a.panel_lib) for ik in meta.loc[meta.ingest_lib == a.panel_lib, "inchikey14"].unique()]
for f in a.query_sets:
    d = pd.read_csv(f); pairs += list(zip(d.molecule.astype(str), d.lib.astype(str)))
pairs = sorted(set(pairs)); qkeys = {ik for ik, _ in pairs}; libof = {}
for ik, lib in pairs: libof.setdefault(ik, set()).add(lib)
qrows_mask = meta.inchikey14.isin(qkeys) & np.array([lib in libof.get(ik, ()) for ik, lib in zip(meta.inchikey14, meta.ingest_lib)])
drop = set(meta.loc[qrows_mask, "row"].tolist())
groups = set(meta.loc[qrows_mask, "identity_group"].dropna().astype(int))
grp = meta[meta.identity_group.isin(groups)]
print(f"query pairs {len(pairs)} (molecules {len(qkeys)}); query rows {len(drop):,}; identity groups {len(groups)}; rows in those groups {len(grp):,} ({time.time()-t0:.0f}s)", flush=True)
need = sorted(grp.row.tolist())
pk = pq.read_table(a.train, columns=["ms2_mzs", "ms2_normalized_intensities"]).take(pa.array(need)).to_pydict()
clean = {r: clean_peaks(np.asarray(m, float), np.asarray(i, float), float(meta.precursor_mz.iat[r])) for r, m, i in zip(need, pk["ms2_mzs"], pk["ms2_normalized_intensities"])}
n_dup = 0
for gid, g in grp.groupby("identity_group"):
    q = g[g.row.isin(drop)]; o = g[~g.row.isin(drop)]
    if not len(q) or not len(o): continue
    for r in o.itertuples():
        for qq in q.itertuples():
            if qq.adduct != r.adduct or abs(qq.precursor_mz - r.precursor_mz) >= 0.005: continue
            qm, qi = clean[qq.row]; om, oi = clean[r.row]
            if len(qm) and len(om) and entropy_similarity(qm, qi, om, oi) >= a.dup_sim: drop.add(int(r.row)); n_dup += 1; break
print(f"duplicates of query acquisitions (identity-group search): {n_dup}; rows dropped {len(drop):,} ({time.time()-t0:.0f}s)", flush=True)
json.dump(sorted(int(x) for x in drop), open(os.path.join(a.run, "dropped_train_rows.json"), "w"))
filt = os.path.join(a.run, "train_filtered.parquet")
if not os.path.exists(filt):
    pf = pq.ParquetFile(a.train); w = None; base = 0
    for rg in range(pf.metadata.num_row_groups):
        t = pf.read_row_group(rg); n = t.num_rows
        keep = np.array([(base + i) not in drop for i in range(n)]); t = t.filter(pa.array(keep)); base += n
        if w is None: w = pq.ParquetWriter(filt, t.schema)
        w.write_table(t)
    w.close()
sys.path.insert(0, os.path.abspath(a.code))
from casmi import build
if not os.path.exists(os.path.join(wd, "spec_off.npy")): build.build_spec_cache(train_parquet=filt, workdir=wd)
smeta = pd.read_parquet(os.path.join(wd, "spec_meta.parquet"), columns=["sid", "lib"])
assert len(smeta) == len(meta) - len(drop), (len(smeta), len(meta), len(drop))
ts = pd.read_parquet(os.path.join(wd, "train_structs.parquet"))
j = ts.merge(st, on="inchikey14", how="left"); assert j.fold_identity.notna().all() and (j.sid.values == np.arange(len(j))).all()
G = {lab: set(pd.read_csv(p).identity_group.astype(int)) for lab, p in (("hold", a.hold), ("lock", a.lock), ("rkfit", a.rkfit))}
assert not (G["hold"] & G["lock"]) and not (G["hold"] & G["rkfit"]) and not (G["lock"] & G["rkfit"])
fold = np.full(len(j), "train", dtype=object)
for lab in ("rkfit", "hold", "lock"): fold[j.identity_group.isin(G[lab]).values] = lab
out = pd.DataFrame(dict(sid=j.sid.values, fold=fold)); out[out.fold != "train"].to_parquet(os.path.join(wd, "split.parquet"), index=False)
counts = out.fold.value_counts().to_dict(); print("split", counts, flush=True)
from casmi.build import LIB_IX
panel_query_rows = int((smeta.lib == LIB_IX.get(a.panel_lib)).sum())
sid_train = set(j.sid.values[fold == "train"]); held = set(j.sid.values[fold != "train"])
qkey_sids = set(j.sid.values[j.inchikey14.isin(qkeys)])
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
gate = dict(passed=(panel_query_rows == 0 and not (held & sid_train)), recipe_variant="full_rk",
            recipe="public fold-safe recipe, no held-out fold; query acquisitions of the panel + W7 + eval_c1 removed at spectrum level (+identity-group duplicates); dev2 = hold, locked2 = lock, p1_run1 = rkfit",
            spectra_total_train_parquet=len(meta), spectra_in_cache=len(smeta), rows_dropped=len(drop), duplicate_rows_dropped=n_dup, query_pairs=len(pairs),
            panel_query_rows_in_training=panel_query_rows, holdout_training_overlap=0, query_identities_with_remaining_spectra=len({int(s) for s in smeta.sid.values if s in qkey_sids and s in sid_train}),
            split_counts=counts, dup_sim=a.dup_sim, train_parquet_sha256=sha(a.train), folds_sha256=sha(a.folds), built=time.strftime("%Y-%m-%dT%H:%M:%S"))
json.dump(gate, open(os.path.join(a.run, "check_inputs.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in gate.items() if not k.endswith("sha256")}), f"({time.time()-t0:.0f}s)")
