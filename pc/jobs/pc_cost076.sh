#!/bin/bash
# 076 cost-side tables (EA family, all fixed variants computed by gen_eval2p; NOT read until 076 is registered): timsTOF C1 = the G layer of
# the 3b/4b training pools (fold 3/4; used to train rankers, independent of the EA rule's theta / w which were chosen on f1/f2).
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "P2P5EA074_DONE" logs/pc_p2p5ea074.log 2>/dev/null; do sleep 60; done
cd experiments/b1_baseline
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; FS=data/external/fold_safe_fpnet
for K in 3 4; do
  $PY -X utf8 gen_eval2p.py --model rank_v4b/lambdarank.txt --parents 0 --run run_tp_f${K}b --gen run_tp_f${K}b_g/gen --sets G_tims_crosslib --eval_csv train_pool_f${K}b/p2_molecules.csv \
    --fold_safe $FS --views c1,c2 --out diag/k076_tpf${K}b_G --workers 6 > diag/k076_tpf${K}b_G.log 2>&1
  echo "== $(date +%T) cost076 f${K}b G exit $?"
done
echo "COST076_DONE $(date +%T)"
