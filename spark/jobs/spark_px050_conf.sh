#!/bin/bash
# 050 confirmation (arm a, read once): 053 NP-truth conf sets -> tables (all strata, +dump_gen) + GLACIER (NP_H real; NP_X/NP_N empty),
# then arm a = NH4 / water-loss proxies on NP_X only (proxy_runner_in -> GL -> px_merge into a run copy), registered main via gen_eval2
# on NP_X for base and arm a (views c1,c2). NP_H tables are built for 057 but NOT evaluated here.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; IPY=$HOME/CASMI2026/.venv-ice/bin/python; R=$HOME/CASMI2026
until grep -q "NP053_SETS_DONE" logs/spark_np053_sets.log 2>/dev/null; do sleep 60; done
for K in 1 2; do
  FS=data/external/fpnet_fold${K}_as_fold0; RUN=$B/run_np053_f${K}conf; mkdir -p $RUN/work
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/np053_f${K}conf/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets NP_H NP_X NP_N > $RUN/features.log 2>&1
  echo "== $(date +%T) conf fold $K features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
  for S in NP_H NP_X NP_N; do
    $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 3600 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) conf fold $K gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
  done
  RPX=${RUN}_pxa; rm -rf $RPX; mkdir -p $RPX/work
  for f in $RUN/*; do [ "$(basename $f)" = work ] || ln -s $(realpath $f) $RPX/; done
  for f in $RUN/work/*; do ln -s $(realpath $f) $RPX/work/; done
  (cd $B && $PY -X utf8 proxy_runner_in.py --inp run_np053_f${K}conf/b1_runner_NP_X_in.json --out run_np053_f${K}conf_pxa/px_runner_NP_X_in.json --stats run_np053_f${K}conf_pxa/proxy_NP_X.json) || { echo "PXCONF050 FAILED proxy $K"; exit 1; }
  rm -f $RPX/work/gl_NP_X.json $RPX/work/gl_NP_X.json.meta.json
  $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier $RPX/px_runner_NP_X_in.json $RPX/work/glpx_NP_X.json -- --device cuda --site none --budget 3600 > $RPX/work/glpx_NP_X_resume.log 2>&1
  echo "== $(date +%T) conf fold $K proxy gl $(grep -a '\[resume\] done' $RPX/work/glpx_NP_X_resume.log | cut -c1-90)"
  (cd $B && $PY -X utf8 px_merge.py --orig run_np053_f${K}conf/work/gl_NP_X.json --px run_np053_f${K}conf_pxa/work/glpx_NP_X.json --out run_np053_f${K}conf_pxa/work/gl_NP_X.json) || { echo "PXCONF050 FAILED merge $K"; exit 1; }
  for V in base pxa; do
    RR=run_np053_f${K}conf; [ $V = pxa ] && RR=run_np053_f${K}conf_pxa
    (cd $B && nice -n 5 $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run $RR --gen run_np053_f${K}conf/gen --sets NP_X --eval_csv np053_f${K}conf/p2_molecules.csv --fold_safe $R/$FS --views c1,c2 --out diag/pxconf050_f${K}_$V --workers 6 > diag/pxconf050_f${K}_$V.log 2>&1)
    echo "== $(date +%T) conf fold $K eval $V exit $?"
  done
done
echo "PXCONF050_DONE $(date +%T)"
