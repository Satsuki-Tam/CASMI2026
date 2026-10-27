#!/bin/bash
# 099 (099_prereg_tgen.md): transductive generation on the fold-safe panel table. A = baseline + top-25 dump; B = test-side parents only; C = 10 train-analog parents (gt3 setup); D = C + test-side parents.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "PANELF0_DONE" logs/spark_panelf0.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
cd experiments/b1_baseline; PY=~/CASMI2026/.venv/bin/python
COMMON="--model rank_v7a/lambdarank.txt --v7f --run run_panel_f0 --gen run_panel_f0/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe data/external/fold_safe_fpnet --views c1,c2,c3 --workers 16"
$PY -X utf8 gen_eval2fd.py $COMMON --parents 0 --dump_top diag/top_panelf0.parquet --out diag/t099_A > diag/t099_A.log 2>&1; echo "== $(date +%T) A exit $?"
$PY -X utf8 gen_eval2fd.py $COMMON --parents 0 --tparents diag/top_panelf0.parquet --tparents_mode only --out diag/t099_B > diag/t099_B.log 2>&1; echo "== $(date +%T) B exit $?"
$PY -X utf8 gen_eval2fd.py $COMMON --parents 10 --out diag/t099_C > diag/t099_C.log 2>&1; echo "== $(date +%T) C exit $?"
$PY -X utf8 gen_eval2fd.py $COMMON --parents 10 --tparents diag/top_panelf0.parquet --tparents_mode add --out diag/t099_D > diag/t099_D.log 2>&1; echo "== $(date +%T) D exit $?"
echo "TGEN099_DONE $(date +%T)"
