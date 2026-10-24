#!/bin/bash
# W7 parity on a 50-molecule subset (A/B 25 each of eval_set): rebuild the test-format parquet with per-molecule masks and the evaluator's
# electron convention, run the SUBMISSION pipeline in the C2 and C1 proxies (learned main = rank_v2, fixed insurance tau 0.9), then compare
# candidate sets / features / fixed-rule outputs with the evaluator's run1_v2 tables. Gate: the script stops at the first failing step.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; E=$B/eval_test_50; PY=.venv/bin/python
git fetch -q origin && git checkout -q origin/main -- $B/b1_pipeline.py $B/b1_parity.py $B/b1_rankfeats.py $B/b1_common.py $B/make_eval_test.py $B/b1_evaluate.py src/metric.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --limit 25 --sets A_timstof B_nplib || { echo "PARITY50 FAILED: make_eval_test"; exit 1; }
cat $E/eval_test_manifest.json | tr -d '\n '; echo
for mode in c2 c1; do
  echo "== $(date +%T) pipeline $mode on 50 molecules"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 12 --folds 0 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $B/rank_v2/lambdarank.txt --tau 0.9 > $E/run_$mode.log 2>&1
  rc=$?; echo "== $(date +%T) exit $rc : $(grep -a 'OFFICIAL\|Traceback\|Error' $E/run_$mode.log | tail -2 | cut -c1-300)"
  [ $rc = 0 ] && [ -s $E/run_$mode/b1_candidates.parquet ] || { echo "PARITY50 FAILED: pipeline $mode"; exit 1; }
  W=1   # M1 insurance uses ICE weight 1
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $B/run1_v2 --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_$mode.md --pred_csv $E/run_$mode/submission_fixed.csv --w_ice $W --tau 0.9 --margin 0.2 2>&1 | cut -c1-240
  echo "-- eval_scores: $(tr -d '\n ' < $E/run_$mode/eval_scores.json | cut -c1-400)"
done
echo "PARITY50_DONE $(date +%T)"
