#!/bin/bash
# 096 reservation (selection only, counts printed; no table is evaluated): new COCONUT-truth confirmation candidates from identity folds 0 and 3,
# disjoint (identity group) from EVERY existing selection CSV under experiments/b1_baseline (incl. 073 = np061_f*unused, 083 = np061_f4pool) and the panel.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $(ls $B/*/p1_molecules.csv $B/*/p2_molecules.csv $B/*/v2/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv 2>/dev/null | grep -v '/np096_' | tr '\n' ' ')"
echo "exclusions: $(echo $EXCL | wc -w) files"
for K in 0 3; do
  $PY -X utf8 $B/p3_select_np.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold $K --n H:600,X:0,N:200 --seed 96$K --exclude $EXCL \
    --out_dir $B/np096_f${K}conf --conf_dir $B/np096_f${K}spare > $B/np096_select_f$K.log 2>&1 || { echo "SELECT FAILED $K"; tail -3 $B/np096_select_f$K.log; }
  echo "== fold $K"; grep -a -E "^\{|NP_|dev |conf " $B/np096_select_f$K.log | cut -c1-260
done
echo "SEL096_DONE $(date +%T)"
