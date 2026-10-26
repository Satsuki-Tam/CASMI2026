#!/bin/bash
# 050 arm a: parity of the frozen 0.379 sources (experiments/b1_ana035, pipeline ef8f8f96) + --adduct_proxy on ALL 250 panel molecules,
# both views: b1_parity with the pipeline's own forward outputs (incl. the proxy GLACIER scores) must reproduce the pipeline's main list.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "PX050_DEV_DONE" logs/spark_px050_dev.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_ana035; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_panel250_fe; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
echo "== $(date +%T) frozen pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) b1_common $(sha256sum $S/b1_common.py | cut -c1-12)"
FAIL=0
for mode in c2 c1; do
  W=$E/run_pxa_$mode
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap --adduct_proxy > $W.log 2>&1
  rc=$?; echo "== $(date +%T) pipeline $mode exit $rc $(grep -a 'submission written' $W.log | cut -c1-200)"; [ $rc = 0 ] || FAIL=1
  $PY -c "import pandas as pd; s = pd.read_csv('$W/b1_stage_stats.csv'); print('molecules with proxies', int((s.n_proxy > 0).sum()), 'proxy spectra', int(s.n_proxy.sum()))"
  $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_${mode}.md \
    --pred_main $W/submission.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap --analog_parquet $B/diag/analog3_fe.parquet > $W/parity.log 2>&1
  rc=$?; echo "parity $mode exit $rc $(tail -1 $W/parity.log | cut -c1-120)"; [ $rc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "PX050_PARITY_DONE PASS $(date +%T)" || echo "PX050_PARITY_DONE FAIL $(date +%T)"
