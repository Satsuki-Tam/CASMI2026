#!/bin/bash
# 057b on the panel-unseen class-2 benchmark (054): blend-weight and PubChemLite-boost variants per fold (GL is MSG-contaminated on the panel).
set -u
cd ~/CASMI2026 || exit 1
until grep -q "PU054_DONE" logs/spark_pu054.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; R=$HOME/CASMI2026
V="2:2:0.5 2:1:0.5 2:0.5:0.5 2:2:1 2:1:1 3:2:0.5 2:2:0.5:1 2:2:0.5:2 2:1:1:1 2:0.5:1:2"
echo "== $(date +%T) gen_eval2vp $(sha256sum $B/gen_eval2vp.py | cut -c1-12)"
for k in 0 1 2 3 4; do
  if [ $k = 0 ]; then FS=data/external/fold_safe_fpnet; else FS=data/external/fpnet_fold${k}_as_fold0; fi
  (cd $B && nice -n 5 $PY -X utf8 gen_eval2vp.py --model rank_v4b/lambdarank.txt --parents 0 --run run_pu054/f$k --gen run_pu054/f$k/gen --sets PU --eval_csv panel_dg/pu_f$k.csv --fold_safe $R/$FS --views c1,c2 --variants $V --out diag/pu057_f$k --workers 6 > diag/pu057_f$k.log 2>&1)
  echo "== $(date +%T) fold $k exit $?"
done
echo "PU057_DONE $(date +%T)"
