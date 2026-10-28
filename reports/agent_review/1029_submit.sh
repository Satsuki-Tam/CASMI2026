#!/bin/bash
# 10/29 submissions (run after 09:00 JST = the UTC-day reset, ONLY with the user's permission; plan and readings fixed in 1029_submission_plan.md and
# 101_decision.md before any of these scores). Both are diagnostics (Codex 101/103), not method candidates; their commit runs are COMPLETE.
set -u
K=/c/kaggle/CASMI/.venv/Scripts/kaggle.exe; C=enveda-CASMI26-molecule-id-mass-spectra
sub() { echo "== $(date +%H:%M:%S) $1"; $K competitions submit $C -k "$1" -v "$2" -f submission.csv -m "$3" || { echo "SUBMIT FAILED: $1"; exit 1; }; sleep 20; }
sub hayatetaf/casmi26-e0-probe-engb 1 "DIAGNOSTIC (Codex 101): E0 engine-2 ENG list top 25 restricted to group B (COCONUT and not training, official key, T-priority exclusive), order kept, no refill, empty -> CCO; read vs BASE_B 0.213 and final E0_B 0.259 (eta 0.015); not a method candidate"
sub hayatetaf/casmi26-e0-probe-prer2b 1 "DIAGNOSTIC (Codex 101): E0 output just before the final rank-2 insertion (E006 control) top 25 restricted to group B, same extraction; D = 0.259 - pre-rank2_B read with eta 0.015; not a method candidate"
echo "== $(date +%H:%M:%S) submitted"
$K competitions submissions $C 2>&1 | head -6
