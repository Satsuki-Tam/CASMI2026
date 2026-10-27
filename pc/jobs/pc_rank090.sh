#!/bin/bash
# 090 (popularity-reliance variants; registration before evaluation): rank_v7a_pc recipe (v3 runs, analog_tr_v3all, C1 x3, rank_params_v7a) with the
# popularity features removed: np4 = - pop_public lsid lpmid lsynonyms; np7 = also - np_bit src_bit lotus. CPU only.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P7=$B/rank_params_v7a/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 --out $B/rank_v7a_np4 --feats v2_noice_ana --drop lib_nref in_train pop_public lsid lpmid lsynonyms --c1_repeat 3 \
  --params_from $P7 --analog_parquet $B/diag/analog_tr_v3all.parquet > $B/rank_v7a_np4_train.log 2>&1
echo "== $(date +%T) np4 exit $? feats $(grep -a '^features' $B/rank_v7a_np4_train.log | head -1 | cut -c1-60) sha $(sha256sum $B/rank_v7a_np4/lambdarank.txt | cut -c1-8)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 --out $B/rank_v7a_np7 --feats v2_noice_ana --drop lib_nref in_train pop_public lsid lpmid lsynonyms np_bit src_bit lotus --c1_repeat 3 \
  --params_from $P7 --analog_parquet $B/diag/analog_tr_v3all.parquet > $B/rank_v7a_np7_train.log 2>&1
echo "== $(date +%T) np7 exit $? feats $(grep -a '^features' $B/rank_v7a_np7_train.log | head -1 | cut -c1-60) sha $(sha256sum $B/rank_v7a_np7/lambdarank.txt | cut -c1-8)"
echo "RANK090_DONE $(date +%T)"
