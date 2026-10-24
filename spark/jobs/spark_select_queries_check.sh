#!/bin/bash
# Codex 015 (c): verify the shared query selector against the legacy implementations on the real W7 inputs, then rebuild the W7 test file
# with the refactored builder into a scratch dir and compare it with the frozen eval_test_full3/test.parquet (must be identical).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
echo "== $(date +%T) selector test"
$PY -X utf8 $B/test_select_queries.py --store data/processed/spectra_store --eval_csv $B/eval_set/p1_molecules.csv --test $B/eval_test_full3/test.parquet 2>&1 | tail -12
echo "== $(date +%T) builder rebuild check"
R=$B/eval_test_full3_rebuild_check; rm -rf $R
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $R --max_spectra 16 --sets A_timstof B_nplib 2>&1 | tail -2
$PY -X utf8 $B/compare_eval_test_dirs.py $B/eval_test_full3 $R
echo "SELECT_CHECK_DONE $(date +%T)"
