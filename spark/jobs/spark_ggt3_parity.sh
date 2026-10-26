#!/bin/bash
# 044 ggt3 parity on parity16 (both views): frozen experiments/b1_gen044 with the 0.379 configuration + --gen_rank 3 --gen_rule fzgate --gen_gl;
# (1) base list = anaw0.5 (b1_parity, shared forward cache), (2) gt3-path decisions (gen_parity2 fzgate), (3) GL-rule decisions (gen_parity3)
# against gen_eval3 fed with the pipeline's own base GL and generated GL.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_gen044; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_parity16_fe; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt; FE=data/external/fpnet_fulleval_as_fold0
echo "== $(date +%T) frozen pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12)"
FAIL=0
for mode in c2 c1; do
  W=$E/run_ggt3_$mode
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap --gen_rank 3 --gen_rule fzgate --gen_gl > $W.log 2>&1
  echo "== $(date +%T) pipeline $mode exit $? $(grep -a 'generated GL:\|submission written' $W.log | cut -c1-200 | tr '\n' ' ')"
  $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_${mode}.md \
    --pred_main $W/submission_base.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap --analog_parquet $B/diag/analog3_fe.parquet > $W/parity.log 2>&1
  prc=$?; echo "base-list parity $mode exit $prc"; [ $prc = 0 ] || FAIL=1
  (cd $B && NUMBA_NUM_THREADS=8 $PY -X utf8 gen_eval3.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/parity16_molecules.csv --fold_safe $FE --views c1,c2 \
     --gl_gen parity_dummy --gl_base_json ../../$W/gl_out.json --gl_gen_json ../../$W/gl_gen_out.json --out diag/ggt3par_$mode --dump_choice diag/genchoice3_par16_$mode.parquet --workers 8 > diag/ggt3par_$mode.log 2>&1; echo "== gen_eval3 $mode exit $?")
  $PY -X utf8 $B/gen_parity3.py --pipe_work $W --choice $B/diag/genchoice3_par16_$mode.parquet --view $mode --out $W/parity_ggt3_${mode}.md
  grc=$?; echo "ggt3 parity $mode exit $grc"; [ $grc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "GGT3PAR_DONE PASS $(date +%T)" || echo "GGT3PAR_DONE FAIL $(date +%T)"
