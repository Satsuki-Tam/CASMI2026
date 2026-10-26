#!/bin/bash
# 042 generation study, step 2: gen_eval on the panel (now) and dev2 v2 (after its --dump_gen run)
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=~/CASMI2026/.venv/bin/python
$PY -X utf8 gen_eval.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --out diag/geneval_panel --workers 12 > diag/geneval_panel.log 2>&1
echo "== $(date +%T) panel exit $?"
until [ -f run_p2dev_fe_g/gen/gen_G_tims_crosslib_window.parquet ]; do sleep 30; done
$PY -X utf8 gen_eval.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set2/v2/p2_molecules.csv --out diag/geneval_p2dev --workers 12 > diag/geneval_p2dev.log 2>&1
echo "== $(date +%T) p2dev exit $?"
echo "GEN042_EVAL_DONE"
