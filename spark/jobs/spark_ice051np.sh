#!/bin/bash
# 051 (resumed with the NP focus): ICEBERG on the 053 NP-truth dev sets (NP_H only; NP_X/NP_N have no covered adduct), into run copies,
# then gen_eval2i (main + ice<w> outputs) views c1,c2. Waits for the GL-heavy jobs so the GPU is free.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "NP053_SETS_DONE" logs/spark_np053_sets.log 2>/dev/null && grep -q "PU054_DONE" logs/spark_pu054.log 2>/dev/null && grep -q "ENS058_DONE" logs/spark_ens058_pu.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; IPY=$HOME/CASMI2026/.venv-ice/bin/python; R=$HOME/CASMI2026
echo "== $(date +%T) gen_eval2i $(sha256sum $B/gen_eval2i.py | cut -c1-12)"
for K in 1 2; do
  RUN=run_np053_f${K}dev; RI=$B/${RUN}_ice; mkdir -p $RI/work
  $IPY spark/jobs/ice_resume.py --python $IPY data/external/iceberg/ice_runner.py data/external/iceberg $B/$RUN/b1_runner_NP_H_in.json $RI/work/ice_NP_H.json -- --device cuda --site none --budget 7200 > $RI/work/ice_NP_H_resume.log 2>&1
  echo "== $(date +%T) ice f$K $(grep -a '\[resume\] done' $RI/work/ice_NP_H_resume.log | cut -c1-100)"
  (cd $B && nice -n 5 $PY -X utf8 gen_eval2i.py --model rank_v4b/lambdarank.txt --parents 0 --run $RUN --ice_run ${RUN}_ice --ice_w 0.5 1 2 --gen $RUN/gen --sets NP_H --eval_csv np053_f${K}dev/p2_molecules.csv --fold_safe $R/data/external/fpnet_fold${K}_as_fold0 --views c1,c2 --out diag/ice051np_f$K --workers 6 > diag/ice051np_f$K.log 2>&1)
  echo "== $(date +%T) eval f$K exit $?"
done
echo "ICE051NP_DONE $(date +%T)"
