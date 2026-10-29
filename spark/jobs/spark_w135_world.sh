#!/bin/bash
# W135 (135_decision.md / 136): build ONE world = batch x pi3 -> (1) b1_world.py (the batch's common masks; fold-safe FPNet of the batch's
# fold) -> (2) GLACIER GL of the world shortlist (released weights; the development runs' runner options; gpu.lock) -> (3) w135_p.py (world
# P = rank_v8w7a main path, analogs under the world mask = the frozen parent bank). SPEED=1 adds w135_gen.py --speed_only (product counts and
# timing only; no truth, class or P rank is read). No reach / oracle number is computed here.
# Usage: bash spark/jobs/spark_w135_world.sh BATCH PI   (BATCH = dF1 .. dR3 / cF1 cR1 cU1, PI = 0 / 30 / 60)
set -u
cd ~/CASMI2026 || exit 1
BATCH=$1; PI=$2; W=experiments/w135/worlds/${BATCH}_p${PI}; PY=$HOME/CASMI2026/.venv/bin/python; PYI=.venv-ice/bin/python
case $BATCH in d*) FS=data/external/fpnet_fold1_as_fold0;; c*) FS=data/external/fpnet_fold2_as_fold0;; *) echo "unknown batch $BATCH"; exit 1;; esac
export PYTHONUTF8=1
fail() { echo "W135_WORLD_FAIL $BATCH p$PI $* $(date '+%F %T')" | tee -a experiments/w135/worlds/status.txt; exit 1; }
mkdir -p experiments/w135/worlds
[ -e $W/b1_features_$BATCH.parquet ] && fail "world exists"
mkdir -p $W/work
echo "== $(date '+%F %T') world $BATCH p$PI start (FPNet $FS)"
OMP_NUM_THREADS=1 nice -n 5 $PY -X utf8 experiments/w135/b1_world.py --eval_csv experiments/w135/batches/$BATCH.csv --wclass_col wclass_p$PI --store data/processed/spectra_store \
  --tier data/external/pubchem_tier --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS \
  --v3 data/external/v3_models/code --folds data/external/identity_folds/structures.parquet --out $W --k 100 --workers 8 --k_fpp 200 --k_pop 50 --sets $BATCH \
  --dump_gen $W/gen > $W/world.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "b1_world rc=$rc"
echo "== $(date '+%F %T') tables: $(grep -a '^saved' $W/world.log | cut -c1-120)"
flock spark/gpu.lock $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $W/b1_runner_${BATCH}_in.json $W/work/gl_${BATCH}.json \
  -- --device cuda --site none --budget 7200 > $W/work/gl_resume.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "gl rc=$rc"
echo "== $(date '+%F %T') gl: $(grep -a '\[resume\] done' $W/work/gl_resume.log | cut -c1-100)"
( cd experiments/b1_baseline && OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=8 $PY -X utf8 ../w135/w135_p.py --run ../w135/worlds/${BATCH}_p${PI} --gl ../w135/worlds/${BATCH}_p${PI}/work/gl_${BATCH}.json \
  --sets $BATCH --eval_csv ../w135/batches/$BATCH.csv --model rank_v8w7a/lambdarank.txt --masks ../w135/worlds/${BATCH}_p${PI}/world_masks.json --out ../w135/worlds/${BATCH}_p${PI}/P ) > $W/p.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "w135_p rc=$rc"
echo "== $(date '+%F %T') P: $(tail -1 $W/p.log | cut -c1-120)"
if [ "${SPEED:-0}" = 1 ]; then
  ( cd experiments/b1_baseline && $PY -X utf8 ../w135/w135_gen.py --batch ../w135/batches/$BATCH.csv --wclass_col wclass_p$PI --world ../w135/worlds/${BATCH}_p${PI} \
    --p ../w135/worlds/${BATCH}_p${PI}/P.parquet --set $BATCH --out ../w135/worlds/${BATCH}_p${PI}/speed --speed_only --workers 16 ) > $W/speed.log 2>&1; rc=$?
  [ $rc -eq 0 ] || fail "speed rc=$rc"
  echo "== $(date '+%F %T') speed: $(tail -1 $W/speed.log | cut -c1-200)"
fi
{ for f in experiments/w135/batches/$BATCH.csv experiments/w135/b1_world.py experiments/w135/w135_p.py experiments/w135/w135_gen.py $W/b1_features_$BATCH.parquet $W/b1_molecules_$BATCH.csv \
    $W/world_masks.json $W/work/gl_$BATCH.json $W/P.parquet $W/gen/gen_$BATCH.npz $W/gen/gen_${BATCH}_window.parquet; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $W/manifest.txt
echo "W135_WORLD_DONE $BATCH p$PI $(date '+%F %T')" | tee -a experiments/w135/worlds/status.txt
