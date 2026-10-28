#!/bin/bash
# 110 FOLD-2 REPLICATION (110_prereg_fpseed.md section 2 / 5; Codex 116 / 117): public fold-safe FPNet recipe (train_fivefold.py, 82,855 updates,
# cosine schedule), held-out identity fold 2 + NP-example groups, seed 1 (the public fpnet_fold2 = seed 0). Same harness_work inputs; run-own split by
# the public make_split.py (work/split.parquet), input gate fold_check.py (check_inputs.json read by the trainer), split audit split_audit.py.
# LAUNCH GATE (checked here, not by convention; Codex 117): the fold-1 stage-3 reading PASSED (the gate line of diag/x110_stage3.md, not merely
# X110_DONE, which a NO also produces), X110_DONE, the 111 chain reached a terminal status (diag/x111_status.txt N111_DONE / N111_FAIL) and no 111
# / evaluation process is alive; the hashes of those files go to the run manifest. A 111-only pass never starts this job.
# Fresh run only (an existing run dir is refused). Resume: `bash spark_fpnet_f2s1.sh --resume` continues ONLY a run whose recorded manifest
# (split, inputs, code, args) still matches. A segment that exits non-zero stops the job (no blind repeat); only a normal time-limited segment
# (rc 0, no final yet) is continued. Done = ckpt_check.py PASS (not the existence of the final file).
# Status line: experiments/fpnet_seed/f2s1/f2s1_status.txt (F2S1_DONE / F2S1_FAIL).
set -u
H=$HOME/CASMI2026; B=$H/experiments/b1_baseline; R=$H/experiments/fpnet_seed/f2s1; FS=$H/data/external/fold_safe_fpnet; FO=$H/data/external/identity_folds/structures.parquet
HW=$H/data/external/harness_work; PY=$H/.venv/bin/python; ST=$R/f2s1_status.txt; MAN=$R/f2s1_manifest.txt
ARGS="--code $H/data/external/v3_models/code --run $R --seed 1 --tag fpnet_f2s1 --max_steps 82855 --segment_minutes 720 --hours 12 --workers 12"
RESUME=0; [ "${1:-}" = "--resume" ] && RESUME=1
die() { echo "F2S1_FAIL $* $(date '+%F %T')"; [ -d $R ] && echo "F2S1_FAIL $* $(date '+%F %T')" > $ST; exit 1; }
# --- launch gate ---
grep -q "PASS (fold 1) -> fold 2 replication" $B/diag/x110_stage3.md 2>/dev/null || die "gate: fold-1 stage 3 did not pass (diag/x110_stage3.md)"
grep -q "^X110_DONE" $B/diag/x110_status.txt 2>/dev/null || die "gate: x110 status is not X110_DONE"
grep -q -E "^(N111_DONE|N111_FAIL)" $B/diag/x111_status.txt 2>/dev/null || die "gate: the 111 chain has no terminal status"
pgrep -f "[s]park_n111|[t]rain_n111.py|[g]en_eval2fd|[s]park_x110.sh|[s]park_c1bank" >/dev/null && die "gate: a 111 / evaluation process is still running"
inputs() { for f in $B/diag/x110_stage3.md $B/diag/x110_status.txt $B/diag/x111_status.txt $FS/make_split.py $FS/train_fivefold.py $FS/fp_bits.npy $FO \
    $H/experiments/fpnet_seed/fold_check.py $H/experiments/fpnet_seed/split_audit.py $H/experiments/fpnet_seed/ckpt_check.py $HW/pool_meta.parquet $HW/pool_fp.npy $HW/spec_meta.parquet \
    $H/spark/jobs/spark_fpnet_f2s1.sh; do echo "$(sha256sum $f | cut -c1-64) $f"; done; echo "args $ARGS"; }
if [ $RESUME -eq 0 ]; then
  [ -e $R ] && die "run dir exists (fresh run only; use --resume for a recorded run)"
  { [ -e $HW/split.parquet ] || [ -L $HW/split.parquet ]; } && die "shared harness_work holds split.parquet (make_split would write through the link)"
  mkdir -p $R; cd $R || exit 1
  $PY $FS/make_split.py $HW $FO $R 2 > $R/make_split.log 2>&1; rc=$?; [ $rc -eq 0 ] || die "make_split rc=$rc"
  { [ -f $R/work/split.parquet ] && [ ! -L $R/work/split.parquet ]; } || die "work/split.parquet is not a run-own file"
  $PY -I $H/experiments/fpnet_seed/fold_check.py $R $FO 2 > $R/fold_check.log 2>&1; rc=$?; [ $rc -eq 0 ] || die "fold_check rc=$rc"
  $PY -I $H/experiments/fpnet_seed/split_audit.py $R $FO $FS 2 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || die "split audit rc=$rc"
  { echo "f2s1 launch $(date '+%F %T')"; inputs; echo "$(sha256sum $R/work/split.parquet | cut -c1-64) $R/work/split.parquet"; } > $MAN
else
  [ -s $MAN ] || die "resume without a recorded manifest"
  cd $R || exit 1
  KEEP='^([0-9a-f]{64} |args )'
  diff <({ inputs; echo "$(sha256sum $R/work/split.parquet | cut -c1-64) $R/work/split.parquet"; } | grep -E "$KEEP" | grep -v "spark_fpnet_f2s1.sh") <(grep -E "$KEEP" $MAN | grep -v "spark_fpnet_f2s1.sh") > $R/resume_diff.txt || die "resume: recorded inputs / split / args differ (resume_diff.txt)"
  echo "resume $(date '+%F %T')" >> $MAN
fi
rm -f $ST
for seg in 1 2 3; do
  [ -e fpnet_f2s1_final.pt ] && break
  $PY $FS/train_fivefold.py $ARGS >> train.log 2>&1; rc=$?
  echo "== $(date +%T) segment $seg rc=$rc" | tee -a $MAN
  [ $rc -eq 0 ] || die "segment $seg exited rc=$rc (not repeated)"
done
[ -e fpnet_f2s1_final.pt ] || die "no final checkpoint after 3 segments"
$PY -I $H/experiments/fpnet_seed/ckpt_check.py $R fpnet_f2s1 82855 1 > $R/ckpt_check.log 2>&1; rc=$?; [ $rc -eq 0 ] || die "completion check rc=$rc"
echo "F2S1_DONE $(date '+%F %T') $(sha256sum fpnet_f2s1_final.pt | cut -c1-16)" | tee $ST
