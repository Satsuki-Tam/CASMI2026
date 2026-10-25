#!/bin/bash
# Codex 023b follow-up (development, not a submission): soft demotion of PubChem-tier-only candidates on the registered M2x output.
# Outputs blend21_pcd<w> = blend21 - w * 1[neither a training structure (view) nor COCONUT], w = 0.5 1 2 4, and blend21_pcdinf = the pool-only filter of
# the FULL order (local counterpart of the pool probe kernel). Same tables, model and fallback as M2x; paired deltas vs blend21 per set / view.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_v3b P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; run=$3; shift 3; OUT=$B/pcd_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) pcd evaluation $name ($run), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$run:$B/rank_v4b/lambdarank.txt:0 --main_of M2x=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --pcd_w 0.5 1 2 4 inf --pc_slots 4=4,8,12,16,20 2=2,4,6,8,10 --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"
done
$PY -X utf8 $B/pcl_boost_report.py $B/pcd_eval_panel $B/pcd_eval_p2dev $B/pcd_eval_devAB --prefix pcd --out $B/diag/pcd_report.md
$PY -X utf8 $B/pcl_boost_report.py $B/pcd_eval_panel $B/pcd_eval_p2dev $B/pcd_eval_devAB --prefix slot --out $B/diag/slot_report.md
echo "PCD_DONE $(date +%T)"
