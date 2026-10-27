#!/bin/bash
# 071 confirmation (run ONLY after the registered development selection; usage: bash pc_conf071.sh rank_v9a|rank_v9b): opens the 053 NP_H / NP_N
# conf tables (fold 1 / fold 2, never evaluated before) once, models rank_v4b (control) + the selected ranker in one gen_eval2m pass.
set -u
SEL=$1; [ -f /c/kaggle/CASMI/experiments/b1_baseline/$SEL/lambdarank.txt ] || { echo "no model $SEL"; exit 2; }
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; FS=data/external/fold_safe_fpnet
echo "== $(date +%T) confirm $SEL sha $(sha256sum $SEL/lambdarank.txt | cut -c1-8)"
for K in 1 2; do
  $PY -X utf8 gen_eval2m.py --model rank_v4b/lambdarank.txt,$SEL/lambdarank.txt --parents 0 --run run_np053_f${K}conf --gen run_np053_f${K}conf/gen --sets NP_H NP_X NP_N \
    --eval_csv np053_f${K}conf/p2_molecules.csv --fold_safe $FS --views c1,c2 --out diag/c071_rank_v4b_np053f${K}conf,diag/c071_${SEL}_np053f${K}conf --workers 6 > diag/c071_np053f${K}conf.log 2>&1
  echo "== $(date +%T) conf f$K exit $?"
done
echo "CONF071_DONE $(date +%T)"
