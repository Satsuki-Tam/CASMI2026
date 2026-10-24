#!/bin/bash
# B1 feature table + GLACIER/ICEBERG scores for one evaluation CSV, on the DGX Spark.
# Usage: bash b1_features_job.sh <eval_csv (repo-relative)> <run_dir (repo-relative)> <sets...>
# Detached launch: cd ~/CASMI2026 && setsid nohup bash spark/jobs/b1_features_job.sh experiments/p1_baseline/run1/p1_molecules.csv experiments/b1_baseline/run_p1 A_timstof B_nplib > logs/b1_run_p1.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
EVAL=$1; RUN=$2; shift 2
mkdir -p "$RUN/work"
echo "== $(date +%T) features for $EVAL -> $RUN sets $*"
.venv/bin/python -X utf8 experiments/b1_baseline/b1_features.py --eval_csv "$EVAL" --store data/processed/spectra_store --tier data/external/pubchem_tier \
  --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet \
  --v3 data/external/v3_models/code --out "$RUN" --k 100 --workers 16 --sets "$@" > "$RUN/features.log" 2>&1
echo "== $(date +%T) features exit $? : $(grep -a '^saved\|^done' "$RUN/features.log" | tr '\n' ' ' | cut -c1-200)"
for S in "$@"; do
  IN="$RUN/b1_runner_${S}_in.json"
  [ -s "$IN" ] || { echo "no runner input for $S"; continue; }
  echo "== GL $S start $(date +%T)" >> "$RUN/runners.log"
  .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier "$IN" "$RUN/work/gl_${S}.json" --device cuda --site none --budget 7200 > "$RUN/work/gl_${S}.log" 2>&1
  echo "== GL $S done $(date +%T) $(grep -o '"status": "[a-z]*"' "$RUN/work/gl_${S}.json.meta.json")" >> "$RUN/runners.log"
  echo "== ICE $S start $(date +%T)" >> "$RUN/runners.log"
  .venv-ice/bin/python data/external/iceberg/ice_runner.py data/external/iceberg "$IN" "$RUN/work/ice_${S}.json" --device cuda --site none --budget 7200 > "$RUN/work/ice_${S}.log" 2>&1
  echo "== ICE $S done $(date +%T) $(grep -o '"status": "[a-z]*"' "$RUN/work/ice_${S}.json.meta.json")" >> "$RUN/runners.log"
done
echo "ALLDONE $(date +%T)" >> "$RUN/runners.log"
.venv/bin/python -X utf8 experiments/b1_baseline/b1_evaluate.py --run "$RUN" --eval_csv "$EVAL" --sets "$@" > "$RUN/evaluate.log" 2>&1
echo "== $(date +%T) evaluate exit $?"; cat "$RUN/results/b1_results.md"
