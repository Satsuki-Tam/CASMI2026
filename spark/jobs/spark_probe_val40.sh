#!/bin/bash
# Codex 023b: validate the EMBEDDED probe pipeline (experiments/b1_probe023/b1_pipeline.py, sha 1bc93dda) on 40 dev2 molecules (8 per stratum; Pc,
# COCONUT-only and T&C truths), both views, registered M2x configuration; validate_probes.py checks membership, prefix order, partition, RR relations.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_probe023; PY=.venv/bin/python; E=$B/eval_test_val40; MODEL=$B/rank_v4b/lambdarank.txt
echo "== $(date +%T) probe validation, pipeline sha $(sha256sum $S/b1_pipeline.py | cut -c1-16)"
rm -rf $E; mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv $S/val40_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib > $E/build.log 2>&1 || { echo "VAL40 FAILED: make_eval_test"; tail -5 $E/build.log; exit 1; }
for mode in c1 c2; do
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 > $E/run_$mode.log 2>&1
  echo "pipeline $mode exit $? ; $(grep -a 'OFFICIAL MRR' $E/run_$mode.log | cut -c1-120)"
  $PY -X utf8 $S/validate_probes.py --run $E/run_$mode --molecules $S/val40_molecules.csv --view $mode 2>&1 | tail -3
done
echo "VAL40_DONE $(date +%T)"
