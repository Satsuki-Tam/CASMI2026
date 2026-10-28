#!/bin/bash
# 109 (a): public fold-safe FPNet recipe (train_fivefold.py, 82,855 updates, cosine schedule), held-out identity fold 1 + NP-example groups,
# NEW seed 1 (the public fpnet_fold1 = seed 0). Same harness_work inputs, split by the public make_split.py, gate by fold_check.py.
# Resumes across segments until the final checkpoint exists (max 3 segments).
set -u
R=$HOME/CASMI2026/experiments/fpnet_seed/f1s1; cd $R || exit 1
for seg in 1 2 3; do
  ~/CASMI2026/.venv/bin/python ~/CASMI2026/data/external/fold_safe_fpnet/train_fivefold.py --code ~/CASMI2026/data/external/v3_models/code --run $R --seed 1 \
    --tag fpnet_f1s1 --max_steps 82855 --segment_minutes 720 --hours 12 --workers 12 >> train.log 2>&1
  echo "== $(date +%T) segment $seg exit $?"
  ls fpnet_f1s1_final.pt >/dev/null 2>&1 && break
done
echo "F1S1_DONE $(date +%T) $(sha256sum fpnet_f1s1_final.pt 2>/dev/null | cut -c1-16)"
