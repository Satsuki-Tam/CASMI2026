#!/bin/bash
# 066 diagnostic on the EXT benchmark (all models unseen): FPNet choice with rank_v4b fixed -- F (full_eval, from 065), P (5 public folds,
# logit mean via --folds 0,1,2,3,4), single public fold0 (--folds 0).
set -u
cd ~/CASMI2026 || exit 1
until grep -q "EXT065_DONE" logs/spark_ext065.log 2>/dev/null; do sleep 30; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_ana035; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_ext110
for V in "P:0,1,2,3,4" "f0:0"; do
  N=${V%%:*}; FO=${V#*:}; W=$E/run_fp_$N
  nice -n 5 $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 6 --solution $E/solution.csv --rank_model $B/rank_v4b/lambdarank.txt --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --folds $FO --analog_w 0.5 --analog_feat ap > $W.log 2>&1
  echo "== $(date +%T) $N exit $? $(grep -a 'FPNet folds\|submission written' $W.log | tr '\n' ' ' | cut -c1-240)"
done
echo "EXT066_DONE $(date +%T)"
