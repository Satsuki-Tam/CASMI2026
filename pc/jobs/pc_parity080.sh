#!/bin/bash
# 080 parity (080_prereg_v7f_ea.md + Codex 081): the v7f frozen sources + EA option (experiments/b1_v7fea) on the 250 panel molecules, both views,
# evaluation mode, against the SAME-PC evaluator table run_panel_fe_pc (built by pc_parity076b.sh). One pipeline run per view gives
# submission_noea.csv (v7f alone -> parity of the v7f reproduction, required BEFORE the 053 conf is opened) and submission.csv (v7f + EA).
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "PARITY076B_DONE" logs/pc_parity076b.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; S=experiments/b1_v7fea; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; FRUN=$B/run_panel_fe_pc; MODEL=$B/rank_v7a/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
echo "== $(date +%T) pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) model $(sha256sum $MODEL | cut -c1-12)"
$PY -X utf8 $B/frag_probe.py --runs run_panel_fe_pc:panel_np250/p1_molecules.csv:P_np250 --out diag/frag_panel_pc.parquet --workers 4 > $B/diag/frag_panel_pc.log 2>&1 &
FRAGPID=$!
FAIL=0
for mode in c2 c1; do
  W=$E/run_v7fea_${mode}
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0 --analog_w_fallback 1 --analog_feat ap --frag_w_fallback 1 --ea_w 1 --ea_theta 0.5 > $W.log 2>&1
  rc=$?; echo "== $(date +%T) pipeline $mode exit $rc $(grep -a 'submission written' $W.log | tail -1 | cut -c1-220)"; [ $rc = 0 ] || FAIL=1
done
wait $FRAGPID; echo "== $(date +%T) frag probe exit $?"
for mode in c2 c1; do
  W=$E/run_v7fea_${mode}
  for kind in noea ea; do
    PM=$W/submission.csv; EAARGS="--ea_w 1 --ea_theta 0.5"; [ $kind = noea ] && { PM=$W/submission_noea.csv; EAARGS=""; }
    $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_${kind}_${mode}.md \
      --pred_main $PM --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
      --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
      --analog_parquet $B/diag/analog3_fe_pcpc.parquet --frag_w_fallback 1 --frag_parquet $B/diag/frag_panel_pc.parquet $EAARGS > $W/parity_${kind}.log 2>&1
    rc=$?; echo "parity080 $kind $mode exit $rc $(tail -1 $W/parity_${kind}.log | cut -c1-200)"; [ $rc = 0 ] || FAIL=1
  done
done
[ $FAIL = 0 ] && echo "PARITY080_DONE PASS $(date +%T)" || echo "PARITY080_DONE FAIL $(date +%T)"
