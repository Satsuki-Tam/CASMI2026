#!/bin/bash
# 106 (iii) ICEBERG pilot: waits for the GL pilot (GPU), builds same-formula-group inputs for the same subset (icepilot106.py), runs the asset
# ice_runner.py on each, then x106_icepilot.py (exploratory reading fixed before the run).
set -u
cd ~/CASMI2026 || exit 1
B=experiments/b1_baseline; P=$B/diag/icepilot106; PY=~/CASMI2026/.venv/bin/python
until grep -q "GLPILOT_DONE" spark/jobs/spark_glpilot106.out 2>/dev/null; do sleep 30; done
$PY -X utf8 $B/icepilot106.py > $B/diag/icepilot106_select.log 2>&1 || { echo "ICEPILOT_FAIL select"; exit 1; }
cat $B/diag/icepilot106_select.log | tail -12
for f in $P/in_*.json; do
  n=$(basename $f .json); n=${n#in_}
  .venv-ice/bin/python data/external/iceberg/ice_runner.py data/external/iceberg $f $P/out_$n.json --device cuda --site none --budget 3600 > $P/ice_$n.log 2>&1
  echo "== $(date +%T) ice $n exit $? $(grep -a -o '"status": "[a-z]*"' $P/out_$n.json.meta.json | head -1)"
done
$PY -X utf8 $B/x106_icepilot.py > $P/x106_icepilot.log 2>&1; echo "== $(date +%T) x106 ice exit $?"
echo "ICEPILOT_DONE $(date +%T)"
