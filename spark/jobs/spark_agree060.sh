#!/bin/bash
# 060 development: agreement top-1 rule on existing runs (f1dev, f2dev, dev2, panel) and the 053 NP dev, views c1,c2.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "NP053_SETS_DONE" logs/spark_np053_sets.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; R=$HOME/CASMI2026; A="--agree 0.6 0.7 0.8 0.9"
echo "== $(date +%T) gen_eval2va $(sha256sum $B/gen_eval2va.py | cut -c1-12)"
cd $B
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
nice -n 5 $PY -X utf8 gen_eval2va.py --model rank_v4b/lambdarank.txt --parents 0 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $R/data/external/fpnet_fulleval_as_fold0 --views c1,c2 $A --out diag/a060_panel --workers 6 > diag/a060_panel.log 2>&1; echo "== $(date +%T) panel exit $?"
nice -n 5 $PY -X utf8 gen_eval2va.py --model rank_v4b/lambdarank.txt --parents 0 --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold1_as_fold0 --views c1,c2 $A --out diag/a060_f1dev --workers 6 > diag/a060_f1dev.log 2>&1; echo "== $(date +%T) f1dev exit $?"
nice -n 5 $PY -X utf8 gen_eval2va.py --model rank_v4b/lambdarank.txt --parents 0 --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold2_as_fold0 --views c1,c2 $A --out diag/a060_f2dev --workers 6 > diag/a060_f2dev.log 2>&1; echo "== $(date +%T) f2dev exit $?"
for K in 1 2; do
  nice -n 5 $PY -X utf8 gen_eval2va.py --model rank_v4b/lambdarank.txt --parents 0 --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold${K}_as_fold0 --views c1,c2 $A --out diag/a060_np053f$K --workers 6 > diag/a060_np053f$K.log 2>&1; echo "== $(date +%T) np053 f$K exit $?"
done
echo "AGREE060_DONE $(date +%T)"
