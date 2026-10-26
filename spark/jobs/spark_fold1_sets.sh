#!/bin/bash
# 2026-10-26: fresh evaluation sets from identity FOLD 1 (unseen by the public fold-safe fpnet_fold1 and by the B1 rankers, which were fit on
# fold-0 molecules), stratified like dev2 (p2_select_v2 --fold 1, seed 11, <= 100 per stratum, dev + locked halves), then feature tables with
# fpnet_fold1 (+ --dump_gen) and GLACIER. For future one-time confirmations (generation stage 2 etc.); locked half kept closed.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
F1=data/external/fpnet_fold1_as_fold0; mkdir -p $F1
for f in data/external/fold_safe_fpnet/*; do bn=$(basename $f); [ "$bn" = fpnet_fold0.pt ] && continue; [ -e $F1/$bn ] || ln -s $(realpath $f) $F1/$bn; done
[ -e $F1/fpnet_fold0.pt ] || ln -s $(realpath data/external/fold_safe_fpnet/fpnet_fold1.pt) $F1/fpnet_fold0.pt
echo "== $(date +%T) fold-1 FPNet: $(sha256sum $F1/fpnet_fold0.pt | cut -c1-16)"
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $B/eval_set/p1_molecules.csv $B/eval_c1/p1_molecules.csv $B/locked_eval/p1_molecules.csv $B/eval_set2/v2/p2_molecules.csv $B/locked_eval2/v2/p2_molecules.csv $B/eval_set2/fit_pool/p2_molecules.csv $B/eval_set2/fit_pool_overflow/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv $B/eval_set3/p2_molecules.csv $B/eval_conf_fit/p2_molecules.csv $B/eval_conf_fit2/p2_molecules.csv"
for f in $EXCL; do [ -s $f ] || { echo "FOLD1 FAILED: missing exclusion $f"; exit 1; }; done
$PY -X utf8 $B/p2_select_v2.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds --exclude $EXCL --n 100 --seed 11 --fold 1 \
  --out_dir $B/eval_set_f1 --locked_dir $B/locked_eval_f1 > /tmp/f1_select.log 2>&1 || { echo "FOLD1 FAILED: select"; tail -5 /tmp/f1_select.log; exit 1; }
tail -3 /tmp/f1_select.log
$PY -c "import pandas as pd; d = pd.read_csv('$B/eval_set_f1/p2_molecules.csv'); print('dev', d.set.value_counts().to_dict(), len(d)); l = pd.read_csv('$B/locked_eval_f1/p2_molecules.csv'); print('locked', len(l))"
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/eval_set_f1/p2_molecules.csv').set.unique())))")
RUN=$B/run_f1dev; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/eval_set_f1/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --out $RUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --dump_gen $RUN/gen --sets $SETS > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
for S in $SETS; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-110)"
done
echo "FOLD1_SETS_DONE $(date +%T)"
