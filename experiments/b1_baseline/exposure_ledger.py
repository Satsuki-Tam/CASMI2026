"""FPNet training-exposure ledgers per checkpoint (Codex 027/028 hypothesis 1).

For a checkpoint, a training structure is a POSITIVE when at least one of its spectra entered the trainer's training set, reproducing
casmi.traindata.Data: spectra of the run's spectrum cache (work/spec_meta.parquet, sid per spectrum) whose structure is not in a held-out
fold of the run's split (work/split.parquet) and whose key is in the v2 pool. NEGPOOL marks keys of the v2 pool (the domain of the
ranking-loss decoy sampler, which is not filtered by the split). Keys are the pool / official scorer keys (train_structs.key).
Output: <out_dir>/ledger_<name>.parquet with columns key, fp_pos, negpool (one row per key of train_structs or the pool).
Usage: python -X utf8 exposure_ledger.py --out_dir experiments/b1_baseline/ledgers
"""
import argparse, json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq

ap = argparse.ArgumentParser(); ap.add_argument("--out_dir", default="experiments/b1_baseline/ledgers")
ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap.add_argument("--pool", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/pool_meta.parquet")
a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
ts = pq.read_table(a.structs, columns=["sid", "key"]).to_pandas(); ts["key"] = ts.key.astype(str)
assert (ts.sid.to_numpy() == np.arange(len(ts))).all(), "sid must equal the row index of train_structs"
pool_keys = set(pq.read_table(a.pool, columns=["key"]).to_pandas().key.astype(str))
in_pool = ts.key.isin(pool_keys).to_numpy()
RUNS = {   # name: (split parquet, held-out fold labels, spectrum cache meta or None = every structure with spectra in the public cache)
    "fold0": ("data/external/fold_safe_fpnet/split.parquet", {"hold", "np"}, None),
    "full_rk": ("experiments/fpnet_full/full_rk/work/split.parquet", {"hold", "lock", "rkfit"}, "experiments/fpnet_full/full_rk/work/spec_meta.parquet"),
    "full_eval": ("experiments/fpnet_full/full_eval/work/split.parquet", {"hold", "lock"}, "experiments/fpnet_full/full_eval/work/spec_meta.parquet"),
}
summary = {}
for name, (split_p, held, meta_p) in RUNS.items():
    sp = pd.read_parquet(split_p, columns=["sid", "fold"])
    assert set(sp.fold.unique()) <= held | {"train"}, (name, sorted(sp.fold.unique()))
    held_sids = set(sp.loc[sp.fold.isin(held), "sid"].astype(int))
    if meta_p:
        with_spec = np.zeros(len(ts), bool); with_spec[np.unique(pq.read_table(meta_p, columns=["sid"]).column("sid").to_numpy())] = True
    else:
        with_spec = np.ones(len(ts), bool)
    pos = with_spec & in_pool & ~np.isin(ts.sid.to_numpy(), list(held_sids))
    pos_keys = set(ts.key.to_numpy()[pos])
    keys = sorted(set(ts.key) | pool_keys)
    L = pd.DataFrame({"key": keys}); L["fp_pos"] = L.key.isin(pos_keys); L["negpool"] = L.key.isin(pool_keys)
    L.to_parquet(os.path.join(a.out_dir, f"ledger_{name}.parquet"), index=False)
    summary[name] = dict(held_sids=len(held_sids), structures_with_spectra=int(with_spec.sum()), positive_structures=int(pos.sum()), positive_keys=len(pos_keys),
                         train_keys=int(ts.key.nunique()), pool_keys=len(pool_keys))
    print(name, summary[name], flush=True)
json.dump(summary, open(os.path.join(a.out_dir, "ledger_summary.json"), "w"), indent=1)
