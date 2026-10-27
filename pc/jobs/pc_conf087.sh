#!/bin/bash
# 087 confirmation on the reserved 083 set (087_prereg_v8w7a.md amendment): gen_eval2m --v7f, rank_v7a_pc vs rank_v8w7a. CPU only.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
$PY -X utf8 gen_eval2m.py --model rank_v7a_pc/lambdarank.txt,rank_v8w7a/lambdarank.txt --v7f --parents 0 --run run_np083_f4conf --gen run_np083_f4conf/gen --sets NP_H NP_X NP_N \
  --eval_csv np061_f4pool/p2_molecules.csv --fold_safe data/external/fpnet_fold4_as_fold0 --views c1,c2 --out diag/c087_rank_v7a_pc,diag/c087_rank_v8w7a --workers 6 > diag/c087.log 2>&1
echo "== $(date +%T) conf087 exit $?"
echo "CONF087_DONE $(date +%T)"
