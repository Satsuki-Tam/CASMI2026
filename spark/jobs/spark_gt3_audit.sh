#!/bin/bash
# 043 pre-submission audit (a): the gt3 choices (c1/c2 views) of every evaluated run, then the official-identity novelty audit of the inserted structures.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
PY=$HOME/CASMI2026/.venv/bin/python; F0=data/external/fold_safe_fpnet
run() { $PY -X utf8 gen_eval2p.py --run $1 --gen $2 --sets $3 --eval_csv $4 --fold_safe $5 --views c1,c2 --out diag/gt3ch_$6 --dump_choice diag/genchoice2p_$6.parquet --workers 8 > diag/gt3ch_$6.log 2>&1; echo "== $(date +%T) $6 exit $?"; }
run run_p2dev_fe run_p2dev_fe_g/gen "C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" eval_set2/v2/p2_molecules.csv data/external/fpnet_fulleval_as_fold0 p2dev &
run run_panel_fe run_panel_fe_g/gen P_np250 panel_np250/p1_molecules.csv data/external/fpnet_fulleval_as_fold0 panel &
wait
run run_conffit_m2x run_conffit_m2x_g/gen "C_np_crosslib E_np_negonly F_np_uncovered G_tims_crosslib" eval_conf_fit/p2_molecules.csv $F0 conffit &
run run_conffit2_m2x run_conffit2_m2x_g/gen "D_np_single E_np_negonly" eval_conf_fit2/p2_molecules.csv $F0 conffit2 &
wait
run run_conf3_m2x run_conf3_m2x_g/gen D_np_single eval_set3/p2_molecules.csv $F0 conf3 &
run run_v3b_eval run_v3b_eval_g/gen "A_timstof B_nplib" eval_set/p1_molecules.csv $F0 w7 &
wait
$PY -X utf8 gt3_audit.py --choice diag/genchoice2p_p2dev.parquet diag/genchoice2p_panel.parquet diag/genchoice2p_conffit.parquet diag/genchoice2p_conffit2.parquet diag/genchoice2p_conf3.parquet diag/genchoice2p_w7.parquet --out diag/gt3_audit --workers 16 > diag/gt3_audit.log 2>&1
echo "== $(date +%T) audit exit $?"
echo "GT3AUDIT_DONE $(date +%T)"
