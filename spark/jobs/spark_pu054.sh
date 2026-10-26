#!/bin/bash
# 054: "panel-unseen" (PU) class-2 benchmark = the Enveda NP panel (timsTOF queries, famous NPs like the hidden test) with the FOLD-SAFE FPNet
# of each molecule's identity fold (never saw the identity), C2 view (references removed) -> the most hidden-like class-2 regime we can build.
# GLACIER is MSG-contaminated on the panel (236/250 in MSG): GL outputs are an optimistic bound; the fallback path (no GL) is the other bound.
# Tables of DG_T per fold with --dump_gen (dg052 ran without it), GLACIER, and the registered main via gen_eval2 (--parents 0, views c1,c2).
set -u
cd ~/CASMI2026 || exit 1
until grep -q "DG052_DONE" logs/spark_dg052.log 2>/dev/null; do sleep 30; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
for k in 0 1 2 3 4; do
  if [ $k = 0 ]; then FS=data/external/fold_safe_fpnet; else FS=data/external/fpnet_fold${k}_as_fold0; fi
  RUN=$B/run_pu054/f$k; mkdir -p $RUN/work
  $PY -c "import pandas as pd; d = pd.read_csv('$B/panel_dg/p1_f$k.csv'); d = d[d.set == 'DG_T'].assign(set='PU'); d.to_csv('$B/panel_dg/pu_f$k.csv', index=False); print(len(d))"
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/panel_dg/pu_f$k.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets PU > $RUN/features.log 2>&1
  echo "== $(date +%T) fold $k features exit $? $(grep -a '^saved' $RUN/features.log | cut -c1-120)"
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_PU_in.json $RUN/work/gl_PU.json -- --device cuda --site none --budget 3600 > $RUN/work/gl_PU_resume.log 2>&1
  echo "== $(date +%T) fold $k gl $(grep -a '\[resume\] done' $RUN/work/gl_PU_resume.log | cut -c1-100)"
  (cd $B && $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run run_pu054/f$k --gen run_pu054/f$k/gen --sets PU --eval_csv panel_dg/pu_f$k.csv --fold_safe $HOME/CASMI2026/$FS --views c1,c2 --out diag/pu054_f$k --workers 8 > diag/pu054_f$k.log 2>&1)
  echo "== $(date +%T) fold $k eval exit $?"
done
echo "PU054_DONE $(date +%T)"
