#!/bin/bash
# 056 confirmation (read once): rank_v8w vs rank_v4b on the reserved fold-3b/4b tables (gen dumps from run_tp_f*b_g).
set -u
cd ~/CASMI2026 || exit 1
until grep -q "TP3B4B_GEN_DONE" logs/spark_tp3b4b_gen.log 2>/dev/null; do sleep 60; done
grep -a "tables identical" logs/spark_tp3b4b_gen.log
grep -a "tables identical: False" logs/spark_tp3b4b_gen.log && { echo "V8W_CONF FAILED: regenerated tables differ"; exit 1; }
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; R=$HOME/CASMI2026
cd $B
for K in 3 4; do
  S5=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('train_pool_f${K}b/p2_molecules.csv').set.unique())))")
  for M in rank_v4b rank_v8w; do
    nice -n 5 $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_tp_f${K}b --gen run_tp_f${K}b_g/gen --sets $S5 --eval_csv train_pool_f${K}b/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold${K}_as_fold0 --views c1,c2 --out diag/c056_${M}_f${K}b --workers 6 > diag/c056_${M}_f${K}b.log 2>&1
    echo "== $(date +%T) fold ${K}b $M exit $?"
  done
done
echo "V8W_CONF_DONE $(date +%T)"
