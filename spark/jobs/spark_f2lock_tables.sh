#!/bin/bash
# 045: fold-2 LOCKED tables (fpnet_fold2, --dump_gen) + GLACIER for the stage-3 confirmation (rule-independent; no rule is evaluated here).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F2=data/external/fpnet_fold2_as_fold0; RUN=$B/run_f2lock
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/locked_eval_f2/p2_molecules.csv').set.unique())))")
mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/locked_eval_f2/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F2 --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | wc -l) sets"
for S in $SETS; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-110)"
done
echo "F2LOCK_TABLES_DONE $(date +%T)"
