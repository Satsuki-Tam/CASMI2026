#!/bin/bash
# 071 amendment (Codex 070): control = rank_v8w_pc (PC re-training of v8w, already trained), learning-curve arm rank_v9h = v8w + tp_f3b only.
# Waits for the first 071 job; CPU only.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "P1SCALE071_DONE\|ENVCHECK FAILED" logs/pc_p1scale071.log 2>/dev/null; do sleep 60; done
grep -q "ENVCHECK FAILED" logs/pc_p1scale071.log && { echo "071b: envcheck failed upstream -> stop"; exit 3; }
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=5 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P0=$B/rank_v4b/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
ADD_H="$B/run_tp_f3b:$B/train_pool_f3b/p2_molecules.csv:fit"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS $ADD_H --out $B/rank_v9h --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 run_tp_f3b=1 --params_from $P0 > $B/rank_v9h_train.log 2>&1
echo "== $(date +%T) v9h exit $? $(grep -a 'c1 share' $B/rank_v9h_train.log) sha $(sha256sum $B/rank_v9h/lambdarank.txt | cut -c1-8)"
cd $B
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { M=$1; T=$2; shift 2
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 "$@" --views c1,c2 --out diag/r071_${M}_$T --workers 5 > diag/r071_${M}_$T.log 2>&1
  echo "== $(date +%T) eval $M $T exit $?"; }
for M in rank_v8w_pc rank_v9h; do
  ev $M f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
  ev $M f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
  ev $M panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
  ev $M p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
  for K in 1 2; do ev $M np053f${K}dev --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $FS; done
done
echo "P1SCALE071B_DONE $(date +%T)"
