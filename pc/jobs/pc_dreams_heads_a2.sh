#!/bin/bash
# 089 stage (a) under the Codex 088 contract: train the fold-1 / fold-2 heads (registered config, no built-in eval), then dreams_fp_eval.py on each.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "DREAMS_EMBED_DONE" logs/pc_dreams_embed.log 2>/dev/null; do sleep 20; done
export OMP_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
for K in 1 2; do
  $PY -X utf8 $B/dreams_fp_train.py --holdout_fold $K --out $B/dreams_fp_f$K --eval 0 > logs/dreams_fp_f$K.log 2>&1
  echo "== $(date +%T) dreams head fold $K exit $? $(grep -a 'step 29999' logs/dreams_fp_f$K.log | cut -c1-120)"
done
for K in 1 2; do
  $PY -X utf8 $B/dreams_fp_eval.py --fold $K --head $B/dreams_fp_f$K/head.pt --out $B/dreams_fp_eval_f$K > logs/dreams_fp_eval_f$K.log 2>&1
  echo "== $(date +%T) dreams eval fold $K exit $?"
done
echo "DREAMS_A_DONE $(date +%T)"
