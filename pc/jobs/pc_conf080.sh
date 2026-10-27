#!/bin/bash
# 080 confirmation (run ONLY after the 080 dev gate PASSED and the v7f-alone parity PASSED): opens the 053 NP_H / NP_N conf tables (fold 1 / 2,
# never evaluated) once with gen_eval2pv (v7f main + fixed variants; only ea0.5w1 is read).
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; FS=data/external/fold_safe_fpnet
for K in 1 2; do
  $PY -X utf8 gen_eval2pv.py --model rank_v7a/lambdarank.txt --parents 0 --run run_np053_f${K}conf --gen run_np053_f${K}conf/gen --sets NP_H NP_X NP_N \
    --eval_csv np053_f${K}conf/p2_molecules.csv --fold_safe $FS --views c1,c2 --out diag/c080_np053f${K}conf --workers 6 > diag/c080_np053f${K}conf.log 2>&1
  echo "== $(date +%T) conf080 f$K exit $?"
done
echo "CONF080_DONE $(date +%T)"
