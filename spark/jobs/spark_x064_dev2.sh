#!/bin/bash
# 064 diagnostic: dev2 tables rebuilt with the public fold-0 FPNet (dev2 = fold 0 -> unseen), GLACIER, gen_eval2 with rank_v4b and rank_v8w.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; FS=data/external/fold_safe_fpnet; RUN=$B/run_p2dev_f0x; mkdir -p $RUN/work
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/eval_set2/v2/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $S5 > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-250)"
for S in $S5; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 3600 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-80)"
done
export NUMBA_NUM_THREADS=6
cd $B
for M in rank_v4b rank_v8w; do
  nice -n 5 $PY -X utf8 gen_eval2.py --model $M/lambdarank.txt --parents 0 --run run_p2dev_f0x --gen run_p2dev_f0x/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $HOME/CASMI2026/$FS --views c1,c2 --out diag/x064_${M}_p2dev_f0 --workers 6 > diag/x064_${M}_p2dev_f0.log 2>&1
  echo "== $(date +%T) eval $M exit $?"
done
echo "X064_DONE $(date +%T)"
