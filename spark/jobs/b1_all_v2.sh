#!/bin/bash
# B1 v2 (Codex 006 fixes): rebuild features + forward models + fixed-rule evaluation for the three evaluation runs, sequentially.
# Detached launch: cd ~/CASMI2026 && setsid nohup bash spark/jobs/b1_all_v2.sh > logs/b1_all_v2.log 2>&1 < /dev/null &
cd ~/CASMI2026 || exit 1
git pull -q --ff-only; echo "== $(date +%T) code $(git log --oneline -1)"
for job in "experiments/b1_baseline/eval_set/p1_molecules.csv experiments/b1_baseline/run1_v2 A_timstof B_nplib" \
           "experiments/b1_baseline/eval_c1/p1_molecules.csv experiments/b1_baseline/run_c1_v2 B_nplib" \
           "experiments/p1_baseline/run1/p1_molecules.csv experiments/b1_baseline/run_p1_v2 A_timstof B_nplib"; do
  set -- $job; EVAL=$1; RUN=$2; shift 2
  mkdir -p "$RUN"
  echo "== $(date +%T) START $RUN"
  bash spark/jobs/b1_features_job.sh "$EVAL" "$RUN" "$@"
  echo "== $(date +%T) END $RUN"
done
echo "== $(date +%T) B1_ALL_V2_DONE"
