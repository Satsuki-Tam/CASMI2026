#!/bin/bash
# 076 parity (usage: bash pc_parity076.sh <ea_w> <ea_theta>): the 0.379 sources + EA option (experiments/b1_v074) on all 250 panel molecules, both views,
# evaluation mode; b1_parity with the pipeline's own forward outputs must reproduce the pipeline's main list (EA applied on both sides). CUDA.
set -u
EW=$1; ET=$2
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; S=experiments/b1_v074; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
echo "== $(date +%T) pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) model $(sha256sum $MODEL | cut -c1-12) ea_w $EW ea_theta $ET"
FAIL=0
for mode in c2 c1; do
  W=$E/run_ea_${mode}
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap --ea_w $EW --ea_theta $ET > $W.log 2>&1
  rc=$?; echo "== $(date +%T) pipeline $mode exit $rc $(grep -a 'submission written\|ea_mols' $W.log | tail -1 | cut -c1-200)"; [ $rc = 0 ] || FAIL=1
  $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_${mode}.md \
    --pred_main $W/submission.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap \
    --analog_parquet $B/diag/analog3_fe_pc.parquet --ea_w $EW --ea_theta $ET > $W/parity.log 2>&1
  rc=$?; echo "parity $mode exit $rc $(tail -1 $W/parity.log | cut -c1-160)"; [ $rc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "PARITY076_DONE PASS $(date +%T)" || echo "PARITY076_DONE FAIL $(date +%T)"
