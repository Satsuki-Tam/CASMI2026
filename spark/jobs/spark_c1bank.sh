#!/bin/bash
# 112: tables of the fold-1 NP C1 bank, DEVELOPMENT half only (c1bank_f1/c1dev, 432 groups; the c1conf half stays unbuilt until a confirmation).
# Same arguments as spark_fold1_sets.sh / spark_np053_sets.sh (fold-1 slot = public fpnet_fold1, seed 0), then GLACIER for every set.
# Nothing is evaluated here; the ledgers (which contain truth ranks) are not read until a registered reader runs.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0
fail() { echo "C1BANK_FAIL $* $(date +%T)"; exit 1; }
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
CSV=$B/c1bank_f1/c1dev/p2_molecules.csv; RUN=$B/run_c1bankdev_f1
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$CSV').set.unique())))")
[ -n "$SETS" ] || fail "no sets"
rm -rf $RUN; mkdir -p $RUN/work
nice -n 10 $PY -X utf8 $B/b1_features.py --eval_csv $CSV --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1; rc=$?
echo "== $(date +%T) features rc=$rc"; [ $rc -eq 0 ] || fail "features rc=$rc"
for S in $SETS; do { [ -s $RUN/b1_molecules_$S.csv ] && [ -s $RUN/b1_features_$S.parquet ]; } || fail "missing table $S"; done
for S in $SETS; do
  nice -n 10 .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1; rc=$?
  echo "== $(date +%T) gl $S rc=$rc $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
done
{ for f in $CSV $B/b1_features.py $F1/fpnet_fold0.pt $RUN/b1_features_manifest.json; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $RUN/c1bank_manifest.txt
echo "C1BANK_DONE $(date +%T)"
