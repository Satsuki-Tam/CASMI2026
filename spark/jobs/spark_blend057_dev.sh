#!/bin/bash
# 057 development: blend-weight variants of the registered main on existing dev runs (NP-truth subsets read afterwards), then on 053 NP dev.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
PY=$HOME/CASMI2026/.venv/bin/python; R=$HOME/CASMI2026
V="2:2:0.5 2:1:0.5 2:0.5:0.5 2:1:1 2:2:1 3:2:0.5 1:1:0.5 2:0.5:1"
echo "== $(date +%T) gen_eval2v $(sha256sum gen_eval2v.py | cut -c1-12)"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
nice -n 5 $PY -X utf8 gen_eval2v.py --model rank_v4b/lambdarank.txt --parents 0 --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold1_as_fold0 --views c1,c2 --variants $V --out diag/b057_f1dev --workers 6 > diag/b057_f1dev.log 2>&1; echo "== $(date +%T) f1dev exit $?"
nice -n 5 $PY -X utf8 gen_eval2v.py --model rank_v4b/lambdarank.txt --parents 0 --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold2_as_fold0 --views c1,c2 --variants $V --out diag/b057_f2dev --workers 6 > diag/b057_f2dev.log 2>&1; echo "== $(date +%T) f2dev exit $?"
nice -n 5 $PY -X utf8 gen_eval2v.py --model rank_v4b/lambdarank.txt --parents 0 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $R/data/external/fpnet_fulleval_as_fold0 --views c1,c2 --variants $V --out diag/b057_panel --workers 6 > diag/b057_panel.log 2>&1; echo "== $(date +%T) panel exit $?"
until grep -q "NP053_SETS_DONE" $R/logs/spark_np053_sets.log 2>/dev/null; do sleep 60; done
for K in 1 2; do
  nice -n 5 $PY -X utf8 gen_eval2v.py --model rank_v4b/lambdarank.txt --parents 0 --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold${K}_as_fold0 --views c1,c2 --variants $V --out diag/b057_np053f${K} --workers 6 > diag/b057_np053f${K}.log 2>&1; echo "== $(date +%T) np053 f$K exit $?"
done
echo "BLEND057_DONE $(date +%T)"
