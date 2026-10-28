#!/bin/bash
# 110 stage 3 resume after a reproduction stop (X110_FAIL_REPRO, Codex 114): reruns ONLY the stage-3 reader on the SAME artefacts with
# --allow_repro <audit.md> (an existing, non-trivial file recording the cause, the affected rows, the hashes of inputs / control / old baseline /
# code, what was changed and why continuing is justified). GLACIER / meta / query / mask / candidate mix-ups are NOT exempted: fix the
# implementation instead. On success the status becomes X110_DONE (resumed, audit sha recorded); the audit path and sha go to the manifest.
# Usage: bash spark/jobs/x110_stage3_resume.sh experiments/b1_baseline/diag/x110_repro_audit.md
set -u
[ -n "${1:-}" ] && [ -s "$1" ] || { echo "missing audit file argument"; exit 1; }
AUD=$(realpath "$1"); PY=$HOME/CASMI2026/.venv/bin/python   # absolute BEFORE cd (Codex 117: a repo-relative argument was resolved after cd)
cd ~/CASMI2026/experiments/b1_baseline || exit 1
grep -q "^X110_FAIL_REPRO" diag/x110_status.txt || { echo "status is not X110_FAIL_REPRO: $(cat diag/x110_status.txt)"; exit 1; }
[ -s "$AUD" ] || { echo "missing audit file"; exit 1; }
h=$(sha256sum "$AUD" | cut -c1-64); echo "$h $AUD (allow_repro audit)" >> diag/x110_manifest.txt
$PY -X utf8 x110_stage3.py --allow_repro "$AUD" > diag/x110_stage3.log 2>&1; rc=$?
if [ $rc -eq 0 ]; then echo "X110_DONE resumed with allow_repro audit $h $(date '+%F %T')" | tee diag/x110_status.txt; else echo "resume failed rc=$rc (status unchanged)"; exit 1; fi
