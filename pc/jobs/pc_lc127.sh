#!/bin/bash
# 127 learning curve (127_prereg_lc.md): the pc_rank087.sh recipe (rank_v8w7a) with --fit_frac / --fit_seed. CPU only (no GPU: CUDA hidden, LightGBM CPU).
# Step 0: frac 1.0 must reproduce rank_v8w7a/lambdarank.txt (fe61dc42) byte for byte, else stop. Then frac 0.5 / 0.25 x seed 1 / 2.
set -u
cd /c/kaggle/CASMI || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P7=$B/rank_params_v7a/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
echo "== $(date +%T) trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12)"
trn() { local OUT=$1; shift
  $PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS --out $OUT --feats v2_noice_ana --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 \
    --params_from $P7 --analog_parquet $B/diag/analog_tr_v8w.parquet "$@" > $OUT.log 2>&1; local rc=$?
  echo "== $(date +%T) $OUT rc=$rc $(grep -a -E '127 learning curve|fit groups after' $OUT.log | tr '\n' ' ' | cut -c1-200) sha $(sha256sum $OUT/lambdarank.txt 2>/dev/null | cut -c1-8)"; return $rc; }
trn $B/rank_lc127_full || { echo "LC127_FAIL full rc"; exit 1; }
[ "$(sha256sum $B/rank_lc127_full/lambdarank.txt | cut -c1-64)" = "$(sha256sum $B/rank_v8w7a/lambdarank.txt | cut -c1-64)" ] || { echo "LC127_FAIL frac 1.0 does not reproduce rank_v8w7a"; exit 1; }
echo "== frac 1.0 reproduces rank_v8w7a byte for byte"
for F in 0.5 0.25; do for S in 1 2; do trn $B/rank_lc127_f${F/./}s$S --fit_frac $F --fit_seed $S || { echo "LC127_FAIL f$F s$S"; exit 1; }; done; done
echo "LC127_TRAIN_DONE $(date +%T)"
