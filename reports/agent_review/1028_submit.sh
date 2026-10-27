#!/bin/bash
# 10/28 submissions (run after 09:00 JST = the UTC-day reset; plan and readings fixed in 1028_submission_plan.md BEFORE any of these scores).
# One at a time; stop on the first failure. Slot 1 = v8w7a only if its parity (both views, incl. the stripped model) PASSed and its smoke is COMPLETE. Slot 5 is held. Every candidate is a frozen one-change kernel whose smoke run completed.
set -u
K=/c/kaggle/CASMI/.venv/Scripts/kaggle.exe; C=enveda-CASMI26-molecule-id-mass-spectra
sub() { echo "== $(date +%H:%M:%S) $1"; $K competitions submit $C -k "$1" -v "$2" -f submission.csv -m "$3" || { echo "SUBMIT FAILED: $1"; exit 1; }; sleep 20; }
sub hayatetaf/casmi26-b1-fpnet-v8w7a 1 "Codex 087/092 one-change vs v7f (0.390): ranker rank_v8w7a (v7f analog-feature recipe + fold-3a/4a pools, pool C1 x1; dev 053 NP_H C2 +0.0327 vs v7a_pc, G C1 +0.18; reserved-083 confirmation NP_H C2 +0.0245 [+0.0098, +0.0388]); frozen v7f pipeline 6e3b4d04; reading fixed in 1028_submission_plan"
# fallback if the v8w7a parity / smoke conditions are not met by 09:00 (Codex 092):
# sub hayatetaf/casmi26-b1-fpnet-v8w 1 "Codex 056/062 one-change vs 0.379 (FE + anaw0.5): ranker rank_v8w (v4b recipe + fold-3a/4a pools, pool C1 x1; 3b/4b confirmation +0.0067 [+0.0023, +0.0112], parity PASS); reading fixed in 1028_submission_plan"
sub hayatetaf/casmi26-b1-fpnet-ggt3t 1 "Codex 045/046 one-change vs 0.379: one generated analog derivative at rank 3 (b1_gen v2), GL gate on the GL path, fallback f.z gate vs main ranks 2-3 (ggt3t); gt3 Public 0.377 = undetermined -> precondition met"
sub hayatetaf/casmi26-b1-fpnet-ea05w1 1 "Codex 076/082b one-change vs 0.379: explained-away demotion EA (score - 1 x [library references present and lib_sim < 0.5]); 073 confirmation NP C2 +0.0246 [+0.017, +0.033]; parity C2 PASS, C1 outputs identical (1 known flag exception)"
sub hayatetaf/casmi26-b1-fpnet-v7fea 1 "Codex 080/081 one-change vs v7f (0.390): v7f + EA (theta 0.5, w 1); 053 conf NP C2 +0.0163 [+0.0086, +0.0252]; parity v7f-alone PASS both views, v7f+EA C2 PASS, C1 outputs identical (1 known flag exception)"
echo "== $(date +%H:%M:%S) four submitted (slot 5 held)"
$K competitions submissions $C 2>&1 | head -8
# slot 5 (only if the user allows it and the commit run of casmi26-e0-probe-baseb is COMPLETE):
# sub hayatetaf/casmi26-e0-probe-baseb 1 "DIAGNOSTIC (Codex 088): E0 engine-1 BASE list top 25 restricted to group B (COCONUT and not training, official key, T-priority exclusive), order kept, no refill, empty -> CCO; compare with E0_B 0.259; not a method candidate"
