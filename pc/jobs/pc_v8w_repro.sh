#!/bin/bash
# 071 prep: reproduce rank_v8w on the PC (same inputs / flags as spark_rank_v8w.sh) to check that PC training matches the Spark model
# (b8706359) before any new ranker is trained here. CPU only.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P0=$B/rank_v4b/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS --out $B/rank_v8w_pc --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 --params_from $P0 > $B/rank_v8w_pc_train.log 2>&1
echo "== $(date +%T) v8w_pc exit $? $(grep -a 'c1 share' $B/rank_v8w_pc_train.log)"
echo "spark $(sha256sum $B/rank_v8w/lambdarank.txt | cut -c1-8)  pc $(sha256sum $B/rank_v8w_pc/lambdarank.txt | cut -c1-8)"
echo "V8W_REPRO_DONE $(date +%T)"
