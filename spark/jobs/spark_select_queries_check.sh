#!/bin/bash
# Codex 015 (c) / 016: verify the shared query selector against the legacy implementations on the real W7 inputs, then rebuild the W7 test
# file with the refactored builder under the SAME conditions as the frozen eval_test_full3 (max_spectra read from its manifest) and compare.
# Fails loudly (non-zero exit, no DONE marker) when any step fails.
set -u -o pipefail
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; F=$B/eval_test_full3
echo "== $(date +%T) selector test (b1_common sha $(sha256sum $B/b1_common.py | cut -c1-16), make_eval_test sha $(sha256sum $B/make_eval_test.py | cut -c1-16))"
$PY -X utf8 $B/test_select_queries.py --store data/processed/spectra_store --eval_csv $B/eval_set/p1_molecules.csv --test $F/test.parquet 2>&1 | tail -12 || { echo "SELECT_CHECK FAILED: selector test"; exit 1; }
MQ=$($PY -c "import json; print(json.load(open('$F/eval_test_manifest.json'))['max_spectra'])") || { echo "SELECT_CHECK FAILED: manifest"; exit 1; }
echo "== $(date +%T) builder rebuild check (max_spectra $MQ from the frozen manifest)"
R=$B/eval_test_full3_rebuild_check; rm -rf $R
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $R --max_spectra $MQ --sets A_timstof B_nplib 2>&1 | tail -1 | cut -c1-160 || { echo "SELECT_CHECK FAILED: builder"; exit 1; }
$PY -X utf8 $B/compare_eval_test_dirs.py $F $R || { echo "SELECT_CHECK FAILED: rebuilt test file differs"; exit 1; }
rm -rf $R
echo "SELECT_CHECK_DONE $(date +%T)"
