#!/bin/bash
# 145 kernel parity v2 (Codex 145): pipeline v2 (experiments/b1_e2k, own E2 index from the shipped map + E2 analog store + E2-time-free budgets)
# on the panel C1 evaluation test, then e2k_parity_check.py v2 (population, NaN-aware columns, E2 order, offline F, P vs the PC v8w7a C1 run, e2_failed 0).
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4
E=experiments/b1_baseline/eval_test_panel250_pc; W=experiments/e2/k_parity_c1_v2; M=experiments/e2/model_v1
[ -e $W ] && { echo "refused: $W exists"; exit 1; }
echo "== $(date +%T) pipeline $(sha256sum experiments/b1_e2k/b1_pipeline.py | cut -c1-12) model $(sha256sum $M/e2_lgb.txt | cut -c1-12) index $(sha256sum $M/e2_ik14_to_scorer.parquet | cut -c1-12)"
$PY -X utf8 experiments/b1_e2k/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_c1.json --rank_model experiments/b1_baseline/rank_v8w7a/lambdarank.txt \
  --tau 0.9 --main blend21 --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
  --frag_w_fallback 1 --gl_json $E/run_v8w7a_c1/gl_out.json --e2_model $M/e2_lgb.txt --e2_index $M/e2_ik14_to_scorer.parquet --e2_dump 1 --solution $E/solution.csv > $W.log 2>&1
rc=$?; echo "== $(date +%T) pipeline exit $rc $(grep -a '145 E2: [0-9]' $W.log | tail -1 | cut -c1-200)"; [ $rc = 0 ] || { echo "E2K_PARITY_DONE FAIL pipeline"; exit 1; }
$PY -X utf8 experiments/e2/e2k_parity_check.py --run $W --ewin experiments/e2/ewin/panel_np250 --set P_np250 --model $M/e2_lgb.txt --test $E/test.parquet \
  --p_ref $E/run_v8w7a_c1/submission.csv --p_ref_cand $E/run_v8w7a_c1/b1_candidates.parquet --hedge 0 > $W.check.log 2>&1
rc=$?; tail -30 $W.check.log; [ $rc = 0 ] && echo "E2K_PARITY_DONE PASS $(date '+%F %T')" || { echo "E2K_PARITY_DONE FAIL $(date '+%F %T')"; exit 1; }
