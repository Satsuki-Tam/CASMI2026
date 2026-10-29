#!/bin/bash
# W135 stage-2 confirmation worlds (139 draft; data only, no selector is applied here): after the design rebuild, build the fold-2 confirmation
# worlds (cF1 / cR1 / cF2 / cR2 / cF3 / cR3 at pi3 = 0.3 and 0, cU1 at 0.3) from the C1-audited CSVs, run the world check on each, then the
# full-mode generation (fold-2 FPNet directory for the bit order) and the product GL of the B lists. Status lines in worlds/confirm_status.txt.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; PYI=.venv-ice/bin/python; export PYTHONUTF8=1; L=experiments/w135/worlds/confirm_status.txt; FS=data/external/fpnet_fold2_as_fold0
until grep -q "W135_REBUILD_DONE\|W135_REBUILD_FAIL" logs/w135_rebuild.log 2>/dev/null; do sleep 60; done
grep -q "W135_REBUILD_FAIL" logs/w135_rebuild.log && { echo "CONFIRM_FAIL design rebuild failed" >> $L; exit 1; }
one() { b=$1; p=$2; W=experiments/w135/worlds/${b}_p$p
  bash spark/jobs/spark_w135_world.sh $b $p > logs/w135c_${b}_p$p.log 2>&1 || { echo "CONFIRM_FAIL world $b p$p" >> $L; return 1; }
  $PY -X utf8 experiments/w135/w135_world_check.py --world $W --set $b > $W/world_check.log 2>&1 || { echo "CONFIRM_FAIL check $b p$p" >> $L; return 1; }
  ( cd experiments/b1_baseline && $PY -X utf8 ../w135/w135_gen_v2.py --batch ../w135/batches/$b.csv --wclass_col wclass_p$p --world ../w135/worlds/${b}_p$p --set $b \
    --fold_safe $FS --out ../w135/worlds/${b}_p$p/gen_full_v2 --workers 8 ) > $W/gen_full_v2.log 2>&1 || { echo "CONFIRM_FAIL gen $b p$p" >> $L; return 1; }
  $PY -X utf8 experiments/w135/w135_prodgl_in.py --world $W --set $b --arm both --out $W/prod_runner_in.json > $W/prodgl_in.log 2>&1 || { echo "CONFIRM_FAIL prodgl input $b p$p" >> $L; return 1; }
  flock spark/gpu.lock $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $W/prod_runner_in.json $W/prod_gl.json \
    -- --device cuda --site none --budget 7200 > $W/prod_gl_resume.log 2>&1 || { echo "CONFIRM_FAIL prodgl $b p$p" >> $L; return 1; }
  echo "CONFIRM_WORLD_DONE $b p$p $(date '+%F %T') $(grep -h WORLD_CHECK $W/world_check.log) $(sha256sum $W/gen_full_v2.parquet | cut -c1-16) $(sha256sum $W/prod_gl.json | cut -c1-16)" >> $L; }
stream() { for spec in "$@"; do one ${spec%:*} ${spec#*:} || return 1; done; }
stream cF1:30 cF2:30 cF3:30 cF1:0 cF2:0 cF3:0 cU1:30 & S1=$!; stream cR1:30 cR2:30 cR3:30 cR1:0 cR2:0 cR3:0 & S2=$!
FAIL=0; wait $S1 || FAIL=1; wait $S2 || FAIL=1
[ $FAIL = 0 ] && { echo "CONFIRM_ALL_DONE $(date '+%F %T')" >> $L; exit 0; }
echo "CONFIRM_FAIL (see above) $(date '+%F %T')" >> $L; exit 1   # v2 (Codex 139): a failure is a non-zero exit
