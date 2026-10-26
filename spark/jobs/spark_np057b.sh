#!/bin/bash
# 057b on the 053 NP-truth dev sets: blend / PubChemLite-boost / analog-weight variants (gen_eval2vp), after the 053 tables + GL exist.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "NP053_SETS_DONE" logs/spark_np053_sets.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; R=$HOME/CASMI2026
V="2:2:0.5 2:1:0.5 2:0.5:0.5 2:2:1 2:1:1 3:2:0.5 2:2:0.5:1 2:2:0.5:2 2:1:1:1 2:0.5:1:2 2:2:0.5:0:1 2:2:0.5:0:1.5 2:1:0.5:0:1"
echo "== $(date +%T) gen_eval2vp $(sha256sum $B/gen_eval2vp.py | cut -c1-12)"
for K in 1 2; do
  (cd $B && nice -n 5 $PY -X utf8 gen_eval2vp.py --model rank_v4b/lambdarank.txt --parents 0 --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold${K}_as_fold0 --views c1,c2 --variants $V --out diag/np057b_f$K --workers 6 > diag/np057b_f$K.log 2>&1)
  echo "== $(date +%T) np053 f$K exit $?"
done
echo "NP057B_DONE $(date +%T)"
