#!/bin/bash
# W135 stage 1 (136_prereg_w135_stage1.md; run only after the Codex 136 check): full-mode generation of the six design worlds at pi3 = 0.3
# (truth located among the products, reach at B = 50, train vs train+peer parents), then the registered reader with the decision.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1
fail() { echo "W135_STAGE1_FAIL $* $(date '+%F %T')"; exit 1; }
for b in dF1 dF2 dF3 dR1 dR2 dR3; do grep -q "W135_WORLD_DONE $b p30" experiments/w135/worlds/status.txt || fail "world $b p30 not built"; [ -e experiments/w135/worlds/${b}_p30/gen_full.parquet ] && fail "$b full table exists"; done
for b in dF1 dF2 dF3 dR1 dR2 dR3; do
  ( cd experiments/b1_baseline && $PY -X utf8 ../w135/w135_gen.py --batch ../w135/batches/$b.csv --wclass_col wclass_p30 --world ../w135/worlds/${b}_p30 --p ../w135/worlds/${b}_p30/P.parquet \
    --set $b --out ../w135/worlds/${b}_p30/gen_full --workers 16 ) > experiments/w135/worlds/${b}_p30/gen_full.log 2>&1 || fail "gen $b"
  echo "== $(date +%T) $b full generation done"
done
$PY -X utf8 experiments/w135/w135_read.py --pi 30 --decide > experiments/w135/stage1_p30.log 2>&1 || fail "reader"
echo "W135_STAGE1_DONE $(date '+%F %T')"
