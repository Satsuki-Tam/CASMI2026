#!/bin/bash
# Offline E0 (public 0.464 lineage) on OUR molecules (Codex 015 (a)). Usage:
#   bash spark/jobs/spark_e0_offline.sh <run_name> <test.parquet> <train.parquet> [limit_molecules]
# env: REUSE_FROM=<earlier work dir of the same inputs> (reuse engine lists / base lists / ICE-GL / N1 caches), ICE_BUDGET GL_BUDGET N1_BUDGET (seconds; defaults generous so coverage is not truncated), NUMBA_THREADS (default 4 = Kaggle's CPU count),
#      RECEIPT=1 also runs the notebook's input-inventory cell 23. Shared inputs (dataset mirrors, class-2 proxy train) come from
#   .venv/bin/python -I experiments/e0_offline/e0_prepare.py shared --root ~/CASMI2026 --shared experiments/e0_offline/runs/_shared --eval_dir experiments/b1_baseline/eval_test_full3
set -u
cd ~/CASMI2026 || exit 1
RUN=$1; TEST=$2; TRAIN=$3; LIMIT=${4:-0}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=${NUMBA_THREADS:-4} PYTHONUNBUFFERED=1 PYTHONHASHSEED=0
E=experiments/e0_offline; R=$E/runs/$RUN; mkdir -p "$R" logs
echo "== $(date -Is) E0 offline run $RUN test=$TEST train=$TRAIN limit=$LIMIT budgets ice=${ICE_BUDGET:-21600} gl=${GL_BUDGET:-10800} n1=${N1_BUDGET:-3600} numba_threads=$NUMBA_NUM_THREADS"
.venv/bin/python -I $E/e0_prepare.py run --root ~/CASMI2026 --shared $E/runs/_shared --run_dir "$R" --test "$TEST" --train "$TRAIN" --limit "$LIMIT" || { echo "E0_RUN FAILED: prepare"; exit 1; }
.venv/bin/python -X utf8 $E/run_e0_offline.py --cells $E/cells --input "$R/kaggle_input" --work "$R/work" --runner_python .venv-ice/bin/python --resume spark/jobs/ice_resume.py \
  --ice_budget "${ICE_BUDGET:-21600}" --gl_budget "${GL_BUDGET:-10800}" --n1_budget "${N1_BUDGET:-3600}" ${RECEIPT:+--receipt} ${REUSE_FROM:+--reuse "$REUSE_FROM"}
rc=$?
echo "E0_RUN_DONE $RUN rc=$rc $(date -Is)"
exit $rc
