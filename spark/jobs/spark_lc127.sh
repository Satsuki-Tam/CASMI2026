#!/bin/bash
# 127 learning-curve evaluation (127_prereg_lc.md): one pass of the reviewed evaluator (gen_eval2fd_n111.py, sha 1ccf5e35) per tag with v8w7a and the four
# subsampled rankers (copied from the PC into rank_lc127_*/; their sha256 are checked against lc127_models.sha256), CPU only, then x_lc127.py.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
PY=$HOME/CASMI2026/.venv/bin/python; ST=diag/xlc127_status.txt; rm -f $ST
fail() { echo "LC127_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ "$(sha256sum gen_eval2fd_n111.py | cut -c1-64)" = "1ccf5e356129d4653e1dfd9e1f988e010bdca8ccb1b45e83bd37a9e70299febd" ] || fail "evaluator sha"
sha256sum -c lc127_models.sha256 > /dev/null 2>&1 || fail "model hashes"
MS="rank_v8w7a rank_lc127_f05s1 rank_lc127_f05s2 rank_lc127_f025s1 rank_lc127_f025s2"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"; FS=data/external/fold_safe_fpnet
ev() { local T=$1; shift
  MOD=$(for M in $MS; do echo -n "$M/lambdarank.txt,"; done | sed 's/,$//'); OUT=$(for M in $MS; do N=${M/rank_v8w7a/v8w7a}; echo -n "diag/rlc127_${N}_$T,"; done | sed 's/,$//')
  $PY -X utf8 gen_eval2fd_n111.py --model $MOD --v7f --parents 0 "$@" --views c1,c2 --out $OUT --workers 4 > diag/rlc127_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) lc127 $T rc=$rc"; return $rc; }
echo "== $(date +%T) start"
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS || fail "f1dev"
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS || fail "np053f1dev"
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS || fail "f2dev"
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets $S3 --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS || fail "np053f2dev"
$PY -X utf8 x_lc127.py > diag/x_lc127.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "reader rc=$rc ($(tail -1 diag/x_lc127.log | cut -c1-200))"
echo "LC127_DONE $(date '+%F %T')" | tee $ST
