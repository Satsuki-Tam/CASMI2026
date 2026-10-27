#!/bin/bash
# 086 EAc diagnostic (086_prereg_eac.md): gen_eval2pv (v7f main) on 5 dev tables + gen_eval2p (0.379 main) on 053 dev, with --refcmp.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { SCR=$1; MOD=$2; T=$3; shift 3
  $PY -X utf8 $SCR --model $MOD/lambdarank.txt --refcmp --parents 0 "$@" --views c1,c2 --out diag/e086_${T} --workers 4 > diag/e086_${T}.log 2>&1
  echo "== $(date +%T) eac086 $T exit $?"; }
ev gen_eval2pv.py rank_v7a v7f_np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev gen_eval2pv.py rank_v7a v7f_np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev gen_eval2pv.py rank_v7a v7f_panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev gen_eval2pv.py rank_v7a v7f_f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev gen_eval2pv.py rank_v7a v7f_f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
ev gen_eval2p.py rank_v4b v4b_np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev gen_eval2p.py rank_v4b v4b_np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
echo "EAC086_DONE $(date +%T)"
