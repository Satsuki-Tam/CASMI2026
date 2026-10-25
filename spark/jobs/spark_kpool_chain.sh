#!/bin/bash
# Pool-window shortlist branch, end-to-end pair comparison (2026-10-25): feature tables with --k_pool 60 (everything else = M2x configuration)
# on the dev sets A/B, the C1 dev set (eval_c1), dev2 v2 (all strata) and the panel; GL seeded from the existing M2x runs with --reuse_complete
# (only molecules whose candidate set changed are re-scored, completely). Registered comparison M2x (no pool branch) vs M2x_pool (pool branch),
# same ranker rank_v4b, main blend21, fallback unchanged. Gain to look for: C1 views (class-1 proxy); protected: all C2 views, epsilon 0.02.
# Waits for the pool audit so that the GPU is shared by at most two jobs.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "POOLAUDIT_DONE" logs/spark_poolaudit.log 2>/dev/null; do sleep 120; done
run_feats() {   # run_feats <eval_csv> <out_run> <seed_run> <sets...>
  local EVAL=$1 RUN=$2 SEED=$3; shift 3
  echo "== $(date +%T) features $RUN (--k_pool 60; GL seeded from $SEED) sets $*"
  mkdir -p $RUN/work
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --k_pool 60 --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features exit $? : $(grep -a '^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-160)"
  for S in "$@"; do
    IN=$RUN/b1_runner_${S}_in.json; [ -s $IN ] || { echo "no runner input for $S"; continue; }
    .venv-ice/bin/python spark/jobs/ice_resume.py --seed $SEED/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== gl $S $(grep -o '"status": "[a-z]*"' $RUN/work/gl_${S}.json.meta.json) $(grep -a '\[resume\] reusing\|\[resume\] done' $RUN/work/gl_${S}_resume.log | tr '\n' ' ' | cut -c1-160)"
  done
}
run_feats $B/eval_set/p1_molecules.csv $B/run_v3b_eval_pool $B/run_v3b_eval A_timstof B_nplib
run_feats $B/eval_c1/p1_molecules.csv $B/run_v3b_c1_pool $B/run_v3b_c1 B_nplib
run_feats $B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_pool $B/run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib
export OMP_NUM_THREADS=2
for E in "devAB $B/eval_set/p1_molecules.csv run_v3b_eval run_v3b_eval_pool A_timstof B_nplib" "c1set $B/eval_c1/p1_molecules.csv run_v3b_c1 run_v3b_c1_pool B_nplib" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 run_p2dev_pool C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$2; base=$3; pr=$4; shift 4; OUT=$B/pool_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name: M2x vs M2x_pool (k_pool 60), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 M2x_pool:$B/$pr:$B/rank_v4b/lambdarank.txt:0 --main_of M2x=blend21 M2x_pool=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-160
done
echo "KPOOL_DONE $(date +%T)"
