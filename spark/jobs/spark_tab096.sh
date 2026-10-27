#!/bin/bash
# 096 reserved confirmation tables (096_reserved_conf.md): b1_features (fold-safe fpnet_fold0) + GLACIER for NP_H / NP_N. Nothing evaluated.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; RUN=$B/run_np096_f0conf; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/np096_f0conf/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 \
  --k_fpp 200 --k_pop 50 --dump_gen $RUN/gen --sets NP_H NP_N > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
for S in NP_H NP_N; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
done
echo "TAB096_DONE $(date +%T)"
