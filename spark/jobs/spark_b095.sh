#!/bin/bash
# 095 (095_prereg_bspec.md): B-group specialist ranker (b1_rank_train --restrict B) and the B-position-preserving reorder evaluated with gen_eval2fd --v7f --bmodel
# (base = rank_v7a, the v7f main) on the development tables. Spark, CPU only.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=~/CASMI2026/.venv/bin/python; P7=$B/rank_params_v7a/rank_results.json
$PY -c "
import pandas as pd
parts = ['$B/diag/analog_tr_v3all.parquet'] + ['$B/diag/analog_tr_%s.parquet' % t for t in ('tpf3a', 'tpf4a', 'tpf3b', 'tpf4b', 'np061f3')]
A = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True); k = ['set', 'view', 'molecule']
assert A.groupby(k).ngroups == sum(pd.read_parquet(p).groupby(k).ngroups for p in parts); A.to_parquet('$B/diag/analog_tr_b095.parquet'); print('analog', A.shape)"
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit $B/run_tp_f3b:$B/train_pool_f3b/p2_molecules.csv:fit $B/run_tp_f4b:$B/train_pool_f4b/p2_molecules.csv:fit"
NPP="$B/run_np061_f3pool:$B/np061_f3pool/p2_molecules.csv:fit"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS $NPP --out $B/rank_b095 --feats v2_noice_ana --drop lib_nref in_train --c1_repeat 3 --restrict B \
  --params_from $P7 --analog_parquet $B/diag/analog_tr_b095.parquet > $B/rank_b095_train.log 2>&1
echo "== $(date +%T) train b095 exit $? $(grep -a 'fit groups\|^rows' $B/rank_b095_train.log | tr '\n' ' ' | cut -c1-200) sha $(sha256sum $B/rank_b095/lambdarank.txt | cut -c1-8)"
cd $B
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model rank_v7a/lambdarank.txt --v7f --bmodel rank_b095/lambdarank.txt --parents 0 "$@" --views c1,c2 --out diag/r095_$T --workers 5 > diag/r095_$T.log 2>&1
  echo "== $(date +%T) eval095 $T exit $?"; }
( ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
  ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
  ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE ) &
( ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
  ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
  ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE ) &
wait
echo "B095_DONE $(date +%T)"
