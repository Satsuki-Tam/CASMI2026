#!/bin/bash
# 079: gen_eval2p with rank_v8w_pc (EA variants) on the 6 development tables; starts after the same-platform 076 parity (CPU slot).
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "PARITY076B_DONE" logs/pc_parity076b.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; cd experiments/b1_baseline
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  $PY -X utf8 gen_eval2p.py --model rank_v8w_pc/lambdarank.txt --parents 0 "$@" --views c1,c2 --out diag/p079_$T --workers 6 > diag/p079_$T.log 2>&1
  echo "== $(date +%T) eval079 $T exit $?"; }
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
echo "V8WEA079_DONE $(date +%T)"
