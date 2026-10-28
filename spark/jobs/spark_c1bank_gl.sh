#!/bin/bash
# 112: GLACIER for the c1dev bank tables, moved to the SERIAL evaluation phase (Codex 113): the first attempt (spark_c1bank.sh) shared the GPU with
# two trainings, crashed once (GB10 cudaErrorIllegalAddress) and was stopped at 22:05. This job waits until both trainings have ended and the
# 110 evaluation has a terminal status, then recomputes the bank's GLACIER from scratch for every set (ice_resume, same runner arguments),
# audits it (gl_audit.py) and appends C1BANK_DONE / C1BANK_FAIL to spark_c1bank.out (the 111 evaluation waits for that line).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; PYI=$HOME/CASMI2026/.venv-ice/bin/python; RUN=$B/run_c1bankdev_f1; OUT=spark/jobs/spark_c1bank.out
STF=$RUN/c1bank_status.txt; RID="c1bank_gl $(date '+%F %T') pid $$"; rm -f $STF
fail() { echo "C1BANK_FAIL $* $(date '+%F %T') [$RID]" | tee -a $OUT | tee $STF; exit 1; }
while pgrep -f "[t]rain_fivefold.py.*--tag fpnet_f1s1" >/dev/null || pgrep -f "[s]park_n111_train.sh" >/dev/null; do sleep 120; done
while [ ! -s $B/diag/x110_status.txt ]; do pgrep -f "[s]park_x110.sh" >/dev/null || break; sleep 120; done
echo "== $(date '+%F %T') bank GLACIER start (110 status: $(cat $B/diag/x110_status.txt 2>/dev/null))" | tee -a $OUT
CSV=$B/c1bank_f1/c1dev/p2_molecules.csv; SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$CSV').set.unique())))")
A=""
for S in $SETS; do
  mkdir -p $RUN/work/stopped_2205; for f in $RUN/work/gl_${S}.json $RUN/work/gl_${S}.json.meta.json $RUN/work/gl_${S}.json.part* $RUN/work/gl_${S}_resume.log; do [ -e "$f" ] && mv "$f" $RUN/work/stopped_2205/; done   # keep the stopped attempt
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1; rc=$?
  echo "== $(date +%T) gl $S rc=$rc $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)" | tee -a $OUT; [ $rc -eq 0 ] || fail "gl $S rc=$rc"
  A="$A $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json"
done
$PYI -X utf8 $B/gl_audit.py $A > $RUN/gl_audit.log 2>&1; rc=$?; cat $RUN/gl_audit.log >> $OUT; [ $rc -eq 0 ] || fail "bank GLACIER audit"
echo "C1BANK_DONE $(date '+%F %T') [$RID]" | tee -a $OUT | tee $STF
