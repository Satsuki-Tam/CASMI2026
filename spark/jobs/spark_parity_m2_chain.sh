#!/bin/bash
# Parity for candidate M2 (Codex 010): once the v3 chain has trained rank_v3 (features run_v3_eval exist), run the 50-molecule parity with
# the M2 configuration (FP+prior 200, prior 50, GLACIER only, rank_v3). Gate for the locked opening together with the v3 artifacts.
cd ~/CASMI2026 || exit 1
until grep -q "V3_TRAIN_DONE" logs/spark_v3_chain.log 2>/dev/null; do sleep 180; done
[ -s experiments/b1_baseline/rank_v3/lambdarank.txt ] || { echo "PARITY_M2 FAILED: rank_v3 model missing"; exit 1; }
CAND=M2 bash spark/jobs/spark_parity50_chain.sh
rc=$?; [ $rc = 0 ] && echo "PARITY_M2_DONE $(date +%T)" || echo "PARITY_M2 FAILED rc=$rc"
