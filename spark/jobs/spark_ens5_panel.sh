#!/bin/bash
# 2026-10-26 02:00 (diagnostic, pre-registered in reports/agent_review/027_prereg_ens2.md addendum before the run): five fold-safe FPNets
# (dmitriigluzdov/casmi26-fold-safe-fpnet; model k trained without fold k AND without the panel natural products) averaged (ENS5) vs fold 0
# alone (M2x), on the panel only (unseen by all five models, both views). dev2 is NOT clean for ENS5 (folds 1-4 trained on fold-0 identities).
set -u
cd ~/CASMI2026 || exit 1
until grep -q "ENS2_DONE" logs/spark_ens2_chain.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FS=data/external/fold_safe_fpnet; RUN=$B/run_ens5_panel; OUT=$B/ens5_eval_panel
echo "== $(date +%T) ENS5 features (folds 0-4: $(for k in 0 1 2 3 4; do sha256sum $FS/fpnet_fold$k.pt | cut -c1-8; done | tr '\n' ' '))"
mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --extra_ckpts $FS/fpnet_fold1.pt $FS/fpnet_fold2.pt $FS/fpnet_fold3.pt $FS/fpnet_fold4.pt \
  --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --sets P_np250 > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? : $(grep -a '^FPNet ensemble\|^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
.venv-ice/bin/python spark/jobs/ice_resume.py --seed $B/run_panel_v3b/work/gl_P_np250.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_P_np250_in.json $RUN/work/gl_P_np250.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_P_np250_resume.log 2>&1
echo "== gl $(grep -a '\[resume\] done' $RUN/work/gl_P_np250_resume.log | cut -c1-120)"
export OMP_NUM_THREADS=2; rm -rf $OUT; mkdir -p $OUT
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/panel_np250/p1_molecules.csv --cands M2x:$B/run_panel_v3b:$B/rank_v4b/lambdarank.txt:0 ENS5:$B/$(basename $RUN):$B/rank_v4b/lambdarank.txt:0 \
  --main_of M2x=blend21 ENS5=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets P_np250 --out $OUT > $OUT/eval.log 2>&1
echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-170
echo "ENS5_DONE $(date +%T)"
