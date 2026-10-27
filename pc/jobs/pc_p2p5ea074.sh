#!/bin/bash
# 074 (reports/agent_review/074_prereg_p2p5ea.md): fixed P2 / EA / P5 variants of the 0.379 main (rank_v4b) on every development table.
# Starts when the 067 CPU evaluations are finished (CPU slot). No CUDA.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "MIX067_PC_DONE" logs/pc_mix067.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; cd experiments/b1_baseline
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  $PY -X utf8 gen_eval2p.py --model rank_v4b/lambdarank.txt --parents 0 "$@" --views c1,c2 --out diag/p074_$T --workers 6 > diag/p074_$T.log 2>&1
  echo "== $(date +%T) eval074 $T exit $?"; }
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
echo "P2P5EA074_DONE $(date +%T)"
