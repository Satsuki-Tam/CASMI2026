#!/bin/bash
# 058: FPNet ensemble on the panel-unseen benchmark. The public fold-safe kit excludes the panel identity groups from EVERY fold (make_split.py),
# so all five public fold models are unseen for the panel -> single fold-0 model vs the 5-model logit average (b1_features --extra_ckpts), same
# timsTOF queries, C2 view. FP-only window ranks (b1_molecules truth_fp_rank) + the registered main with GLACIER (MSG-contaminated on the panel).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; FS=data/external/fold_safe_fpnet
$PY -c "import pandas as pd; d = pd.read_csv('$B/panel_np250/p1_molecules.csv'); d['set'] = 'PUE'; d.to_csv('$B/panel_dg/pue_all.csv', index=False); print(len(d))"
for V in single ens5; do
  RUN=$B/run_ens058/$V; mkdir -p $RUN/work
  EXTRA=""; [ $V = ens5 ] && EXTRA="--extra_ckpts $FS/fpnet_fold1.pt $FS/fpnet_fold2.pt $FS/fpnet_fold3.pt $FS/fpnet_fold4.pt"
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $B/panel_dg/pue_all.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets PUE $EXTRA > $RUN/features.log 2>&1
  echo "== $(date +%T) $V features exit $? $(grep -a 'FPNet ensemble\|^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_PUE_in.json $RUN/work/gl_PUE.json -- --device cuda --site none --budget 3600 > $RUN/work/gl_PUE_resume.log 2>&1
  echo "== $(date +%T) $V gl $(grep -a '\[resume\] done' $RUN/work/gl_PUE_resume.log | cut -c1-100)"
  (cd $B && nice -n 5 $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run run_ens058/$V --gen run_ens058/$V/gen --sets PUE --eval_csv panel_dg/pue_all.csv --fold_safe $HOME/CASMI2026/$FS --views c1,c2 --out diag/ens058_$V --workers 6 > diag/ens058_$V.log 2>&1)
  echo "== $(date +%T) $V eval exit $?"
done
echo "ENS058_DONE $(date +%T)"
