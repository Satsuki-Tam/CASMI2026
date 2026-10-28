#!/bin/bash
# 106 GL-summary pilot: subset selection (glpilot106.py) -> GLACIER re-run with per-spectrum detail (gl_runner_detail.py = the asset runner with an
# extra CSV; scoring unchanged) on each subset input -> x106_glpilot.py (exploratory reading fixed before the run).
set -u
cd ~/CASMI2026 || exit 1
B=experiments/b1_baseline; P=$B/diag/glpilot106; PY=~/CASMI2026/.venv/bin/python
$PY -X utf8 $B/glpilot106.py > $B/diag/glpilot106_select.log 2>&1 || { echo "GLPILOT_FAIL select"; exit 1; }
tail -2 $B/diag/glpilot106_select.log
for f in $P/in_*.json; do
  n=$(basename $f .json); n=${n#in_}
  .venv-ice/bin/python $B/gl_runner_detail.py data/external/glacier $f $P/out_$n.json --device cuda --site none --budget 3600 --detail $P/detail_$n.csv > $P/gl_$n.log 2>&1
  echo "== $(date +%T) gl $n exit $? $(grep -a -o '"status": "[a-z]*"' $P/out_$n.json.meta.json | head -1) $(wc -l < $P/detail_$n.csv 2>/dev/null) detail rows"
done
$PY -X utf8 $B/x106_glpilot.py > $P/x106_glpilot.log 2>&1; echo "== $(date +%T) x106 exit $?"
echo "GLPILOT_DONE $(date +%T)"
