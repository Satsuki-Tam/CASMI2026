#!/bin/bash
# Features-only shortlist audit with the current fold-0 FPNet (no forward runners): pool-window branch reach on W7 A/B, dev2 v2, panel.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "$B/eval_set/p1_molecules.csv run_poolaudit_devAB A_timstof B_nplib" "$B/eval_set2/v2/p2_molecules.csv run_poolaudit_p2dev C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "$B/panel_np250/p1_molecules.csv run_poolaudit_panel P_np250"; do
  set -- $E; csv=$1; run=$B/$2; shift 2; mkdir -p $run
  echo "== $(date +%T) audit $run sets $*"
  $PY -X utf8 $B/b1_features.py --eval_csv $csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $run --k 100 --workers 8 --k_fpp 200 --k_pop 50 --sets "$@" > $run/features.log 2>&1
  echo "exit $? $(grep -a "^saved\|^done" $run/features.log | tr "\n" " " | cut -c1-200)"
done
echo "POOLAUDIT_DONE $(date +%T)"
