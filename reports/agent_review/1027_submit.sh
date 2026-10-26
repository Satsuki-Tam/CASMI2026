#!/bin/bash
# 10/27 submissions (run after 09:00 JST; plan fixed in 1027_submission_plan.md). One at a time; stop on the first failure.
set -u
K=/c/kaggle/CASMI/.venv/Scripts/kaggle.exe; C=enveda-CASMI26-molecule-id-mass-spectra
sub() { echo "== $(date +%H:%M:%S) $1"; $K competitions submit $C -k "$1" -v "$2" -f submission.csv -m "$3" || { echo "SUBMIT FAILED: $1"; exit 1; }; sleep 20; }
sub hayatetaf/casmi26-b1-fpnet-v7f 1 "Codex 038/039 one-change comparison vs 0.379 (FE + anaw0.5): v7f = analog-feature ranker rank_v7a (600 trees) on GL-covered molecules, insurance + 1 z(ap) + 1 z(MetFrag-lite) on GL-fallback; pipeline 6e3b4d04; branch-B reading fixed in 038_decision"
sub hayatetaf/casmi26-b1-probe-prior 1 "DIAGNOSTIC (Codex 039): working-baseline shortlist (full_eval, k_fpp 200, k_pop 50) ordered by the prior alone (FP tie-break), no forward models; measures this fixed policy only"
sub hayatetaf/casmi26-b1-fpnet-gt3 1 "Codex 043 one-change comparison vs 0.379 (FE + anaw0.5): + one generated analog derivative (own b1_gen v2 ef8c856a; top-10 analog parents, 1-2 biosynthetic edits, query-derived mass, raw-window absence) at rank 3 if its FPNet f.z >= the main rank-3 f.z; pipeline 8d0c415e"
sub hayatetaf/casmi26-e0-probe-b 1 "DIAGNOSTIC pair (Codex 049, 055): E0 (0.464 reproduction) final list restricted to group B = COCONUT and not training (official key; T-priority exclusive), order kept, no refill, empty -> CCO; not a method candidate"
sub hayatetaf/casmi26-b1-probe-b379 1 "DIAGNOSTIC pair (Codex 049, 055): current B1 0.379 (57650023 kernel) final list restricted to group B with the identical appended cell; not a method candidate"
echo "== $(date +%H:%M:%S) all five submitted"
$K competitions submissions $C 2>&1 | head -8
