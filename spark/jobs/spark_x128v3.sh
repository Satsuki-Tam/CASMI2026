#!/bin/bash
# 128 v3 evaluations (128_prereg_wf.md v2 + v3 sections, Codex 129): gen_eval2fd_n128v3.py (sha checked) with rank_v8w7a and the MIST v3 scores
# (experiments/mist/scores_v3), fold 1 (default) or fold 2 (FOLD=2). CPU only. Input record at the start and re-checked at the end; the row
# manifest lists exactly the files this run wrote. The reader x128v3_summary.py runs separately. Status: diag/x128v3[f2]_status.txt
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
PY=$HOME/CASMI2026/.venv/bin/python; K=${FOLD:-1}; SUF=$([ "$K" = 1 ] && echo "" || echo f2); ST=diag/x128v3${SUF}_status.txt; rm -f $ST
fail() { echo "X128V3_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
EXPECT=${EXPECT_SHA:?set EXPECT_SHA to the reviewed gen_eval2fd_n128v3.py sha256}
[ "$(sha256sum gen_eval2fd_n128v3.py | cut -c1-64)" = "$EXPECT" ] || fail "evaluator sha"
grep -q "^MIST_SCORE_DONE" ../mist/scores_v3/status.txt || fail "MIST v3 scores not done"
$PY -X utf8 x128_inputs.py --fold $K --out diag/x128v3${SUF}_inputs.json || fail "input record"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"; FS=data/external/fold_safe_fpnet
OUTS=()
ev() { local T=$1; shift
  $PY -X utf8 gen_eval2fd_n128v3.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 "$@" --fold_safe $FS --views c1,c2 --out diag/r128v3${SUF}_$T --workers 4 --wf --wf_mist ../mist/scores_v3 --wf_mtag $T > diag/r128v3${SUF}_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) x128v3 $T rc=$rc"; OUTS+=("diag/r128v3${SUF}_$T.csv"); return $rc; }
if [ "$K" = 1 ]; then
  BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('c1bank_f1/c1dev/p2_molecules.csv').set.unique())))")
  ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv || fail "f1dev"
  ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv || fail "np053f1dev"
  ev c1bankdev --run run_c1bankdev_f1 --gen run_c1bankdev_f1/gen --sets $BSETS --eval_csv c1bank_f1/c1dev/p2_molecules.csv || fail "c1bankdev"
else
  ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv || fail "f2dev"
  ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets $S3 --eval_csv np053_f2dev/p2_molecules.csv || fail "np053f2dev"
fi
$PY -X utf8 x128_inputs.py --fold $K --out diag/x128v3${SUF}_inputs.json --check || fail "inputs changed during the run"
: > diag/x128v3${SUF}_rows_manifest.txt
for f in "${OUTS[@]}"; do [ -s "$f" ] || fail "missing output $f"; h=$(sha256sum $f | cut -c1-64); echo "$h $f" >> diag/x128v3${SUF}_rows_manifest.txt; done
h=$(sha256sum diag/x128v3${SUF}_inputs.json | cut -c1-64); echo "$h diag/x128v3${SUF}_inputs.json" >> diag/x128v3${SUF}_rows_manifest.txt
echo "X128V3_EVAL_DONE $(date '+%F %T') (reader withheld until the review)" | tee $ST
