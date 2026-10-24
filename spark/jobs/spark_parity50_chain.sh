#!/bin/bash
# W7 parity on a 50-molecule subset (A/B 25 each of eval_set): rebuild the test-format parquet with per-molecule masks and the evaluator's
# electron convention, run the SUBMISSION pipeline in the C2 and C1 proxies (learned main = rank_v2, fixed insurance tau 0.9), then compare
# candidate sets / features / fixed-rule outputs with the evaluator's run1_v2 tables. Gate: the script stops at the first failing step.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
# candidate configuration (M1 default): features run of the evaluator, model, ICE weight, extra pipeline args, output dir
CAND=${CAND:-M1}
if [ "$CAND" = M2 ]; then FRUN=$B/run_v3_eval; MODEL=$B/rank_v3/lambdarank.txt; WICE=0; PARGS="--k_fpp 200 --k_pop 50 --w_ice 0"; E=$B/eval_test_50_m2
else FRUN=$B/run1_v2; MODEL=$B/rank_v2/lambdarank.txt; WICE=1; PARGS=""; E=$B/eval_test_50c; fi
echo "candidate $CAND: features $FRUN, model $MODEL, w_ice $WICE, pipeline args [$PARGS]"
git fetch -q origin && git checkout -q origin/main -- $B/b1_pipeline.py $B/b1_parity.py $B/b1_rankfeats.py $B/b1_common.py $B/make_eval_test.py $B/b1_evaluate.py $B/b1_locked_eval.py src/metric.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --limit 25 --sets A_timstof B_nplib || { echo "PARITY50 FAILED: make_eval_test"; exit 1; }
cat $E/eval_test_manifest.json | tr -d '\n '; echo
for mode in c2 c1; do
  echo "== $(date +%T) pipeline $mode on 50 molecules"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 12 --folds 0 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 $PARGS > $E/run_$mode.log 2>&1
  rc=$?; echo "== $(date +%T) exit $rc : $(grep -a 'OFFICIAL\|Traceback\|Error' $E/run_$mode.log | tail -2 | cut -c1-300)"
  [ $rc = 0 ] && [ -s $E/run_$mode/b1_candidates.parquet ] || { echo "PARITY50 FAILED: pipeline $mode"; exit 1; }
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_$mode.md       --pred_main $E/run_$mode/submission.csv --pred_fixed $E/run_$mode/submission_fixed.csv --stage_stats $E/run_$mode/b1_stage_stats.csv --model $MODEL --w_ice $WICE --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_$mode 2>&1 | cut -c1-240
  prc=${PIPESTATUS[0]}; echo "parity $mode exit $prc"; [ $prc = 0 ] || PARITY_FAIL=1
  echo "-- eval_scores: $(tr -d '\n ' < $E/run_$mode/eval_scores.json | cut -c1-400)"
done
if [ "${PARITY_FAIL:-0}" = 1 ]; then echo "PARITY50 FAILED: verdict"; exit 1; fi
echo "PARITY50_DONE $(date +%T)"
