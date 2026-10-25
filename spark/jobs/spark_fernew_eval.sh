#!/bin/bash
# Codex 026 / 026_decision section 2 (pre-registered before the run): full_eval tables x rank_rk_fx (FE_new) vs full_eval x rank_v4b (M2x_fe =
# submitted 57630996) vs the fold-0 M2x control, registered main output blend21 + GL fallback; existing features and forward outputs, no GPU.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
echo "== $(date +%T) models: rank_v4b $(sha256sum $B/rank_v4b/lambdarank.txt | cut -c1-12), rank_rk_fx $(sha256sum $B/rank_rk_fx/lambdarank.txt | cut -c1-12)"
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_fe run_panel_v3b P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_fe run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval_fe run_v3b_eval A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; fe=$3; base=$4; shift 4; OUT=$B/fernew_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) $name: M2x_fe ($fe + rank_v4b) / M2x ($base + rank_v4b) / FE_new ($fe + rank_rk_fx), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x_fe:$B/$fe:$B/rank_v4b/lambdarank.txt:0 M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 FE_new:$B/$fe:$B/rank_rk_fx/lambdarank.txt:0 \
    --main_of M2x_fe=blend21 M2x=blend21 FE_new=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-170
done
echo "FERNEW_DONE $(date +%T)"
