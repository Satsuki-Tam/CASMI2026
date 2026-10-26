#!/bin/bash
# 053: NP-truth evaluation sets (truth = COCONUT structure, MSG-free, fold-safe) for folds 1 and 2: selection (dev + closed conf), then
# feature tables of the DEV halves with the fold's public FPNet (+ --dump_gen) and GLACIER. Nothing is evaluated here.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $(ls $B/*/p1_molecules.csv $B/*/p2_molecules.csv $B/*/v2/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv 2>/dev/null | grep -v '/np053_' | tr '\n' ' ')"
echo "== $(date +%T) exclusions: $(echo $EXCL | wc -w) files; selector $(sha256sum $B/p3_select_np.py | cut -c1-12)"
for K in 1 2; do
  nice -n 10 $PY -X utf8 $B/p3_select_np.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold $K --n H:200,X:60,N:60 --seed 3$K --exclude $EXCL \
    --out_dir $B/np053_f${K}dev --conf_dir $B/np053_f${K}conf > $B/np053_select_f$K.log 2>&1 || { echo "NP053 FAILED: select fold $K"; tail -5 $B/np053_select_f$K.log; exit 1; }
  grep -a -E "NP_|checks|coconut_truth" $B/np053_select_f$K.log | cut -c1-300
done
for K in 1 2; do
  FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_np053_f${K}dev; mkdir -p $RUN/work
  nice -n 10 $PY -X utf8 $B/b1_features.py --eval_csv $B/np053_f${K}dev/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets NP_H NP_X NP_N > $RUN/features.log 2>&1
  echo "== $(date +%T) fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-220)"
  for S in NP_H NP_X NP_N; do
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) fold $K gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-100)"
  done
done
echo "NP053_SETS_DONE $(date +%T)"
