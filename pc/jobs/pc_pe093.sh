#!/bin/bash
# 093: gen_eval2pv (v7f main + EA variant ea0.5w1) with rank_v8w7a on the 5 development tables of 086 (V / V+E come from e086_v7f_*). CPU only.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  $PY -X utf8 gen_eval2pv.py --model rank_v8w7a/lambdarank.txt --refcmp --parents 0 "$@" --views c1,c2 --out diag/e093_${T} --workers 6 > diag/e093_${T}.log 2>&1
  echo "== $(date +%T) pe093 $T exit $?"; }
ev v8w7a_np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev v8w7a_np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev v8w7a_panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev v8w7a_f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev v8w7a_f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
echo "PE093_DONE $(date +%T)"
