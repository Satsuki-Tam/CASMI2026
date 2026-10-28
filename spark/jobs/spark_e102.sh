#!/bin/bash
# 102 (102_prereg_elite.md): E-lite training (e1b = pointwise binary, e1r = lambdarank control; same rows as v8w7a, features e1, E window) and one
# gen_eval2fd --v7f --emodel pass per development table (main = rank_v8w7a). Results are NOT read until the registration is final.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=~/CASMI2026/.venv/bin/python
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
COMMON="--runs $RUNS0 $POOLS --feats e1 --restrict E --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 --analog_parquet $B/diag/analog_tr_v8w.parquet"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12) feats $(sha256sum $B/b1_rankfeats.py | cut -c1-12) ekeys $(sha256sum $B/diag/e_window_keys.parquet | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py $COMMON --pointwise --params_from $B/rank_params_e1b/rank_results.json --out $B/rank_e1b > $B/rank_e1b_train.log 2>&1 &
$PY -X utf8 $B/b1_rank_train.py $COMMON --params_from $B/rank_params_v7a/rank_results.json --out $B/rank_e1r > $B/rank_e1r_train.log 2>&1 &
wait
echo "== $(date +%T) trained e1b $(sha256sum $B/rank_e1b/lambdarank.txt | cut -c1-8) e1r $(sha256sum $B/rank_e1r/lambdarank.txt | cut -c1-8)"
cd $B || exit 1
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
EM=rank_e1b/lambdarank.txt,rank_e1r/lambdarank.txt
ev() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --emodel $EM --rrf_k 10 "$@" --views c1,c2 --out diag/r102_$T --workers 2 > diag/r102_$T.log 2>&1
  echo "== $(date +%T) eval102 $T exit $?"; }
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS &
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS &
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE &
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS &
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS &
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE &
wait
echo "E102_DONE $(date +%T)"
