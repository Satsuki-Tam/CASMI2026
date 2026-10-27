#!/bin/bash
# 061 fold-4 pool on the LOCAL PC (the Spark run stopped after the fold-3 pool): tables + GLACIER for np061_f4pool (selection already made on
# the Spark with seed 64, p2_molecules.csv copied). Same arguments as spark_np061_pools.sh. CUDA: run only when no other CUDA job is active.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; IPY=/c/kaggle/CASMI/.venv-ice/Scripts/python.exe
K=4; FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_np061_f${K}pool; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/np061_f${K}pool/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --sets NP_H NP_X NP_N > $RUN/features.log 2>&1
echo "== $(date +%T) fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
for S in NP_H NP_X NP_N; do
  $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) fold $K gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
done
echo "NP061F4_DONE $(date +%T)"
