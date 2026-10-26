#!/bin/bash
# 048 development (pre-registered): gen_eval3 with gt3t / ggt3t on dev2 v2, fold-1 dev, fold-2 dev (new GL inputs) and the panel; consistency of
# main / gt3 / ggt3 with the stage-2 tables where they exist.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0; F2=data/external/fpnet_fold2_as_fold0; FE=data/external/fpnet_fulleval_as_fold0
DEV2="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
cd $B
$PY -X utf8 gen_eval3.py --run run_f2dev --gen run_f2dev/gen --sets $DEV2 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $F2 --views c1,c2,c3 --emit_gl glgen_f2dev --workers 8 > diag/g048_emit_f2dev.log 2>&1
cd ~/CASMI2026
for IN in $B/glgen_f2dev/gl_gen_*_in.json; do
  S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=$B/glgen_f2dev/gl_gen_${S}.json
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > $B/glgen_f2dev/gl_gen_${S}_resume.log 2>&1
  echo "== $(date +%T) GL f2dev $S $(grep -a '\[resume\] done' $B/glgen_f2dev/gl_gen_${S}_resume.log | cut -c1-90)"
done
cd $B
$PY -X utf8 gen_eval3.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --gl_gen glgen_p2dev/gl_gen --out diag/g048_p2dev --workers 6 > diag/g048_p2dev.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen_f1dev/gl_gen --out diag/g048_f1dev --workers 6 > diag/g048_f1dev.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f2dev --gen run_f2dev/gen --sets $DEV2 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $F2 --views c1,c2,c3 --gl_gen glgen_f2dev/gl_gen --out diag/g048_f2dev --workers 6 > diag/g048_f2dev.log 2>&1 &
wait
$PY -X utf8 gen_eval3.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --gl_gen glgen_panel/gl_gen --out diag/g048_panel --workers 12 > diag/g048_panel.log 2>&1
$PY - <<'PY'
import pandas as pd
k = ["set", "view", "molecule"]
for n in ("p2dev", "f1dev", "panel"):
    a = pd.read_csv(f"diag/g048_{n}.csv"); b = pd.read_csv(f"diag/stage2_{n}.csv"); m = a.merge(b, on=k, suffixes=("", "_s2"))
    print(n, "rows", len(a), "main/gt3/ggt3 identical to stage 2:", all(bool((m[c] - m[c + "_s2"]).abs().max() < 1e-12) for c in ("main", "gt3", "ggt3")))
PY
echo "GATE048_DEV_DONE $(date +%T)"
