#!/bin/bash
# 044 stage-2 development (pre-registered in reports/agent_review/044_prereg_stage2.md): GLACIER on the top-5 novel generated structures, then
# the GL-scale rules on dev2 v2 (full_eval) + fold-1 dev (fpnet_fold1) + panel full_eval (protection views). Waits for the fold-1 tables + GL.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
until grep -q "FOLD1_SETS_DONE" logs/spark_fold1_sets.log 2>/dev/null; do sleep 60; done
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0; FE=data/external/fpnet_fulleval_as_fold0
DEV2="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
cd $B
# pass 1: GL inputs
$PY -X utf8 gen_eval3.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --emit_gl glgen_p2dev --workers 10 > diag/stage2_emit_p2dev.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --emit_gl glgen_f1dev --workers 10 > diag/stage2_emit_f1dev.log 2>&1 &
wait
$PY -X utf8 gen_eval3.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --emit_gl glgen_panel --workers 16 > diag/stage2_emit_panel.log 2>&1
echo "== $(date +%T) GL inputs: $(ls glgen_p2dev glgen_f1dev glgen_panel 2>/dev/null | tr '\n' ' ')"
cd ~/CASMI2026
for D in glgen_p2dev glgen_f1dev glgen_panel; do
  for IN in $B/$D/gl_gen_*_in.json; do
    S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=$B/$D/gl_gen_${S}.json
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > $B/$D/gl_gen_${S}_resume.log 2>&1
    echo "== $(date +%T) GL $D $S $(grep -a '\[resume\] done' $B/$D/gl_gen_${S}_resume.log | cut -c1-100)"
  done
done
cd $B
$PY -X utf8 gen_eval3.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --gl_gen glgen_p2dev/gl_gen --out diag/stage2_p2dev --workers 10 > diag/stage2_p2dev.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen_f1dev/gl_gen --out diag/stage2_f1dev --workers 10 > diag/stage2_f1dev.log 2>&1 &
wait
$PY -X utf8 gen_eval3.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --gl_gen glgen_panel/gl_gen --out diag/stage2_panel --workers 16 > diag/stage2_panel.log 2>&1
echo "STAGE2_DEV_DONE $(date +%T)"
