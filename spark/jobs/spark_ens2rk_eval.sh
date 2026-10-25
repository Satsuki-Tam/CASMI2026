#!/bin/bash
# 028_decision section 4 (pre-registered before the run): ENS2 tables x frozen rank_rk_fx (bundle), vs the working baseline M2x_fe and the
# cumulative reference M2x, plus ENS2 x rank_v4b and full_eval x rank_rk_fx for the 2x2; registered evaluator, main blend21 + GL fallback.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "panel $B/panel_np250/p1_molecules.csv run_ens2_panel run_panel_fe run_panel_v3b P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_ens2_p2dev run_p2dev_fe run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$2; ens=$3; fe=$4; base=$5; shift 5; OUT=$B/ens2rk_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) $name: M2x_fe / M2x / ENS2 (v4b) / FE_new (rk_fx) / ENS2_new (rk_fx), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x_fe:$B/$fe:$B/rank_v4b/lambdarank.txt:0 M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 ENS2:$B/$ens:$B/rank_v4b/lambdarank.txt:0 \
    FE_new:$B/$fe:$B/rank_rk_fx/lambdarank.txt:0 ENS2_new:$B/$ens:$B/rank_rk_fx/lambdarank.txt:0 \
    --main_of M2x_fe=blend21 M2x=blend21 ENS2=blend21 FE_new=blend21 ENS2_new=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-170
done
echo "ENS2RK_DONE $(date +%T)"
