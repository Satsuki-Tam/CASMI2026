#!/bin/bash
# 144 E2: train (e2_train.py, fold 3 / 4 pool tables) as soon as the six training feature tables exist, then the registered development
# reading (e2_eval.py, 144_prereg_e2.md v2) as soon as the five development feature tables exist.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1; O=experiments/e2/ewin; M=experiments/e2/model_v1
TR="train_pool_f3a train_pool_f3b np061_f3pool train_pool_f4a train_pool_f4b np061_f4pool"; DV="np053_f1dev np053_f2dev eval_set_f1 eval_set_f2 panel_np250"
waitall() { for d in $1; do until [ -f $O/$d/e2f_manifest.json ]; do grep -q E2_FEATS_FAIL logs/spark_e2_feats2.log 2>/dev/null && { echo "== $(date +%T) features failed"; return 1; }; sleep 30; done; done; }
waitall "$TR" || { echo "E2_TRAIN_FAIL"; exit 1; }
echo "== $(date +%T) training tables ready"; [ -e $M/e2_lgb.txt ] && { echo "refused: $M exists"; exit 1; }
$PY -X utf8 experiments/e2/e2_train.py --out $M > $M.log 2>&1; rc=$?; tail -12 $M.log; [ $rc = 0 ] || { echo "E2_TRAIN_FAIL $(date +%T)"; exit 1; }
waitall "$DV" || { echo "E2_EVAL_FAIL"; exit 1; }
echo "== $(date +%T) development tables ready"
$PY -X utf8 experiments/e2/e2_eval.py --model $M/e2_lgb.txt --out experiments/e2/eval_v1 > experiments/e2/eval_v1.log 2>&1; rc=$?
[ $rc = 0 ] && echo "E2_EVAL_DONE $(date '+%F %T')" || { echo "E2_EVAL_FAIL $(date '+%F %T')"; tail -5 experiments/e2/eval_v1.log; exit 1; }
