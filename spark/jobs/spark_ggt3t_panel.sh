#!/bin/bash
# 045: ggt3 parity of the frozen experiments/b1_gen045 (hard deadline + manifest record) on ALL 250 panel molecules (both views):
# (1) base list = anaw0.5 (b1_parity, shared forward cache), (2) gen_eval3 with the pipeline's base + generated GL -> dump_choice,
# (3) full-list parity (gen_parity4 --rule ggt3: every query, ordered top-25 official keys, ids, duplicates), (4) GL-rule decisions (gen_parity3).
# Every non-zero exit fails the verdict.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_gen048; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_panel250_fe; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt; FE=data/external/fpnet_fulleval_as_fold0
true
echo "== $(date +%T) frozen pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) gen_eval3 $(sha256sum $B/gen_eval3.py | cut -c1-12)"
FAIL=0
for mode in c2 c1; do
  W=$E/run_ggt3t_$mode
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap --gen_rank 3 --gen_rule fzgate2 --gen_gl > $W.log 2>&1
  rc=$?; echo "== $(date +%T) pipeline $mode exit $rc $(grep -a 'generated GL:\|submission written' $W.log | cut -c1-220 | tr '\n' ' ')"; [ $rc = 0 ] || FAIL=1
  $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_${mode}.md \
    --pred_main $W/submission_base.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap --analog_parquet $B/diag/analog3_fe.parquet > $W/parity.log 2>&1
  rc=$?; echo "base-list parity $mode exit $rc"; [ $rc = 0 ] || FAIL=1
  (cd $B && NUMBA_NUM_THREADS=8 $PY -X utf8 gen_eval3.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 \
     --gl_gen parity_dummy --gl_base_json ../../$W/gl_out.json --gl_gen_json ../../$W/gl_gen_out.json --out diag/ggt3t_p250_$mode --dump_choice diag/genchoice3t_p250_$mode.parquet --workers 8 > diag/ggt3t_p250_$mode.log 2>&1)
  rc=$?; echo "gen_eval3 $mode exit $rc"; [ $rc = 0 ] || FAIL=1
  $PY -X utf8 $B/gen_parity4.py --pipe_work $W --choice $B/diag/genchoice3t_p250_$mode.parquet --view $mode --rule ggt3t --out $W/parity4_ggt3t_${mode}.md 2>/dev/null
  rc=$?; echo "full-list parity $mode exit $rc"; [ $rc = 0 ] || FAIL=1
  $PY -X utf8 $B/gen_parity3.py --pipe_work $W --choice $B/diag/genchoice3t_p250_$mode.parquet --view $mode --out $W/parity_ggt3_${mode}.md 2>/dev/null
  rc=$?; echo "GL-rule parity $mode exit $rc"; [ $rc = 0 ] || FAIL=1
  $PY -c "import json; m = json.load(open('$W/b1_run_manifest.json')); print('manifest gen_gl_record', m['params'].get('gen_gl_record'))"
done
[ $FAIL = 0 ] && echo "GGT3T_P250_DONE PASS $(date +%T)" || echo "GGT3T_P250_DONE FAIL $(date +%T)"
