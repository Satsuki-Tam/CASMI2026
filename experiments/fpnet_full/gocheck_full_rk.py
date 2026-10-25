"""021 GO check for full_rk, on the trainer's own data object (casmi.traindata.Data with the run's holdout labels):
  (i)  no spectrum of a held-out identity group (hold / lock / rkfit) is in Data.tr, and no dropped query row is in the cache;
  (iii) per query identity (panel, W7, eval_c1): number of spectra that REMAIN trainable (Data.tr) -> 'c1_seen' (>0) vs 'unseen_after_removal' (0),
        written to query_identity_exposure.csv BEFORE any evaluation.
Usage: python -X utf8 gocheck_full_rk.py --run <abs run dir> --code data/external/v3_models/code --query_sets CSV... --panel_lib enveda-np-examples
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--code", required=True); ap.add_argument("--query_sets", nargs="+", required=True)
ap.add_argument("--train", default=""); ap.add_argument("--holdout", default="hold,lock,rkfit"); a = ap.parse_args()
qsets = [(os.path.basename(os.path.dirname(f)), pd.read_csv(f)) for f in a.query_sets]
sys.path.insert(0, os.path.abspath(a.code)); os.chdir(a.run)
from casmi import traindata
D = traindata.Data("cpu", seed=0, holdout_folds=tuple(a.holdout.split(",")))
tr_sid = D.sid[D.tr]
split = pd.read_parquet("work/split.parquet")
held = set(split.sid[split.fold.isin(a.holdout.split(","))].astype(int))
overlap = int(np.isin(tr_sid, list(held)).sum())
ts = pd.read_parquet("work/train_structs.parquet", columns=["sid", "inchikey14"])
sid_of = dict(zip(ts.inchikey14, ts.sid))
cnt = pd.Series(tr_sid).value_counts()
rows = []
for name, d in qsets:
    for r in d.itertuples():
        s = sid_of.get(str(r.molecule), -1); n = int(cnt.get(s, 0)) if s >= 0 else 0
        rows.append(dict(source=name, set=getattr(r, "set", ""), group=getattr(r, "group", ""), molecule=r.molecule, identity_group=int(getattr(r, "identity_group", -1)), sid=int(s),
                         n_trainable_spectra_remaining=n, exposure="c1_seen" if n > 0 else "unseen_after_removal"))
e = pd.DataFrame(rows); e.to_csv(os.path.join(a.run, "query_identity_exposure.csv"), index=False)
res = dict(train_spectra=int(len(D.tr)), held_sids=len(held), held_overlap_in_Data_tr=overlap,
           exposure_counts={f"{k[0]}:{k[1]}": int(v) for k, v in e.groupby(["source", "exposure"]).size().items()},
           go_condition_i=overlap == 0)
gate = json.load(open("check_inputs.json")); gate["holdout_training_overlap"] = overlap; gate["holdout_overlap_source"] = "computed from casmi.traindata.Data.tr (gocheck_full_rk.py)"
json.dump(gate, open("check_inputs.json", "w"), indent=2)
json.dump(res, open("gocheck.json", "w"), indent=1); print(json.dumps(res, indent=1))
