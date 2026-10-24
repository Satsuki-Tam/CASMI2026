#!/bin/bash
# W7: the submission pipeline itself on the development eval set (C2 and C1 proxies; learned main = rank_v2, fixed insurance), then the parity test.
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; E=$B/eval_test_set; PY=.venv/bin/python
git fetch -q origin && git checkout -q origin/main -- $B/b1_pipeline.py $B/b1_parity.py $B/b1_rankfeats.py $B/b1_common.py src/metric.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
for f in test.parquet exclude_rows_c1.json exclude_identities_c2.json solution.csv; do [ -s $E/$f ] || { echo "missing $E/$f"; exit 1; }; done
for mode in c2 c1; do
  if [ "$mode" = c2 ]; then M="--exclude_identities $E/exclude_identities_c2.json --exclude_rows $E/exclude_rows_c1.json"; else M="--exclude_rows $E/exclude_rows_c1.json"; fi
  echo "== $(date +%T) pipeline eval $mode (learned main + fixed insurance)"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 16 --folds 0 $M --solution $E/solution.csv --rank_model $B/rank_v2/lambdarank.txt > $E/run_$mode.log 2>&1
  echo "== $(date +%T) exit $? : $(grep -a 'OFFICIAL\|Traceback\|Error' $E/run_$mode.log | tail -2 | cut -c1-300)"
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $B/run1_v2 --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_$mode.md 2>&1 | cut -c1-240
  echo "-- eval_scores: $(tr -d '\n ' < $E/run_$mode/eval_scores.json 2>/dev/null | cut -c1-500)"
done
echo "PIPEEVAL2_DONE $(date +%T)"
