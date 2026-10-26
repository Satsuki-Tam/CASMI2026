#!/bin/bash
# 061 (prep, nothing evaluated): COCONUT-listed-truth TRAINING pools from identity folds 3 and 4 (fold-safe fpnet_fold3/4), disjoint from every
# existing set (incl. the reserved 3b/4b), for a ranker trained with more NP-type C2 groups (v8w recipe). p3_select_np with large n (all to
# the 'dev' half; the 'conf' half stays empty or tiny and is never used). Tables + GLACIER. Waits for the GL-heavy queue to drain.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "V8W_CONF_DONE" logs/spark_v8w_conf.log 2>/dev/null && grep -q "ICE051NP_DONE" logs/spark_ice051np.log 2>/dev/null; do sleep 120; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $(ls $B/*/p1_molecules.csv $B/*/p2_molecules.csv $B/*/v2/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv 2>/dev/null | grep -v '/np061_' | tr '\n' ' ')"
for K in 3 4; do
  $PY -X utf8 $B/p3_select_np.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold $K --n H:600,X:200,N:200 --seed 6$K --exclude $EXCL \
    --out_dir $B/np061_f${K}pool --conf_dir $B/np061_f${K}unused > $B/np061_select_f$K.log 2>&1 || { echo "NP061 FAILED select $K"; tail -3 $B/np061_select_f$K.log; exit 1; }
  grep -a -E "NP_|checks|coconut" $B/np061_select_f$K.log | cut -c1-200
  FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_np061_f${K}pool; mkdir -p $RUN/work
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/np061_f${K}pool/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
    --sets NP_H NP_X NP_N > $RUN/features.log 2>&1
  echo "== $(date +%T) fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
  for S in NP_H NP_X NP_N; do
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) fold $K gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
  done
done
echo "NP061_POOLS_DONE $(date +%T)"
