#!/bin/bash
# 110 FOLD-2 REPLICATION (110_prereg_fpseed.md section 2: run only if fold 1 passed stage 3; Codex 116: after the current 110/111 chain).
# Public fold-safe FPNet recipe (train_fivefold.py, 82,855 updates, cosine schedule), held-out identity fold 2 + NP-example groups, seed 1
# (the public fpnet_fold2 = seed 0). Same harness_work inputs; run-own split by the public make_split.py (work/split.parquet), input gate
# fold_check.py (check_inputs.json read by the trainer), split audit split_audit.py; then the same segment loop as spark_fpnet_f1s1.sh.
# Exit statuses are captured right after each command (rc=$?). Status line: experiments/fpnet_seed/f2s1/f2s1_status.txt (F2S1_DONE / F2S1_FAIL).
# The completion check (ckpt_check.py) and every reading are done by spark_x110f2.sh, which waits for this job.
set -u
H=$HOME/CASMI2026; R=$H/experiments/fpnet_seed/f2s1; FS=$H/data/external/fold_safe_fpnet; FO=$H/data/external/identity_folds/structures.parquet
ST=$R/f2s1_status.txt; PY=$H/.venv/bin/python
[ -e $R/fpnet_f2s1_final.pt ] && { echo "final checkpoint exists (no reuse)"; exit 1; }
mkdir -p $R; cd $R || exit 1; rm -f $ST
fail() { echo "F2S1_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ -e $H/data/external/harness_work/split.parquet ] && fail "shared harness_work holds split.parquet (make_split would write through the link)"
$PY $FS/make_split.py $H/data/external/harness_work $FO $R 2 > $R/make_split.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "make_split rc=$rc"
[ -f $R/work/split.parquet ] && [ ! -L $R/work/split.parquet ] || fail "work/split.parquet is not a run-own file"
$PY -I $H/experiments/fpnet_seed/fold_check.py $R $FO 2 > $R/fold_check.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "fold_check rc=$rc"
$PY -I $H/experiments/fpnet_seed/split_audit.py $R $FO $FS 2 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "split audit rc=$rc"
for seg in 1 2 3; do
  $PY $FS/train_fivefold.py --code $H/data/external/v3_models/code --run $R --seed 1 --tag fpnet_f2s1 --max_steps 82855 --segment_minutes 720 --hours 12 --workers 12 >> train.log 2>&1; rc=$?
  echo "== $(date +%T) segment $seg rc=$rc"
  [ -e fpnet_f2s1_final.pt ] && break
done
[ -e fpnet_f2s1_final.pt ] || fail "no final checkpoint after 3 segments"
echo "F2S1_DONE $(date '+%F %T') $(sha256sum fpnet_f2s1_final.pt | cut -c1-16)" | tee $ST
