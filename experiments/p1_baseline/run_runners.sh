#!/bin/bash
# Run GLACIER then ICEBERG on each P1 shortlist as soon as the funnel has written the runner input. Usage: run_runners.sh <run_dir> <set> [<set> ...]
RUN=$1; shift
PY=/c/kaggle/CASMI/.venv-ice/Scripts/python.exe
mkdir -p "$RUN/work"
for S in "$@"; do
  IN="$RUN/p1_runner_${S}_in.json"
  while [ ! -s "$IN" ]; do sleep 30; done
  sleep 5
  echo "== GL $S start $(date +%T)"
  "$PY" /c/kaggle/CASMI/data/external/glacier/gl_runner.py /c/kaggle/CASMI/data/external/glacier "$IN" "$RUN/work/gl_${S}.json" --device cuda --site none --budget 7200 > "$RUN/work/gl_${S}.log" 2>&1
  echo "== GL $S done $(date +%T) $(grep -o '"status": "[a-z]*"' "$RUN/work/gl_${S}.json.meta.json")"
  echo "== ICE $S start $(date +%T)"
  "$PY" /c/kaggle/CASMI/data/external/iceberg/ice_runner.py /c/kaggle/CASMI/data/external/iceberg "$IN" "$RUN/work/ice_${S}.json" --device cuda --site none --budget 7200 > "$RUN/work/ice_${S}.log" 2>&1
  echo "== ICE $S done $(date +%T) $(grep -o '"status": "[a-z]*"' "$RUN/work/ice_${S}.json.meta.json")"
done
echo ALLDONE $(date +%T)
