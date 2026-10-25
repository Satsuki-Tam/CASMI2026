#!/bin/bash
# Codex 022 implementation check for the M2x + full_eval candidate: the SUBMISSION pipeline loading our checkpoint with --fpnet_ckpt vs the
# evaluator tables built with the same checkpoint (run_panel_fe), on 16 panel molecules chosen to cover the branches (GL-covered multi-adduct,
# GL-short fallback, library priority, the largest windows), both views, shared forward cache (--forward_from pipe), thresholds 1.0, with the
# model, predictions and stage stats passed so that the OUTPUT comparison actually runs. Only the FPNet differs from M2x (k_pool 0, pcl 0).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; E=$B/eval_test_parity16_fe; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
until [ -s $FRUN/b1_features_P_np250.parquet ]; do sleep 60; done
echo "== $(date +%T) parity16 full_eval: ckpt sha $(sha256sum $(readlink -f $CK) | cut -c1-16), pipeline sha $(sha256sum $B/b1_pipeline.py | cut -c1-16)"
rm -rf $E; mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv $B/panel_np250/parity16_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --sets P_np250 || { echo "PARITYFE FAILED: make_eval_test"; exit 1; }
FAIL=0
for mode in c2 c1; do
  echo "== $(date +%T) pipeline $mode (--fpnet_ckpt full_eval)"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK > $E/run_$mode.log 2>&1
  rc=$?; echo "pipeline exit $rc; $(grep -a 'FPNet checkpoint' $E/run_$mode.log | cut -c1-140)"; [ $rc = 0 ] && [ -s $E/run_$mode/b1_candidates.parquet ] || { echo "PARITYFE FAILED: pipeline $mode"; exit 1; }
  $PY -X utf8 $B/b1_parity.py --dump $E/run_$mode/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $E/run_$mode/parity_${mode}_shared.md \
    --pred_main $E/run_$mode/submission.csv --pred_fixed $E/run_$mode/submission_fixed.csv --stage_stats $E/run_$mode/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_$mode --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 > $E/run_$mode/parity.log 2>&1
  prc=$?; echo "parity $mode exit $prc"; grep -a "PARITY\|identical\|differs\|query selection\|output agreement\|^| main\|^| insurance\|fallback\|n_compared\|molecules" $E/run_$mode/parity.log | cut -c1-200 | head -20
  [ $prc = 0 ] || FAIL=1
  echo "-- manifest: $(grep -o '"fpnet_ckpt_sha256": "[0-9a-f]*"' $E/run_$mode/b1_run_manifest.json) $(grep -o '"fusion": {[^}]*}' $E/run_$mode/b1_run_manifest.json | cut -c1-160)"
done
[ $FAIL = 0 ] && echo "PARITYFE_DONE PASS $(date +%T)" || echo "PARITYFE_DONE FAIL $(date +%T)"
