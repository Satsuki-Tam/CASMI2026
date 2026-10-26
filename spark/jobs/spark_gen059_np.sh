#!/bin/bash
# 059 development (diagnostic of the class-3 route on NP chemistry): gen_eval3 on the 053 NP-truth dev sets (fold-1/2), views c1,c2,c3, with the
# generated-structure GLACIER pass (emit -> GL -> evaluate), exactly like 048; rules main / gt3 / ggt3 / gt3t / ggt3t.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "NP053_SETS_DONE" logs/spark_np053_sets.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
echo "== $(date +%T) gen_eval3 $(sha256sum $B/gen_eval3.py | cut -c1-12) b1_gen $(sha256sum $B/b1_gen.py | cut -c1-12)"
for K in 1 2; do
  FS=data/external/fpnet_fold${K}_as_fold0
  (cd $B && nice -n 5 $PY -X utf8 gen_eval3.py --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $FS --views c1,c2,c3 --emit_gl glgen_np053f$K --workers 8 > diag/g059_emit_np053f$K.log 2>&1)
  echo "== $(date +%T) emit f$K exit $?"
  for IN in $B/glgen_np053f$K/gl_gen_*_in.json; do
    S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=$B/glgen_np053f$K/gl_gen_${S}.json
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > $B/glgen_np053f$K/gl_gen_${S}_resume.log 2>&1
    echo "== $(date +%T) GL gen f$K $S $(grep -a '\[resume\] done' $B/glgen_np053f$K/gl_gen_${S}_resume.log | cut -c1-90)"
  done
  (cd $B && nice -n 5 $PY -X utf8 gen_eval3.py --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $FS --views c1,c2,c3 --gl_gen glgen_np053f$K/gl_gen --out diag/g059_np053f$K --workers 8 > diag/g059_np053f$K.log 2>&1)
  echo "== $(date +%T) eval f$K exit $?"
done
echo "GEN059_DONE $(date +%T)"
