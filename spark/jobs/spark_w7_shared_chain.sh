#!/bin/bash
# Codex 014: shared-cache MECHANICAL parity for the version being opened (M2x blend21, eval_test_full3). The evaluator-side ranking is computed
# with the forward scores produced by the pipeline run itself (gl_out.json), so candidate sets, truth membership, top-1, RR, ordered top-25 and
# the missing-data branch must agree exactly (thresholds 1.0). Runs after each proxy view of spark_w7_m2xb_chain.sh completes.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; E=$B/eval_test_full3; FRUN=$B/run_v3b_eval; MODEL=$B/rank_v4b/lambdarank.txt
for mode in c2 c1; do
  until grep -q "W7M2XB_${mode}_DONE\|W7M2XB FAILED" logs/spark_w7_m2xb_chain.log 2>/dev/null; do sleep 60; done
  grep -q "W7M2XB FAILED" logs/spark_w7_m2xb_chain.log && { echo "W7_SHARED ABORTED: pipeline chain failed"; exit 1; }
  echo "== $(date +%T) shared-cache parity $mode"
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_${mode}_shared.md --pred_main $E/run_$mode/submission.csv --pred_fixed $E/run_$mode/submission_fixed.csv --stage_stats $E/run_$mode/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_$mode --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 2>&1 | grep -a "PARITY\|identical\|query selection\|differs\|^| main\|^| insurance\|abs diff\|fallback" | cut -c1-220
  echo "W7_SHARED_${mode}_DONE $(date +%T)"
done
echo "W7_SHARED_DONE $(date +%T)"
