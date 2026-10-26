#!/bin/bash
# 050 confirmation sets (fixed BEFORE any confirmation result): fresh E/F molecules from fold-1/2 identities unused by every earlier set
# (incl. 053 NP dev/conf), selected with p2_select_v2 (E/F strata first; the other strata of these selections are never evaluated), tables
# with each fold's fold-safe FPNet and the base GLACIER (E/F have no covered adduct -> runner_empty).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $(ls $B/*/p1_molecules.csv $B/*/p2_molecules.csv $B/*/v2/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv 2>/dev/null | grep -v '/pxconf_' | tr '\n' ' ')"
echo "== $(date +%T) exclusions $(echo $EXCL | wc -w) files"
for K in 1 2; do
  nice -n 5 $PY -X utf8 $B/p2_select_v2.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds --exclude $EXCL --n 100 --seed 5$K --fold $K \
    --out_dir $B/pxconf_f${K}a --locked_dir $B/pxconf_f${K}b > $B/pxconf_select_f$K.log 2>&1 || { echo "PXCONF FAILED select $K"; tail -3 $B/pxconf_select_f$K.log; exit 1; }
  grep -a -E "^[A-G]_|checks" $B/pxconf_select_f$K.log | cut -c1-200
  # confirmation molecules = E and F strata of BOTH halves (a + b), nothing else
  $PY -c "import pandas as pd; d = pd.concat([pd.read_csv('$B/pxconf_f${K}a/p2_molecules.csv'), pd.read_csv('$B/pxconf_f${K}b/p2_molecules.csv')]); d = d[d.set.isin(['E_np_negonly', 'F_np_uncovered'])]; import os; os.makedirs('$B/pxconf_f${K}', exist_ok=True); d.to_csv('$B/pxconf_f${K}/p2_molecules.csv', index=False); print('fold $K conf E/F', d.set.value_counts().to_dict())"
  FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_pxconf_f$K; mkdir -p $RUN/work
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/pxconf_f${K}/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets E_np_negonly F_np_uncovered > $RUN/features.log 2>&1
  echo "== $(date +%T) fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
  for S in E_np_negonly F_np_uncovered; do
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 1800 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) fold $K gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-80)"
  done
done
echo "PXCONF_SETS_DONE $(date +%T)"
