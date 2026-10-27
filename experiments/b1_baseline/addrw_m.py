"""091: copy of each fp_mean_score parquet with fprw_m (window-rank transfer for the PC-recomputed merged fp_m, same rule as fprw_s) -> <name>_m.parquet."""
import sys
import numpy as np, pandas as pd
for p in sys.argv[1:]:
    F = pd.read_parquet(p); rw = np.full(len(F), np.nan)
    for m, idx in F.groupby(["set", "molecule"]).indices.items():
        v = F.fp_m.values[idx]; ranks = np.sort(F.fp_rank_window.values[idx].astype(float))
        o = np.argsort(-np.nan_to_num(v, nan=-1e18), kind="stable"); rr_ = np.empty(len(idx)); rr_[o] = ranks; rw[idx] = rr_
    F["fprw_m"] = rw; q = p.replace(".parquet", "_m.parquet"); F.to_parquet(q); print(q, "fprw_m added", len(F))
