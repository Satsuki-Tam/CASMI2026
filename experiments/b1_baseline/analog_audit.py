"""Codex 035 pre-submission identity audit of the analog channel (FROZEN module experiments/b1_ana035/b1_analog.py).

For every C2 molecule of the given evaluation sets, the analogs are recomputed with the evaluator's masks and checked:
  (1) no returned analog key is in the exclusion set (truth key, raw keys of the query molecule, identity-group keys);
  (2) no returned key belongs to a query spectrum's identity (the query rows are excluded at the representative level);
  (3) for a sample of the returned keys, the official scorer identity of the key's SMILES (src/metric) equals the key.
Usage: python -X utf8 analog_audit.py --runs EVAL_CSV:SET1,SET2 ... --out diag/analog_audit.md
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments", "b1_ana035"))   # frozen b1_analog / b1_common first
import b1_analog as BA  # noqa: E402
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "src")); import metric  # noqa: E402
ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--out", required=True); ap.add_argument("--sample_keys", type=int, default=1500)
ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
a = ap.parse_args(); T0 = time.time()
print("frozen b1_analog:", BA.__file__, flush=True)
S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=print)
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
_idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
n_mol = n_hit_excl = n_hit_query = 0; returned = set()
for spec in a.runs:
    csv, sets = spec.split(":"); ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev["molecule"].astype(str)
    for r in ev[ev.set.isin(sets.split(","))].itertuples(index=False):
        mid, lib, tk = str(r.molecule), r.lib, str(r.scorer_key)
        q = select_queries(sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT), 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        qspec = []
        for x in q:
            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
            mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
        raw = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
        drop = raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set()))
        an = store.analogs(qspec, query_rows=q, drop_keys=drop)
        keys = {k for k, _ in an}; n_mol += 1
        n_hit_excl += len(keys & drop); n_hit_query += len(keys & {key_of_row[x] for x in q if key_of_row[x] is not None}); returned |= keys
rng = np.random.default_rng(0); sample = sorted(returned); sample = [sample[i] for i in rng.choice(len(sample), min(a.sample_keys, len(sample)), replace=False)]
ok = bad = miss = 0; bad_ex = []
for k in sample:
    smi = KEY_SMI.get(k)
    if smi is None: miss += 1; continue
    try: ck = metric.canonicalize_smiles_to_ik14(smi)
    except Exception: ck = None
    if ck == k: ok += 1
    else: bad += 1; bad_ex.append((k, ck))
L = ["# Analog identity audit (Codex 035, frozen b1_analog)", "", f"C2 molecules audited: {n_mol}; returned analog keys (unique): {len(returned):,}",
     f"(1) returned keys in the exclusion set: **{n_hit_excl}**", f"(2) returned keys equal to a query spectrum's identity: **{n_hit_query}**",
     f"(3) official identity of the key's SMILES == key: {ok} / {ok + bad} sampled (missing SMILES {miss}); mismatches {bad}: {bad_ex[:10]}", f"seconds {time.time() - T0:.0f}"]
open(os.path.join(HERE, a.out), "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))
