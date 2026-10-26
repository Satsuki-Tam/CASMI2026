#!/bin/bash
# 2026-10-26 (overnight, low priority): ranker TRAINING pools from identity folds 3 and 4 (stratified like dev2, 200 per stratum x dev/locked
# halves = up to 2,000 molecules per fold), feature tables with the matching fold-safe FPNet (unseen) + GLACIER. Not used for evaluation.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $B/eval_set/p1_molecules.csv $B/eval_c1/p1_molecules.csv $B/locked_eval/p1_molecules.csv $B/eval_set2/v2/p2_molecules.csv $B/locked_eval2/v2/p2_molecules.csv $B/eval_set2/fit_pool/p2_molecules.csv $B/eval_set2/fit_pool_overflow/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv $B/eval_set3/p2_molecules.csv $B/eval_conf_fit/p2_molecules.csv $B/eval_conf_fit2/p2_molecules.csv $B/eval_set_f1/p2_molecules.csv $B/locked_eval_f1/p2_molecules.csv $B/eval_set_f2/p2_molecules.csv $B/locked_eval_f2/p2_molecules.csv"
for f in $EXCL; do [ -s $f ] || { echo "TRAINPOOL FAILED: missing exclusion $f"; exit 1; }; done
for K in 3 4; do
  FD=data/external/fpnet_fold${K}_as_fold0; mkdir -p $FD
  for f in data/external/fold_safe_fpnet/*; do bn=$(basename $f); [ "$bn" = fpnet_fold0.pt ] && continue; [ -e $FD/$bn ] || ln -s $(realpath $f) $FD/$bn; done
  [ -e $FD/fpnet_fold0.pt ] || ln -s $(realpath data/external/fold_safe_fpnet/fpnet_fold${K}.pt) $FD/fpnet_fold0.pt
  echo "== $(date +%T) fold $K FPNet $(sha256sum $FD/fpnet_fold0.pt | cut -c1-16)"
  nice -n 10 $PY -X utf8 $B/p2_select_v2.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds --exclude $EXCL --n 200 --seed 2$K --fold $K \
    --out_dir $B/train_pool_f${K}a --locked_dir $B/train_pool_f${K}b > /tmp/tp_f${K}.log 2>&1 || { echo "TRAINPOOL FAILED: select fold $K"; tail -3 /tmp/tp_f${K}.log; continue; }
  tail -2 /tmp/tp_f${K}.log
done
for K in 3 4; do
  FD=data/external/fpnet_fold${K}_as_fold0
  for H in a b; do
    E=$B/train_pool_f${K}${H}/p2_molecules.csv; [ -s $E ] || continue
    RUN=$B/run_tp_f${K}${H}; mkdir -p $RUN/work
    SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$E').set.unique())))")
    nice -n 10 $PY -X utf8 $B/b1_features.py --eval_csv $E --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
      --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FD --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 --sets $SETS > $RUN/features.log 2>&1
    echo "== $(date +%T) features $RUN exit $? $(grep -a '^saved' $RUN/features.log | wc -l) sets"
    for S in $SETS; do
      nice -n 10 .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
      echo "== $(date +%T) gl $RUN $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
    done
  done
done
echo "TRAINPOOL_DONE $(date +%T)"
