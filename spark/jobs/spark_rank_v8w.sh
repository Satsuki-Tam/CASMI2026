#!/bin/bash
# 056: rank_v8a weight controls (v8w: pool C1 x1; v8n: pool without G rows), fixed params, dev evaluation like 047.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; P0=$B/rank_v4b/rank_results.json
for K in 3 4; do $PY -c "import pandas as pd; d = pd.read_csv('$B/train_pool_f${K}a/p2_molecules.csv'); d = d[d.set != 'G_tims_crosslib']; import os; os.makedirs('$B/train_pool_f${K}a_np', exist_ok=True); d.to_csv('$B/train_pool_f${K}a_np/p2_molecules.csv', index=False); print('f${K}a np', len(d))"; done
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
POOLS_NP="$B/run_tp_f3a:$B/train_pool_f3a_np/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a_np/p2_molecules.csv:fit"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS --out $B/rank_v8w --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 --params_from $P0 > $B/rank_v8w_train.log 2>&1; echo "== $(date +%T) v8w exit $? $(grep -a 'c1 share' $B/rank_v8w_train.log)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS_NP --out $B/rank_v8n --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 > $B/rank_v8n_train.log 2>&1; echo "== $(date +%T) v8n exit $? $(grep -a 'c1 share' $B/rank_v8n_train.log)"
cd $B
for M in rank_v8w rank_v8n; do
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_f1dev --gen run_f1dev/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set_f1/p2_molecules.csv --fold_safe data/external/fpnet_fold1_as_fold0 --views c1,c2 --out diag/r056_${M}_f1dev --workers 6 > diag/r056_${M}_f1dev.log 2>&1 &
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_f2dev --gen run_f2dev/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set_f2/p2_molecules.csv --fold_safe data/external/fpnet_fold2_as_fold0 --views c1,c2 --out diag/r056_${M}_f2dev --workers 6 > diag/r056_${M}_f2dev.log 2>&1 &
  wait
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe data/external/fpnet_fulleval_as_fold0 --views c1,c2 --out diag/r056_${M}_p2dev --workers 6 > diag/r056_${M}_p2dev.log 2>&1 &
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe data/external/fpnet_fulleval_as_fold0 --views c1,c2 --out diag/r056_${M}_panel --workers 6 > diag/r056_${M}_panel.log 2>&1 &
  wait
done
echo "RANK_V8W_DONE $(date +%T)"
