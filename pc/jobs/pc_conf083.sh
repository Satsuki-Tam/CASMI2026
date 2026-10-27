#!/bin/bash
# 083 reserved confirmation tables (083_reserved_conf.md): np061_f4pool built on the PC as a CONFIRMATION set (not training). Starts after the 080 parity (GPU).
# the Spark with seed 64, p2_molecules.csv copied). Same arguments as spark_np061_pools.sh. CUDA: run only when no other CUDA job is active.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "PARITY080_DONE" logs/pc_parity080.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; IPY=/c/kaggle/CASMI/.venv-ice/Scripts/python.exe
# Codex 082: verify --alias_perview on the known panel case first (SQFSKOYWJBQGKQ / BEBLLQPTMVOKAX: pipeline C1 = not train, 0 refs, lib 0)
T1=$B/run_aliastest; mkdir -p $T1
$PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/one_SQFSKOYWJBQGKQ.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity   --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fpnet_fulleval_as_fold0 --v3 data/external/v3_models/code --out $T1 --k 100 --workers 2 --k_fpp 200 --k_pop 50   --sets P_np250 --alias_perview > $T1/features.log 2>&1
$PY -X utf8 -c "
import pandas as pd
F = pd.read_parquet('$T1/b1_features_P_np250.parquet'); r = F[F.official_key == 'BEBLLQPTMVOKAX']
print('ALIASTEST', r[['in_train_c1', 'lib_nref_c1', 'lib_sim_c1', 'in_train_c2', 'lib_nref_c2', 'lib_sim_c2']].to_dict('records'))"
K=4; FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_np083_f${K}conf; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/np061_f${K}pool/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets NP_H NP_X NP_N --alias_perview > $RUN/features.log 2>&1
echo "== $(date +%T) fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
for S in NP_H; do
  $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) fold $K gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
done
echo "CONF083_DONE $(date +%T)"
