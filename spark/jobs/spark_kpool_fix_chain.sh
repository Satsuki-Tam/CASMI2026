#!/bin/bash
# Codex 020: re-run the W7 A/B pool-branch features with the view-specific pool eligibility (the first run gave the truth a C2 pool slot
# for a pool entry that exists only because it is a training structure). GL seeded from the first pool run (complete molecules reused).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "KPOOL_DONE" logs/spark_kpool_chain.log 2>/dev/null; do sleep 120; done
RUN=$B/run_v3b_eval_pool2; mkdir -p $RUN/work
echo "== $(date +%T) features $RUN (fixed eligibility, --k_pool 60; features sha $(sha256sum $B/b1_features.py | cut -c1-16))"
$PY -X utf8 $B/b1_features.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 \
  --k_fpp 200 --k_pop 50 --k_pool 60 --sets A_timstof B_nplib > $RUN/features.log 2>&1
echo "features exit $?"
for S in A_timstof B_nplib; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --seed $B/run_v3b_eval_pool/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py \
    data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== gl $S $(grep -o '"status": "[a-z]*"' $RUN/work/gl_${S}.json.meta.json) $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-120)"
done
OUT=$B/pool_eval_devAB_fix; rm -rf $OUT; mkdir -p $OUT
OMP_NUM_THREADS=2 $PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/eval_set/p1_molecules.csv --cands M2x:$B/run_v3b_eval:$B/rank_v4b/lambdarank.txt:0 M2x_pool:$RUN:$B/rank_v4b/lambdarank.txt:0 \
  --main_of M2x=blend21 M2x_pool=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets A_timstof B_nplib --out $OUT > $OUT/eval.log 2>&1
echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md | cut -c1-160
echo "KPOOL_FIX_DONE $(date +%T)"
