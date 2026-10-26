#!/bin/bash
# 056 confirmation prerequisite: gen dumps (query logits) for the reserved fold-3b/4b tables (the existing run_tp_f3b/f4b were built without
# --dump_gen); same inputs and FPNet as the original tables -> tables must be identical (checked), only gen/ is used. Nothing is evaluated here.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
for K in 3 4; do
  FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_tp_f${K}b_g; mkdir -p $RUN
  SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/train_pool_f${K}b/p2_molecules.csv').set.unique())))")
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/train_pool_f${K}b/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1
  echo "== $(date +%T) fold ${K}b gen exit $?"
  $PY - <<PY
import pandas as pd
for s in "$SETS".split():
    a = pd.read_parquet("$B/run_tp_f${K}b/b1_features_%s.parquet" % s); b = pd.read_parquet("$B/run_tp_f${K}b_g/b1_features_%s.parquet" % s)
    same = a.shape == b.shape and all(a[c].astype(str).tolist() == b[c].astype(str).tolist() for c in ("molecule", "smiles", "fp"))
    print("fold ${K}b", s, "tables identical:", same)
PY
done
echo "TP3B4B_GEN_DONE $(date +%T)"
