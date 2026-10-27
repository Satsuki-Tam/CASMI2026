#!/bin/bash
# 087 (087_prereg_v8w7a.md): candidate rank_v8w7a = rank_v7a_pc recipe (v2_noice_ana - lib_nref - in_train, C1 x3, params rank_params_v7a: 31 leaves, lr .03, 600 rounds)
# + the v8w pools (run_tp_f3a / f4a, fit, C1 x1, analog features analog_tr_tpf3a/f4a). CPU only.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P7=$B/rank_params_v7a/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS --out $B/rank_v8w7a --feats v2_noice_ana --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 \
  --params_from $P7 --analog_parquet $B/diag/analog_tr_v8w.parquet > $B/rank_v8w7a_train.log 2>&1
echo "== $(date +%T) v8w7a exit $? $(grep -a 'c1 share' $B/rank_v8w7a_train.log | tail -1) sha $(sha256sum $B/rank_v8w7a/lambdarank.txt | cut -c1-8)"
echo "RANK087_DONE $(date +%T)"
