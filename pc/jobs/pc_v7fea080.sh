#!/bin/bash
# 080 development (080_prereg_v7f_ea.md): gen_eval2pv (v7f main + fixed variants incl. ea0.5w1) with rank_v7a on the decision tables (+ dev2).
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
echo "== $(date +%T) model rank_v7a $(sha256sum rank_v7a/lambdarank.txt | cut -c1-8) evaluator $(sha256sum gen_eval2pv.py | cut -c1-8)"
ev() { T=$1; shift
  $PY -X utf8 gen_eval2pv.py --model rank_v7a/lambdarank.txt --parents 0 "$@" --views c1,c2 --out diag/v080_$T --workers 4 > diag/v080_$T.log 2>&1
  echo "== $(date +%T) eval080 $T exit $?"; }
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
echo "V7FEA080_DONE $(date +%T)"
