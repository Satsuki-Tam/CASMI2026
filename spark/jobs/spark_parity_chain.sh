#!/bin/bash
# W7 parity after the post-chain's pipeline evaluation: the pipeline's candidate dumps (C2 / C1 proxies) vs the evaluator's feature tables (run1_v2).
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; E=$B/eval_test_set; PY=.venv/bin/python
until grep -q "PIPEEVAL_DONE" logs/spark_post_chain.log 2>/dev/null; do sleep 300; done
git fetch -q origin && git checkout -q origin/main -- $B/b1_parity.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
for mode in c2 c1; do
  echo "== $(date +%T) parity $mode"
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $B/run1_v2 --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_$mode.md 2>&1 | cut -c1-240
  echo "-- official scores of the pipeline run: $(cat $E/run_$mode/eval_scores.json 2>/dev/null | tr -d '\n ' | cut -c1-400)"
done
echo "PARITY_DONE $(date +%T)"
