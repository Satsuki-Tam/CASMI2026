#!/bin/bash
# 115: resumes (SIGCONT) M_all CPU generators that were paused (SIGSTOP) under the pre-fixed stop condition (c) while the 111 serial training ran.
# Waits until experiments/n111/r1/train_status.txt holds a terminal line (N111_TRAIN_DONE / N111_TRAIN_FAIL) and no train_n111.py process is left,
# then, for each PID, re-checks that it is still the same M_all generator (command line contains its prefix) before resuming it.
# Usage: nohup bash experiments/e115/gen_resume.sh <pid>:<prefix> [<pid>:<prefix> ...] &   -> experiments/e115/mall_sim/gen_resume.log
cd ~/CASMI2026 || exit 1
LOG=experiments/e115/mall_sim/gen_resume.log
echo "== $(date "+%F %T") waiting for the 111 training to end; will resume: $*" >> $LOG
while ! grep -q -E "^N111_TRAIN_(DONE|FAIL)" experiments/n111/r1/train_status.txt 2>/dev/null || pgrep -f "^[^ ]*python[^ ]* experiments/n111/train_n111.py" >/dev/null; do sleep 60; done
for a in "$@"; do pid=${a%%:*}; pf=${a#*:}
  if tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null | grep -q -- "experiments/e115/gl_simulate.py data/external/glacier experiments/e115/mall/jobs.json $pf --device cpu"; then
    kill -CONT $pid && echo "== $(date "+%F %T") resumed $pid ($pf)" >> $LOG
  else echo "== $(date "+%F %T") $pid is not the generator of $pf any more; not touched" >> $LOG; fi
done
