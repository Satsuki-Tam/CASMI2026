#!/bin/bash
# 047 (pre-registered): rank_v4b recipe + fold-3a/4a pools as fit, fixed params (--params_from rank_v4b); reproduction rank_v4b_r; development
# evaluation of the registered main (anaw0.5) with each ranker on fold-1 dev, fold-2 dev, dev2 v2 and the panel (no generation: --parents 0).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; P0=$B/rank_v4b/rank_results.json
until grep -q "run_tp_f4a G_tims_crosslib" logs/spark_trainpool_f34.log 2>/dev/null; do sleep 60; done
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 --out $B/rank_v4b_r --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 > $B/rank_v4b_r_train.log 2>&1; echo "== $(date +%T) v4b_r exit $?"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS --out $B/rank_v8a --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 > $B/rank_v8a_train.log 2>&1; echo "== $(date +%T) v8a exit $?"
grep -a -i "fit\|groups\|rows" $B/rank_v8a_train.log | head -20
cmp -s $B/rank_v4b_r/lambdarank.txt $B/rank_v4b/lambdarank.txt && echo "v4b_r model file IDENTICAL to rank_v4b" || echo "v4b_r model file differs from rank_v4b"
cd $B
for M in rank_v4b rank_v8a; do
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_f1dev --gen run_f1dev/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set_f1/p2_molecules.csv --fold_safe data/external/fpnet_fold1_as_fold0 --views c1,c2 --out diag/r047_${M}_f1dev --workers 8 > diag/r047_${M}_f1dev.log 2>&1 &
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_f2dev --gen run_f2dev/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set_f2/p2_molecules.csv --fold_safe data/external/fpnet_fold2_as_fold0 --views c1,c2 --out diag/r047_${M}_f2dev --workers 8 > diag/r047_${M}_f2dev.log 2>&1 &
  wait
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe data/external/fpnet_fulleval_as_fold0 --views c1,c2 --out diag/r047_${M}_p2dev --workers 8 > diag/r047_${M}_p2dev.log 2>&1 &
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe data/external/fpnet_fulleval_as_fold0 --views c1,c2 --out diag/r047_${M}_panel --workers 8 > diag/r047_${M}_panel.log 2>&1 &
  wait
done
echo "RANK_V8A_DONE $(date +%T)"
