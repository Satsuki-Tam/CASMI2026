#!/bin/bash
# 073 reserved confirmation tables (reports/agent_review/073_reserved_conf.md): features + GL for np061_f{3,4}unused on the PC. Nothing evaluated.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; IPY=/c/kaggle/CASMI/.venv-ice/Scripts/python.exe
until [ -f experiments/b1_baseline/diag/e072_top_v4b_np053f2dev.parquet ]; do sleep 30; done
for K in 3 4; do
  FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_np073_f${K}conf; mkdir -p $RUN/work
  echo "== $(date +%T) fold $K fpnet $(sha256sum $FS/fpnet_fold0.pt | cut -c1-12) (fold_safe fold$K $(sha256sum data/external/fold_safe_fpnet/fpnet_fold$K.pt | cut -c1-12))"
  $PY -X utf8 $B/b1_features.py --eval_csv $B/np061_f${K}unused/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 4 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets NP_H NP_N NP_X > $RUN/features.log 2>&1
  echo "== $(date +%T) fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
  $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_NP_H_in.json $RUN/work/gl_NP_H.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_NP_H_resume.log 2>&1
  echo "== $(date +%T) fold $K gl NP_H $(grep -a '\[resume\] done' $RUN/work/gl_NP_H_resume.log | cut -c1-90)"
done
echo "CONF073_DONE $(date +%T)"
