#!/bin/bash
# Codex 020 condition (3) for a pool60 submission: MECHANICAL parity of the submission pipeline (--k_pool 60) and the evaluator
# (b1_features --k_pool 60, view-specific pool eligibility) on 50 W7 molecules, both views, with the shared forward cache (--forward_from pipe)
# and thresholds 1.0. Waits for the corrected W7 pool feature run (run_v3b_eval_pool2).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; E=$B/eval_test_50_kpool; FRUN=$B/run_v3b_eval_pool2; MODEL=$B/rank_v4b/lambdarank.txt
until grep -q "KPOOL_FIX_DONE" logs/spark_kpool_fix_chain.log 2>/dev/null; do sleep 120; done
echo "== $(date +%T) parity k_pool 60: pipeline sha $(sha256sum $B/b1_pipeline.py | cut -c1-16), features sha $(sha256sum $B/b1_features.py | cut -c1-16)"
rm -rf $E; mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --limit 25 --sets A_timstof B_nplib || { echo "PARITYK FAILED: make_eval_test"; exit 1; }
FAIL=0
for mode in c2 c1; do
  echo "== $(date +%T) pipeline $mode on 50 molecules (--k_pool 60)"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 12 --folds 0 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --k_pool 60 > $E/run_$mode.log 2>&1
  rc=$?; echo "pipeline exit $rc"; [ $rc = 0 ] && [ -s $E/run_$mode/b1_candidates.parquet ] || { echo "PARITYK FAILED: pipeline $mode"; exit 1; }
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_${mode}_shared.md \
    --pred_main $E/run_$mode/submission.csv --pred_fixed $E/run_$mode/submission_fixed.csv --stage_stats $E/run_$mode/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_$mode --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 2>&1 | grep -a "PARITY\|identical\|differs\|query selection\|^| main\|^| insurance\|fallback" | cut -c1-200
  prc=${PIPESTATUS[0]}; echo "parity $mode exit $prc"; [ $prc = 0 ] || FAIL=1
  echo "-- seconds: $(grep -o '"seconds": [0-9]*' $E/run_$mode/b1_run_manifest.json | head -1) | fusion: $(grep -o '"fusion": {[^}]*}' $E/run_$mode/b1_run_manifest.json | cut -c1-160)"
done
[ $FAIL = 0 ] && echo "PARITYK_DONE PASS $(date +%T)" || echo "PARITYK_DONE FAIL $(date +%T)"
