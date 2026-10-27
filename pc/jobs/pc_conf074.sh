#!/bin/bash
# 074 confirmation on the reserved 073 tables (run ONLY after the registered 074 selection AND its dev gate passed): opens
# run_np073_f3conf / run_np073_f4conf once with gen_eval2p (all fixed variants are computed; only the selected one is read).
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
for K in 3 4; do grep -q "\[resume\] done: ok\|\[resume\] done: partial" run_np073_f${K}conf/work/gl_NP_H_resume.log 2>/dev/null || { echo "073 fold $K GL not complete"; exit 2; }; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; FS=data/external/fold_safe_fpnet
for K in 3 4; do
  $PY -X utf8 gen_eval2p.py --model rank_v4b/lambdarank.txt --parents 0 --run run_np073_f${K}conf --gen run_np073_f${K}conf/gen --sets NP_H NP_X NP_N \
    --eval_csv np061_f${K}unused/p2_molecules.csv --fold_safe $FS --views c1,c2 --out diag/c074_np073f${K}conf --workers 6 > diag/c074_np073f${K}conf.log 2>&1
  echo "== $(date +%T) conf074 f$K exit $?"
done
echo "CONF074_DONE $(date +%T)"
