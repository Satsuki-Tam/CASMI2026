#!/bin/bash
# 045 stage-3 development (pre-registered): gen_eval4 --db_parents 10, pass 1 (GL inputs) -> GLACIER -> pass 2, on dev2 v2 (full_eval),
# fold-1 dev (fpnet_fold1) and the panel (full_eval, protection views). Starts after the stage-2 confirmation.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
until grep -q "STAGE2_CONF2_DONE" logs/spark_stage2_conf2.log 2>/dev/null; do sleep 60; done
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0; FE=data/external/fpnet_fulleval_as_fold0
DEV2="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
cd $B
$PY -X utf8 gen_eval4.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --emit_gl glgen4_p2dev --workers 10 > diag/stage3_emit_p2dev.log 2>&1 &
$PY -X utf8 gen_eval4.py --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --emit_gl glgen4_f1dev --workers 10 > diag/stage3_emit_f1dev.log 2>&1 &
wait
$PY -X utf8 gen_eval4.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --emit_gl glgen4_panel --workers 18 > diag/stage3_emit_panel.log 2>&1
echo "== $(date +%T) GL inputs: $(ls glgen4_p2dev glgen4_f1dev glgen4_panel 2>/dev/null | tr '\n' ' ')"
cd ~/CASMI2026
for D in glgen4_p2dev glgen4_f1dev glgen4_panel; do
  for IN in $B/$D/gl_gen_*_in.json; do
    S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=$B/$D/gl_gen_${S}.json
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > $B/$D/gl_gen_${S}_resume.log 2>&1
    echo "== $(date +%T) GL $D $S $(grep -a '\[resume\] done' $B/$D/gl_gen_${S}_resume.log | cut -c1-100)"
  done
done
cd $B
$PY -X utf8 gen_eval4.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --gl_gen glgen4_p2dev/gl_gen --out diag/stage3_p2dev --workers 10 > diag/stage3_p2dev.log 2>&1 &
$PY -X utf8 gen_eval4.py --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen4_f1dev/gl_gen --out diag/stage3_f1dev --workers 10 > diag/stage3_f1dev.log 2>&1 &
wait
$PY -X utf8 gen_eval4.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --gl_gen glgen4_panel/gl_gen --out diag/stage3_panel --workers 18 > diag/stage3_panel.log 2>&1
echo "STAGE3_DEV_DONE $(date +%T)"
