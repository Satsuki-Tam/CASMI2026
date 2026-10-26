#!/bin/bash
# 065: EXT benchmark (60 external structures absent from train, none in MassSpecGym -> unseen by FPNet, rankers, library and GLACIER):
# the frozen 0.379 pipeline (b1_ana035) with rank_v4b and with rank_v8w, evaluation mode (--solution).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_ana035; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_ext110; CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
for M in rank_v4b rank_v8w; do
  W=$E/run_$M
  nice -n 5 $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 6 --solution $E/solution.csv --rank_model $B/$M/lambdarank.txt --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap > $W.log 2>&1
  echo "== $(date +%T) $M exit $? $(grep -a 'submission written\|MRR' $W.log | tail -2 | tr '\n' ' ' | cut -c1-240)"
done
echo "EXT065_DONE $(date +%T)"
