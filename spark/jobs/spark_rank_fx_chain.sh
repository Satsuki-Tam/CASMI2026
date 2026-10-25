#!/bin/bash
# Codex 019: fixed-hyperparameter pair comparisons (no re-search). The selected params + rounds of the frozen rank_v4b are reused for every
# model, so each comparison changes only the training rows:
#   rank_v4b_fx      = rank_v4b's tables and flags, params fixed  -> must reproduce rank_v4b (prediction check)
#   rank_v6g_fx      = + fold-0 G-type fit pool (72 identities), C1 x3 like the rest
#   rank_v6g_fx_w1   = + G fit pool with G's C1 groups x1 ('G C1 weight reduced'), other C1 groups x3
# Registered evaluation vs the frozen rank_v4b (main blend21) on dev2 (all strata), dev A/B (fit/tune/eval reported) and the panel.
# Pre-registered (017 + 019): gain = dev2 G/C1; protected = G/C2, C/C1, C/C2, D/C2, A/B C2 + C1, panel both views; epsilon 0.02.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; P0=$B/rank_v4b/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
RUNSG="$RUNS0 $B/run_fitpool_v3:$B/eval_set2/fit_pool/fit_molecules.csv:fit"
echo "== $(date +%T) fixed-param training (trainer sha $(sha256sum $B/b1_rank_train.py | cut -c1-16); params from $P0)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 --out $B/rank_v4b_fx --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 > $B/rank_v4b_fx_train.log 2>&1; echo "v4b_fx exit $?"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNSG --out $B/rank_v6g_fx --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 > $B/rank_v6g_fx_train.log 2>&1; echo "v6g_fx exit $?"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNSG --out $B/rank_v6g_fx_w1 --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_fitpool_v3=1 --params_from $P0 > $B/rank_v6g_fx_w1_train.log 2>&1; echo "v6g_fx_w1 exit $?"
for m in v4b_fx v6g_fx v6g_fx_w1; do echo "-- rank_$m: $(grep -a 'params fixed\|fit groups after\|per-run c1' $B/rank_${m}_train.log | tr '\n' ' ' | cut -c1-220)"; done
# reproduction check: rank_v4b_fx must predict exactly like the frozen rank_v4b on the dev tables
$PY - <<'PY'
import lightgbm as lgb, numpy as np, pandas as pd, sys
sys.path.insert(0, "experiments/b1_baseline")
a = lgb.Booster(model_file="experiments/b1_baseline/rank_v4b/lambdarank.txt"); b = lgb.Booster(model_file="experiments/b1_baseline/rank_v4b_fx/lambdarank.txt")
X = np.random.default_rng(0).normal(size=(20000, a.num_feature()))
d = np.abs(a.predict(X) - b.predict(X)).max(); print("REPRO rank_v4b vs rank_v4b_fx: trees", a.num_trees(), b.num_trees(), "| max |pred diff| on 20k random rows", float(d), "->", "IDENTICAL" if d < 1e-9 else "DIFFERENT")
PY
export OMP_NUM_THREADS=2
for E in "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval A_timstof B_nplib" "panel $B/panel_np250/p1_molecules.csv run_panel_v3b P_np250"; do
  set -- $E; name=$1; csv=$2; run=$3; shift 3; OUT=$B/pair_fx_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name (sets $*)"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$run:$B/rank_v4b/lambdarank.txt:0 Gfx:$B/$run:$B/rank_v6g_fx/lambdarank.txt:0 Gfx1:$B/$run:$B/rank_v6g_fx_w1/lambdarank.txt:0 \
    --main_of M2x=blend21 Gfx=blend21 Gfx1=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-160
done
echo "FX_DONE $(date +%T)"
