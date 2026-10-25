#!/bin/bash
# Codex 017 proposal 2: ONE-PAIR comparison rank_v4b vs rank_v6g = rank_v4b's recipe (same tables, v2_noice, drop lib_nref in_train, c1_repeat 3)
# plus the fold-0 G-type fit pool (timsTOF query + other-library references; identity groups disjoint from dev2/locked2 and every earlier set).
# Everything else fixed (query, shortlist, features, hyperparameters, blend21 + GL-cover fallback). Registered-output evaluation on dev2 (all
# strata, both views), the dev sets A/B and the panel with b1_locked_eval.py (main_of = blend21 for both). Pre-registered protections (017):
# gain to confirm = dev2 G/C1 blend21; protect G/C2, C/D C2, A/B C2 + C1, panel both views; epsilon 0.02. Waits for the fit-pool features.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "FITPOOL_DONE\|FITPOOL FAILED" logs/spark_fitpool_chain.log 2>/dev/null; do sleep 300; done
grep -q "FITPOOL FAILED" logs/spark_fitpool_chain.log && { echo "V6G ABORTED: fit pool failed"; exit 1; }
[ -s $B/run_fitpool_v3/b1_features_G_tims_crosslib.parquet ] || { echo "V6G FAILED: no G feature table"; exit 1; }
RUNS="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv $B/run_fitpool_v3:$B/eval_set2/fit_pool/fit_molecules.csv:fit"
echo "== $(date +%T) train rank_v6g (rank_v4b recipe + fit pool G; trainer sha $(sha256sum $B/b1_rank_train.py | cut -c1-16))"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_v6g --feats v2_noice --drop lib_nref in_train --c1_repeat 3 > $B/rank_v6g_train.log 2>&1; echo "train exit $?"
grep -a "^USED\|^features\|fit groups\|WARNING" $B/rank_v6g_train.log | cut -c1-220
# control: retrain rank_v4b's recipe with the new trainer (set discovery) to show the baseline is reproduced (same tables -> same model up to determinism)
$PY -X utf8 $B/b1_rank_train.py --runs "$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv" --out $B/rank_v4b_repro --feats v2_noice --drop lib_nref in_train --c1_repeat 3 > $B/rank_v4b_repro_train.log 2>&1
echo "rank_v4b reproduction: fit groups $(grep -a 'fit groups' $B/rank_v4b_repro_train.log | cut -c1-80) | model sha original $(sha256sum $B/rank_v4b/lambdarank.txt | cut -c1-12) repro $(sha256sum $B/rank_v4b_repro/lambdarank.txt | cut -c1-12)"
export OMP_NUM_THREADS=2
for E in "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval A_timstof B_nplib" "panel $B/panel_np250/p1_molecules.csv run_panel_v3b P_np250"; do
  set -- $E; name=$1; csv=$2; run=$3; shift 3; OUT=$B/pair_v6g_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name (sets $*)"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$run:$B/rank_v4b/lambdarank.txt:0 M6g:$B/$run:$B/rank_v6g/lambdarank.txt:0 --main_of M2x=blend21 M6g=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED\|^| " $OUT/*.md 2>/dev/null | grep -a "REGISTERED\|M6g\|M2x" | cut -c1-200 | head -40
done
echo "V6G_DONE $(date +%T)"
