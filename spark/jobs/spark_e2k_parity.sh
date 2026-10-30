#!/bin/bash
# 145 kernel parity on Spark: the generated E2 pipeline (experiments/b1_e2k, make_e2k.py) on the panel C1 evaluation test (eval_test_panel250_pc,
# copied from the PC; GL from the PC v8w7a C1 run), then e2k_parity_check.py against the development panel tables and the offline fusion.
# Waits for the E2 model (experiments/e2/model_v1) and the panel feature table.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4
E=experiments/b1_baseline/eval_test_panel250_pc; W=experiments/e2/k_parity_c1; M=experiments/e2/model_v1/e2_lgb.txt
until [ -f $M ] && [ -f experiments/e2/ewin/panel_np250/e2f_manifest.json ]; do grep -q -E "E2_FEATS_FAIL" logs/spark_e2_feats2.log 2>/dev/null && { echo "E2K_PARITY_FAIL feats failed"; exit 1; }; sleep 30; done
[ -e $W ] && { echo "refused: $W exists"; exit 1; }
echo "== $(date +%T) pipeline $(sha256sum experiments/b1_e2k/b1_pipeline.py | cut -c1-12) model $(sha256sum $M | cut -c1-12)"
$PY -X utf8 experiments/b1_e2k/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_c1.json --rank_model experiments/b1_baseline/rank_v8w7a/lambdarank.txt \
  --tau 0.9 --main blend21 --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
  --frag_w_fallback 1 --gl_json $E/run_v8w7a_c1/gl_out.json --e2_model $M --e2_dump 1 --solution $E/solution.csv > $W.log 2>&1
rc=$?; echo "== $(date +%T) pipeline exit $rc $(grep -a '145 E2: [0-9]' $W.log | tail -1 | cut -c1-200)"; [ $rc = 0 ] || { echo "E2K_PARITY_FAIL pipeline"; exit 1; }
$PY -X utf8 experiments/e2/e2k_parity_check.py --run $W --ewin experiments/e2/ewin/panel_np250 --set P_np250 --model $M --p_ref $E/run_v8w7a_c1/submission.csv > $W.check.log 2>&1
rc=$?; tail -30 $W.check.log; [ $rc = 0 ] && echo "E2K_PARITY_DONE PASS $(date '+%F %T')" || { echo "E2K_PARITY_DONE FAIL $(date '+%F %T')"; exit 1; }
