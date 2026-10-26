#!/bin/bash
# 2026-10-27: tables (fpnet_fold1, --dump_gen) + GLACIER for the fresh confirmation set conf_g_f1a (fold-1 identities unused by every earlier set;
# reserved for the GL-less gate hypothesis; rule-independent, nothing is evaluated here). conf_g_f1b = reserve.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0; RUN=$B/run_confg_f1a
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/conf_g_f1a/p2_molecules.csv').set.unique())))")
mkdir -p $RUN/work
nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/conf_g_f1a/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $?"
for S in $SETS; do
  nice -n 5 .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-100)"
done
echo "CONFG_TABLES_DONE $(date +%T)"
