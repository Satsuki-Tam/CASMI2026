#!/bin/bash
# 052 diagnostic: timsTOF vs other-instrument queries of the same natural products, fold-safe FPNet per identity fold (never saw them).
# Measures the truth's FP rank in the whole label-free window (b1_molecules truth_fp_rank) per version; no method decision.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
$PY -X utf8 $B/dg052_sets.py || { echo "DG052 FAILED: sets"; exit 1; }
for k in 0 1 2 3 4; do
  if [ $k = 0 ]; then FS=data/external/fold_safe_fpnet; else FS=data/external/fpnet_fold${k}_as_fold0; fi
  RUN=$B/run_dg052/f$k; mkdir -p $RUN
  $PY -X utf8 $B/b1_features.py --eval_csv $B/panel_dg/p1_f$k.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
    --sets DG_T DG_riken DG_gnps > $RUN/features.log 2>&1
  echo "== $(date +%T) fold $k exit $? fpnet $(sha256sum $FS/fpnet_fold0.pt | cut -c1-12) $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-160)"
done
echo "DG052_DONE $(date +%T)"
