#!/bin/bash
# Panel table with the fold-safe fpnet_fold0 (the 250 panel identities are unseen by every fold-safe FPNet) = class-2 simulation for Enveda NPs,
# current b1_features with gen dump, + GLACIER. For the transductive-generation study (family structure: 30% of panel molecules derivable from another).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; RUN=$B/run_panel_f0; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $RUN --k 100 --workers 12 \
  --k_fpp 200 --k_pop 50 --dump_gen $RUN/gen --sets P_np250 > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
.venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_P_np250_in.json $RUN/work/gl_P_np250.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_resume.log 2>&1
echo "== $(date +%T) gl $(grep -a '\[resume\] done' $RUN/work/gl_resume.log | cut -c1-90)"
echo "PANELF0_DONE $(date +%T)"
