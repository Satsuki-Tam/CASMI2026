#!/bin/bash
# W135 stage 2 (139_decision.md): one chained run -- (1) wait until the 18 design worlds have their full-mode generation + product GL (status
# lines) -> (2) cv (leave-one-pair-out, descriptive) -> (3) fit on the 18 design worlds -> frozen model + freeze manifest -> (4) wait until the
# 13 confirmation worlds are complete -> (5) apply the frozen model once -> (6) the registered reader. Every step's exit value is checked; nothing
# is re-run or tuned in between. Outputs: experiments/w135/s2/{cv,fit,confirm}_* and logs/w135_s2.log.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=4; S=experiments/w135/s2
fail() { echo "W135_S2_FAIL $* $(date '+%F %T')"; exit 1; }
DES="dF1 dF2 dF3 dR1 dR2 dR3"
need_design() { for b in $DES; do for p in 0 30 60; do grep -q "PRODGL_DONE $b p$p " experiments/w135/worlds/prodgl_status.txt 2>/dev/null || return 1; done; done; return 0; }
until need_design; do sleep 60; done
echo "== $(date '+%F %T') design data complete"
$PY -X utf8 experiments/w135/w135_selector.py --mode cv --out $S/cv > $S/cv.log 2>&1 || fail "cv (see $S/cv.log)"
echo "== $(date '+%F %T') cv done"
$PY -X utf8 experiments/w135/w135_selector.py --mode fit --out $S/fit > $S/fit.log 2>&1 || fail "fit (see $S/fit.log)"
echo "== $(date '+%F %T') fit done (model $(sha256sum $S/fit_model.json | cut -c1-16))"
until grep -q "CONFIRM_ALL_DONE\|CONFIRM_FAIL" experiments/w135/worlds/confirm_status.txt 2>/dev/null; do sleep 60; done
grep -q "CONFIRM_FAIL" experiments/w135/worlds/confirm_status.txt && fail "confirmation worlds (see confirm_status.txt)"
$PY -X utf8 experiments/w135/w135_selector.py --mode apply --model $S/fit_model.json --out $S/confirm > $S/confirm.log 2>&1 || fail "apply (see $S/confirm.log)"
echo "== $(date '+%F %T') apply done"
$PY -X utf8 experiments/w135/w135_read_s2.py --queries $S/confirm_queries.parquet > $S/confirm_reading.log 2>&1 || fail "reader (see $S/confirm_reading.log)"
echo "W135_S2_DONE $(date '+%F %T')"
