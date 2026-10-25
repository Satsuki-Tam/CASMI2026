#!/bin/bash
# Codex 024 Q3: the only remaining demotion candidate (unconditional w = 0.5) measured in the FPNet-seen regime: full_eval tables (M2x_fe; panel C1 =
# identity seen, query unseen; dev2 = held out from full_eval, unseen) next to the fold-0 tables (M2x). Same evaluator, fallback and model.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_fe P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_fe C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$2; run=$3; shift 3; OUT=$B/pcdfe_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) pcd 0.5 on full_eval tables $name ($run), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x_fe:$B/$run:$B/rank_v4b/lambdarank.txt:0 --main_of M2x_fe=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --pcd_w 0.5 --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"
done
$PY -X utf8 $B/pcl_boost_report.py $B/pcdfe_eval_panel $B/pcdfe_eval_p2dev --cand M2x_fe --prefix pcd --out $B/diag/pcd_fe_report.md
echo "PCDFE_DONE $(date +%T)"
