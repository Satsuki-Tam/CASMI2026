#!/bin/bash
# 063 diagnostic: raw f.z shift fed to the ranker, on full_eval tables (dev2, panel) and a fold-model table (f1dev, control).
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
PY=$HOME/CASMI2026/.venv/bin/python; R=$HOME/CASMI2026; A="--fp_shifts -15 -10 -5 10"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
echo "== $(date +%T) gen_eval2s $(sha256sum gen_eval2s.py | cut -c1-12)"
nice -n 5 $PY -X utf8 gen_eval2s.py --model rank_v4b/lambdarank.txt --parents 0 --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $R/data/external/fpnet_fulleval_as_fold0 --views c1,c2 $A --out diag/f063_p2dev --workers 6 > diag/f063_p2dev.log 2>&1; echo "== $(date +%T) p2dev exit $?"
nice -n 5 $PY -X utf8 gen_eval2s.py --model rank_v4b/lambdarank.txt --parents 0 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $R/data/external/fpnet_fulleval_as_fold0 --views c1,c2 $A --out diag/f063_panel --workers 6 > diag/f063_panel.log 2>&1; echo "== $(date +%T) panel exit $?"
nice -n 5 $PY -X utf8 gen_eval2s.py --model rank_v4b/lambdarank.txt --parents 0 --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold1_as_fold0 --views c1,c2 $A --out diag/f063_f1dev --workers 6 > diag/f063_f1dev.log 2>&1; echo "== $(date +%T) f1dev exit $?"
echo "FPS063_DONE $(date +%T)"
