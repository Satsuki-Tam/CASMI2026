#!/bin/bash
# 095 one-time confirmation on np096_conf095 (NP_H 400) after the 096 tables are complete. Spark, CPU.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "TAB096_DONE" logs/spark_tab096.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
cd experiments/b1_baseline; PY=~/CASMI2026/.venv/bin/python
$PY -X utf8 gen_eval2fd.py --model rank_v7a/lambdarank.txt --v7f --bmodel rank_b095/lambdarank.txt --parents 0 --run run_np096_f0conf --gen run_np096_f0conf/gen --sets NP_H \
  --eval_csv np096_conf095/p2_molecules.csv --fold_safe data/external/fold_safe_fpnet --views c1,c2 --out diag/c095_np096 --workers 12 > diag/c095_np096.log 2>&1
echo "== $(date +%T) conf095 exit $?"
$PY -X utf8 x095c_summary.py > diag/x095c.log 2>&1; tail -4 diag/x095c.log
echo "CONF095_DONE $(date +%T)"
