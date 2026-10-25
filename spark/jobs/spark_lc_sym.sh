#!/bin/bash
# Codex 030 audit: symmetric-mask DIAGNOSTIC tables (query library removed for every candidate in the C1 view), panel + dev2 C/G, after the pilot.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "LCPILOT_DONE" logs/spark_lc_pilot.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FS=data/external/fpnet_fulleval_as_fold0
for E in "$B/panel_np250/p1_molecules.csv $B/run_panel_fe_lcsym P_np250" "$B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_fe_lcsym C_np_crosslib G_tims_crosslib"; do
  set -- $E; EVAL=$1; RUN=$2; shift 2; mkdir -p $RUN/work
  $PY -X utf8 $B/b1_features_sym.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --lib_conditions --sym_lib_mask --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) sym features $RUN exit $?"
done
$PY -X utf8 $B/lc_audit.py --runs $B/run_panel_fe_lc:P_np250 $B/run_p2dev_fe_lc:C_np_crosslib,D_np_single,E_np_negonly,F_np_uncovered,G_tims_crosslib \
  --sym_runs $B/run_panel_fe_lcsym:P_np250 $B/run_p2dev_fe_lcsym:C_np_crosslib,G_tims_crosslib --out $B/diag/lc_audit.md > /dev/null 2>&1
echo "LCSYM_DONE $(date +%T)"
