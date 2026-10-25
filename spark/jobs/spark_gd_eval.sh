#!/bin/bash
# Gated demotion (development, not a submission; 2026-10-25 19:30): when the best library similarity among the view's TRAINING candidates is >= theta,
# subtract w (z units) from the non-training candidates (N) or only the PubChem-tier-only ones (P). Grid fixed before results: N 0.6/0.7/0.8 x w 1/2/4
# (0.6 and 0.8 at w 2 only), P 0.7 x w 2/4. Same tables, model and fallback as M2x; paired deltas vs blend21. Waits for the pcd chain to finish.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "PCD_DONE" logs/spark_pcd_eval.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_v3b P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; run=$3; shift 3; OUT=$B/gd_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) gated demotion $name ($run), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$run:$B/rank_v4b/lambdarank.txt:0 --main_of M2x=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" \
    --gate_dem N:0.6:2 N:0.7:1 N:0.7:2 N:0.7:4 N:0.8:2 P:0.7:2 P:0.7:4 --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"
done
$PY -X utf8 $B/pcl_boost_report.py $B/gd_eval_panel $B/gd_eval_p2dev $B/gd_eval_devAB --prefix gd --out $B/diag/gd_report.md
echo "GD_DONE $(date +%T)"
