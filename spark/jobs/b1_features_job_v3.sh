#!/bin/bash
# B1 v3 feature table + forward scores for one evaluation CSV on the DGX Spark: wider FP+prior branch (200) and a prior-only branch (50),
# GLACIER only by default (the fixed rule is no better with ICEBERG on every development set, 2026-10-24). Runners go through the
# resumable driver (GB10 CUDA crashes). Usage: FEAT_ARGS="--k_fpp 200 --k_pop 50" RUNNERS="gl" bash b1_features_job_v3.sh <eval_csv> <run_dir> <sets...>
set -u
cd ~/CASMI2026 || exit 1
EVAL=$1; RUN=$2; shift 2; FEAT_ARGS=${FEAT_ARGS:-"--k_fpp 200 --k_pop 50"}; RUNNERS=${RUNNERS:-gl}
mkdir -p "$RUN/work"
echo "== $(date +%T) features for $EVAL -> $RUN sets $* [$FEAT_ARGS; runners $RUNNERS]"
.venv/bin/python -X utf8 experiments/b1_baseline/b1_features.py --eval_csv "$EVAL" --store data/processed/spectra_store --tier data/external/pubchem_tier \
  --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet \
  --v3 data/external/v3_models/code --out "$RUN" --k 100 --workers 16 $FEAT_ARGS --sets "$@" > "$RUN/features.log" 2>&1
echo "== $(date +%T) features exit $? : $(grep -a '^saved\|^done' "$RUN/features.log" | tr '\n' ' ' | cut -c1-200)"
for S in "$@"; do
  IN="$RUN/b1_runner_${S}_in.json"
  [ -s "$IN" ] || { echo "no runner input for $S"; continue; }
  for R in $RUNNERS; do
    if [ "$R" = gl ]; then PKG=data/external/glacier; SCR=gl_runner.py; else PKG=data/external/iceberg; SCR=ice_runner.py; fi
    echo "== $R $S start $(date +%T)" >> "$RUN/runners.log"
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python $PKG/$SCR $PKG "$IN" "$RUN/work/${R}_${S}.json" -- --device cuda --site none --budget 7200 > "$RUN/work/${R}_${S}_resume.log" 2>&1
    echo "== $R $S done $(date +%T) $(grep -o '"status": "[a-z]*"' "$RUN/work/${R}_${S}.json.meta.json") $(grep -a '\[resume\] done' "$RUN/work/${R}_${S}_resume.log" | cut -c1-80)" >> "$RUN/runners.log"
  done
done
echo "ALLDONE $(date +%T)" >> "$RUN/runners.log"
.venv/bin/python -X utf8 experiments/b1_baseline/b1_evaluate.py --run "$RUN" --eval_csv "$EVAL" --sets "$@" > "$RUN/evaluate.log" 2>&1
echo "== $(date +%T) evaluate exit $?"; grep -a "^## \|^| S(2,0,0.5) |\|^| S(2,1,0.5) |\|libpri(tau=0.9,m=0.2)" "$RUN/results/b1_results.md" | cut -c1-200
