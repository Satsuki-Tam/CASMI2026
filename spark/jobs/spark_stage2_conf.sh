#!/bin/bash
# 044 confirmation (pre-registered; selection = ggt3 in 044_dev_selection.md): fold-1 LOCKED 500 tables (fpnet_fold1, --dump_gen) + GLACIER,
# generated-structure GLACIER, then gen_eval3 reporting ONLY gt3 and ggt3 (read once).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/locked_eval_f1/p2_molecules.csv').set.unique())))")
RUN=$B/run_f1lock; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/locked_eval_f1/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
for S in $SETS; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-110)"
done
export NUMBA_NUM_THREADS=8
cd $B
$PY -X utf8 gen_eval3.py --run run_f1lock --gen run_f1lock/gen --sets $SETS --eval_csv locked_eval_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --emit_gl glgen_f1lock --workers 16 > diag/stage2_emit_f1lock.log 2>&1
echo "== $(date +%T) emit exit $?"
cd ~/CASMI2026
for IN in $B/glgen_f1lock/gl_gen_*_in.json; do
  S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=$B/glgen_f1lock/gl_gen_${S}.json
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > $B/glgen_f1lock/gl_gen_${S}_resume.log 2>&1
  echo "== GL gen $S $(grep -a '\[resume\] done' $B/glgen_f1lock/gl_gen_${S}_resume.log | cut -c1-100)"
done
cd $B
$PY -X utf8 gen_eval3.py --run run_f1lock --gen run_f1lock/gen --sets $SETS --eval_csv locked_eval_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen_f1lock/gl_gen --rules gt3,ggt3 --out diag/stage2_f1lock --workers 16 > diag/stage2_f1lock.log 2>&1
echo "== $(date +%T) confirmation exit $?"
echo "STAGE2_CONF_DONE $(date +%T)"
