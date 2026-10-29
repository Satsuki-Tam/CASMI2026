#!/bin/bash
# W135 stage-2 preparation (137; INVEST at stage 1): for each design world (batch x pi3) -> (1) full-mode generation with w135_gen_v2.py if the
# world has none yet (p0 / p60 worlds: waits for the world's DONE line), (2) the product GL runner input of the B products (w135_prodgl_in.py reads
# only ids + B_detail), (3) GLACIER (released, the world runner options; gpu.lock) -> <world>/prod_gl.json, (4) a manifest line. No selector, no
# reading of reach or P ranks. Usage: bash spark/jobs/spark_w135_prodgl.sh "dF1:30 dF2:30 ..."
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; PYI=.venv-ice/bin/python; export PYTHONUTF8=1; L=experiments/w135/worlds/prodgl_status.txt
for spec in $1; do
  b=${spec%:*}; p=${spec#*:}; W=experiments/w135/worlds/${b}_p$p
  until grep -q "W135_WORLD_DONE $b p$p" experiments/w135/worlds/status.txt 2>/dev/null; do grep -q "W135_REBUILD_FAIL" logs/w135_rebuild.log && { echo "PRODGL_FAIL rebuild failed" >> $L; exit 1; }; sleep 30; done
  if [ ! -e $W/gen_full_v2.parquet ]; then
    ( cd experiments/b1_baseline && $PY -X utf8 ../w135/w135_gen_v2.py --batch ../w135/batches/$b.csv --wclass_col wclass_p$p --world ../w135/worlds/${b}_p$p --set $b \
      --fold_safe data/external/fpnet_fold1_as_fold0 --out ../w135/worlds/${b}_p$p/gen_full_v2 --workers 12 ) > $W/gen_full_v2.log 2>&1 || { echo "PRODGL_FAIL gen $b p$p $(date '+%F %T')" >> $L; continue; }
  fi
  [ -e $W/prod_gl.json ] && { echo "skip $b p$p (prod_gl exists)" >> $L; continue; }
  $PY -X utf8 experiments/w135/w135_prodgl_in.py --world $W --set $b --arm both --out $W/prod_runner_in.json > $W/prodgl_in.log 2>&1 || { echo "PRODGL_FAIL input $b p$p" >> $L; continue; }
  flock spark/gpu.lock $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $W/prod_runner_in.json $W/prod_gl.json \
    -- --device cuda --site none --budget 7200 > $W/prod_gl_resume.log 2>&1 || { echo "PRODGL_FAIL gl $b p$p" >> $L; continue; }
  echo "PRODGL_DONE $b p$p $(date '+%F %T') $(sha256sum $W/gen_full_v2.parquet | cut -c1-16) $(sha256sum $W/prod_runner_in.json | cut -c1-16) $(sha256sum $W/prod_gl.json | cut -c1-16) $(grep -a '\[resume\] done' $W/prod_gl_resume.log | cut -c1-60)" >> $L
done
echo "PRODGL_LIST_DONE $1 $(date '+%F %T')" >> $L
