#!/bin/bash
# Codex 024: after spark_fullrk_chain.sh, the 2x2 ranker x Pc-demotion comparison on the full_rk tables (A = rank_v4b, B = rank_v4b + pcd0.5,
# C = rank_rk_fx, D = rank_rk_fx + pcd0.5; same FPNet, candidates, forward, fallback). Waits for FULLRK_DONE.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "FULLRK_DONE\|FULLRK FAILED" logs/spark_fullrk_chain.log 2>/dev/null; do sleep 120; done
grep -q "FULLRK FAILED" logs/spark_fullrk_chain.log && { echo "RK2X2 SKIPPED: chain failed"; exit 1; }
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "panel $B/panel_np250/p1_molecules.csv run_rk_panel P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_rk_p2dev C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_rk_eval A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; run=$3; shift 3; OUT=$B/rk2x2_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) 2x2 $name ($run), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands RK_old:$B/$run:$B/rank_v4b/lambdarank.txt:0 RK_new:$B/$run:$B/rank_rk_fx/lambdarank.txt:0 --main_of RK_old=blend21 RK_new=blend21 \
    --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --pcd_w 0.5 --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"
done
$PY -X utf8 $B/twobytwo_report.py $B/rk2x2_panel $B/rk2x2_p2dev $B/rk2x2_devAB --out $B/diag/rk_2x2.md
echo "RK2X2_DONE $(date +%T)"
