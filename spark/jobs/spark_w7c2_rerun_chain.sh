#!/bin/bash
# Re-run the W7 C2 proxy on the full development eval set after the first run lost GLACIER to a GB10 crash (pipeline runners now go through
# the resumable driver). Waits for the first chain to finish its C1 run; then pipeline (M1 config) -> parity verdict.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; E=$B/eval_test_full; PY=.venv/bin/python
until grep -q "W7FULL_DONE\|W7FULL FAILED" logs/spark_w7full_chain.log 2>/dev/null; do sleep 120; done
git fetch -q origin && git checkout -q origin/main -- $B/b1_pipeline.py $B/b1_parity.py spark/jobs/ice_resume.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
mv $E/run_c2 $E/run_c2_glcrash 2>/dev/null; mv $E/run_c2.log $E/run_c2_glcrash.log 2>/dev/null
echo "== $(date +%T) pipeline c2 rerun on 600 molecules (M1, runners via resumable driver)"
$PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_c2 --workers 12 --folds 0 --mask_json $E/mask_c2.json --solution $E/solution.csv --rank_model $B/rank_v2/lambdarank.txt --tau 0.9 > $E/run_c2.log 2>&1
rc=$?; echo "== $(date +%T) exit $rc : $(grep -a 'OFFICIAL\|Traceback\|Error' $E/run_c2.log | tail -2 | cut -c1-400)"
[ $rc = 0 ] && [ -s $E/run_c2/b1_candidates.parquet ] || { echo "W7C2 FAILED: pipeline"; exit 1; }
echo "-- manifest: $(tr -d '\n ' < $E/run_c2/b1_run_manifest.json | cut -c1-300)"
$PY -X utf8 $B/b1_parity.py --dump $E/run_c2/b1_candidates.parquet --features_run $B/run1_v2 --view c2 --solution $E/solution.csv --out $E/run_c2/parity_c2.md --pred_main $E/run_c2/submission.csv --pred_fixed $E/run_c2/submission_fixed.csv --stage_stats $E/run_c2/b1_stage_stats.csv --model $B/rank_v2/lambdarank.txt --w_ice 1 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_c2 2>&1 | grep -a "PARITY\|main (learned\|insurance (fixed\|forward-score\|query selection\|identical candidate" | cut -c1-240
echo "-- eval_scores: $(tr -d '\n ' < $E/run_c2/eval_scores.json | cut -c1-600)"
echo "W7C2_DONE $(date +%T)"
