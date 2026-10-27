#!/bin/bash
# 071 (reports/agent_review/071_prereg_p1_scale.md): train rank_v9a / rank_v9b on the PC (CPU only), environment check (PC gen_eval2 of
# rank_v4b on f1dev must equal the Spark diag/r047_rank_v4b_f1dev.csv), then the registered development evaluation. No CUDA.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=5 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P0=$B/rank_v4b/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
ADD_A="$B/run_tp_f3b:$B/train_pool_f3b/p2_molecules.csv:fit $B/run_tp_f4b:$B/train_pool_f4b/p2_molecules.csv:fit"
ADD_B="$ADD_A $B/run_np061_f3pool:$B/np061_f3pool/p2_molecules.csv:fit"
REP="run_tp_f3a=1 run_tp_f4a=1 run_tp_f3b=1 run_tp_f4b=1 run_np061_f3pool=1"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS $ADD_A --out $B/rank_v9a --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run $REP --params_from $P0 > $B/rank_v9a_train.log 2>&1
echo "== $(date +%T) v9a exit $? $(grep -a 'c1 share' $B/rank_v9a_train.log) sha $(sha256sum $B/rank_v9a/lambdarank.txt | cut -c1-8)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS $ADD_B --out $B/rank_v9b --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run $REP --params_from $P0 > $B/rank_v9b_train.log 2>&1
echo "== $(date +%T) v9b exit $? $(grep -a 'c1 share' $B/rank_v9b_train.log) sha $(sha256sum $B/rank_v9b/lambdarank.txt | cut -c1-8)"
cd $B
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() {  # $1 model dir, $2 tag, then gen_eval2 args
  M=$1; T=$2; shift 2
  $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 "$@" --views c1,c2 --out diag/r071_${M}_$T --workers 5 > diag/r071_${M}_$T.log 2>&1
  echo "== $(date +%T) eval $M $T exit $?"
}
ev rank_v4b f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
$PY -X utf8 -c "
import pandas as pd
a = pd.read_csv('diag/r047_rank_v4b_f1dev.csv'); b = pd.read_csv('diag/r071_rank_v4b_f1dev.csv')
x = a.merge(b, on=['set', 'view', 'molecule'], suffixes=('_s', '_p'))
d = (x.main_s - x.main_p).abs()
print('ENVCHECK rows spark', len(a), 'pc', len(b), 'merged', len(x), 'main equal', int((d < 1e-9).sum()), 'max abs diff', float(d.max()))
import sys; sys.exit(0 if len(x) == len(a) == len(b) and float(d.max()) < 1e-9 else 3)
" || { echo "ENVCHECK FAILED -> stop"; exit 3; }
for M in rank_v9a rank_v9b; do
  ev $M f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
  ev $M f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
  ev $M panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
  ev $M p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
done
for M in rank_v4b rank_v8w rank_v9a rank_v9b; do
  for K in 1 2; do ev $M np053f${K}dev --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $FS; done
done
echo "P1SCALE071_DONE $(date +%T)"
