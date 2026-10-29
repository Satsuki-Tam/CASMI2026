#!/bin/bash
# Preparation for a confirmation (no evaluation, ledgers not read): tables of the fold-1 NP C1 bank, CONFIRMATION half (c1bank_f1/c1conf, 429 groups;
# reserved by the 128 / 133 registrations as the positive-ion C1 cost check), same arguments as spark_c1bank.sh (fold-1 slot = public fpnet_fold1,
# seed 0), then GLACIER for every set serially (ice_resume, same runner arguments, under the shared GPU lock) and the GLACIER audit.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; PYI=$HOME/CASMI2026/.venv-ice/bin/python; F1=data/external/fpnet_fold1_as_fold0
CSV=$B/c1bank_f1/c1conf/p2_molecules.csv; RUN=$B/run_c1bankconf_f1; STF=$RUN/c1bankconf_status.txt
fail() { echo "C1CONF_FAIL $* $(date '+%F %T')" | tee $STF; exit 1; }
exec 9>$HOME/CASMI2026/spark/gpu.lock
flock -n 9 || { echo "refused: the GPU lock is held by another job ($(date '+%F %T'))"; exit 1; }
[ -e $RUN ] && { echo "refused: $RUN exists"; exit 1; }
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || { echo "fold-1 slot sha"; exit 1; }
[ "$(sha256sum $CSV | cut -c1-64)" = "0fcd0b991c1ff6679b56d7e0219a31944b8c9860a2a4f29c9e878026e10aa939" ] || { echo "c1conf csv sha (c1bank_freeze.json)"; exit 1; }
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$CSV').set.unique())))")
[ -n "$SETS" ] || { echo "no sets"; exit 1; }
mkdir -p $RUN/work
nice -n 10 $PY -X utf8 $B/b1_features.py --eval_csv $CSV --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1; rc=$?
echo "== $(date +%T) features rc=$rc"; [ $rc -eq 0 ] || fail "features rc=$rc"
for S in $SETS; do { [ -s $RUN/b1_molecules_$S.csv ] && [ -s $RUN/b1_features_$S.parquet ]; } || fail "missing table $S"; done
A=""
for S in $SETS; do
  nice -n 10 $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1; rc=$?
  echo "== $(date +%T) gl $S rc=$rc $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"; [ $rc -eq 0 ] || fail "gl $S rc=$rc"
  A="$A $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json"
done
$PYI -X utf8 $B/gl_audit.py $A > $RUN/gl_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "GLACIER audit"
{ for f in $CSV $B/b1_features.py $F1/fpnet_fold0.pt $RUN/b1_features_manifest.json; do echo "$(sha256sum $f | cut -c1-64) $f"; done; for S in $SETS; do for f in $RUN/b1_features_$S.parquet $RUN/b1_molecules_$S.csv $RUN/work/gl_$S.json; do echo "$(sha256sum $f | cut -c1-64) $f"; done; done; } > $RUN/c1bankconf_manifest.txt
echo "C1CONF_DONE $(date '+%F %T')" | tee $STF
