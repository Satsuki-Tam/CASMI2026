#!/bin/bash
# 128 fold-1 evaluation (128_prereg_wf.md): gen_eval2fd_n128.py (= PC gen_eval2fd.py with --wf / --wf_mist; sha checked) with rank_v8w7a on the fold-1
# tables and the MIST aug scores (experiments/mist/scores), CPU only, then the registered reader x128_summary.py. Status: diag/x128_status.txt
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
PY=$HOME/CASMI2026/.venv/bin/python; ST=diag/x128_status.txt; rm -f $ST
fail() { echo "X128_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
EXPECT=${EXPECT_SHA:?set EXPECT_SHA to the reviewed gen_eval2fd_n128.py sha256}
[ "$(sha256sum gen_eval2fd_n128.py | cut -c1-64)" = "$EXPECT" ] || fail "evaluator sha"
for t in f1dev np053f1dev c1bankdev; do [ -s ../mist/scores/mist_${t}_manifest.json ] || fail "MIST scores $t missing"; done
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"; FS=data/external/fold_safe_fpnet
BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('c1bank_f1/c1dev/p2_molecules.csv').set.unique())))")
ev() { local T=$1; shift
  $PY -X utf8 gen_eval2fd_n128.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 "$@" --fold_safe $FS --views c1,c2 --out diag/r128_$T --workers 4 --wf --wf_mist ../mist/scores --wf_mtag $T > diag/r128_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) x128 $T rc=$rc"; return $rc; }
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv || fail "f1dev"
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv || fail "np053f1dev"
ev c1bankdev --run run_c1bankdev_f1 --gen run_c1bankdev_f1/gen --sets $BSETS --eval_csv c1bank_f1/c1dev/p2_molecules.csv || fail "c1bankdev"
$PY -X utf8 x128_summary.py > diag/x128_summary.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "reader rc=$rc ($(tail -1 diag/x128_summary.log | cut -c1-200))"
echo "X128_DONE $(date '+%F %T')" | tee $ST
