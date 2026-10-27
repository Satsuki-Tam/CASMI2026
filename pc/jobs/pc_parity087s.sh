#!/bin/bash
# Codex 092: the kernel embeds the STRIPPED ranker (rank_v8w7a/lambdarank_stripped.txt). Re-run the evaluator side of the 087 parity with the stripped
# model against the same pipeline outputs (pipeline used the original model) -> PASS means the stripped model orders the real panel rows identically.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "PARITY087_DONE" logs/pc_parity087.log 2>/dev/null; do sleep 30; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; FRUN=$B/run_panel_fe_pc; MODEL=$B/rank_v8w7a/lambdarank_stripped.txt
echo "== $(date +%T) stripped model $(sha256sum $MODEL | cut -c1-12)"
FAIL=0
for mode in c2 c1; do
  W=$E/run_v8w7a_${mode}
  $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_stripped_${mode}.md \
    --pred_main $W/submission.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
    --analog_parquet $B/diag/analog3_fe_pcpc.parquet --frag_w_fallback 1 --frag_parquet $B/diag/frag_panel_pc.parquet > $W/parity_stripped.log 2>&1
  rc=$?; echo "parity087s $mode exit $rc $(tail -1 $W/parity_stripped.log | cut -c1-200)"; [ $rc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "PARITY087S_DONE PASS $(date +%T)" || echo "PARITY087S_DONE FAIL $(date +%T)"
