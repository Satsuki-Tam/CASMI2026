#!/bin/bash
# W7 on the full development eval set (600 molecules): test-format parquet with per-molecule masks (evaluator conventions), the SUBMISSION
# pipeline in the C2 and C1 proxies with candidate M1 (learned main = rank_v2, fixed insurance tau 0.9), official scores, parity vs run1_v2.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; E=$B/eval_test_full; PY=.venv/bin/python
git fetch -q origin && git checkout -q origin/main -- $B/b1_pipeline.py $B/b1_parity.py $B/b1_rankfeats.py $B/b1_common.py $B/make_eval_test.py $B/b1_evaluate.py src/metric.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --sets A_timstof B_nplib || { echo "W7FULL FAILED: make_eval_test"; exit 1; }
tr -d '\n ' < $E/eval_test_manifest.json; echo
for mode in c2 c1; do
  echo "== $(date +%T) pipeline $mode on 600 molecules (M1: rank_v2, ICE on, insurance tau 0.9)"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 12 --folds 0 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $B/rank_v2/lambdarank.txt --tau 0.9 > $E/run_$mode.log 2>&1
  rc=$?; echo "== $(date +%T) exit $rc : $(grep -a 'OFFICIAL\|Traceback\|Error' $E/run_$mode.log | tail -2 | cut -c1-400)"
  [ $rc = 0 ] && [ -s $E/run_$mode/b1_candidates.parquet ] || { echo "W7FULL FAILED: pipeline $mode"; exit 1; }
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $B/run1_v2 --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_$mode.md --pred_csv $E/run_$mode/submission_fixed.csv --w_ice 1 --tau 0.9 --margin 0.2 2>&1 | grep -a "identical candidate\|Jaccard\|truth in\|disagrees\|fixed-rule output\|top-1 identical" | cut -c1-240
  echo "-- eval_scores: $(tr -d '\n ' < $E/run_$mode/eval_scores.json | cut -c1-600)"
  echo "-- manifest: $(tr -d '\n ' < $E/run_$mode/b1_run_manifest.json | cut -c1-300)"
done
echo "W7FULL_DONE $(date +%T)"
