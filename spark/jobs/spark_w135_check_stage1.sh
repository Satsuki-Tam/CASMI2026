#!/bin/bash
# W135 (136_decision.md §8): after the v2 rebuild of the pi3 = 0.3 design worlds, run w135_world_check.py on each (exit values collected); only
# when all six PASS, start spark_w135_stage1_v2.sh (full mode + reader v2 --decide).
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1
until grep -q "W135_P30_V2_DONE\|W135_REBUILD_FAIL" logs/w135_rebuild.log 2>/dev/null; do sleep 30; done
grep -q "W135_REBUILD_FAIL" logs/w135_rebuild.log && { echo "W135_CHECK_FAIL rebuild failed $(date '+%F %T')"; exit 1; }
FAIL=0
for b in dF1 dF2 dF3 dR1 dR2 dR3; do
  $PY -X utf8 experiments/w135/w135_world_check.py --world experiments/w135/worlds/${b}_p30 --set $b > experiments/w135/worlds/${b}_p30/world_check.log 2>&1; rc=$?
  echo "== $(date +%T) world check $b exit $rc $(grep -h 'WORLD_CHECK\|c1_keys' experiments/w135/worlds/${b}_p30/world_check.log | tr '\n' ' ' | cut -c1-220)"
  [ $rc -eq 0 ] || FAIL=1
done
[ $FAIL -eq 0 ] || { echo "W135_CHECK_FAIL world check $(date '+%F %T')"; exit 1; }
echo "W135_CHECK_PASS $(date '+%F %T')"
bash spark/jobs/spark_w135_stage1_v2.sh
