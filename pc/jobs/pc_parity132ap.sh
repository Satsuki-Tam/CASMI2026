#!/bin/bash
# 132 parity B re-check (2026-10-30; documented known case 076 / Codex 082 / 083): the C1 parity failed on ONE molecule (SQFSKOYWJBQGKQ, candidate
# BEBLLQPTMVOKAX) because the old evaluator table run_panel_fe_pc aggregates an official key's aliases over the C1 + C2 union shortlist, while the
# pipeline (= the submission) aggregates per view (--alias_perview, Codex 082). Rebuild the same PC panel table with --alias_perview (all other
# arguments as 076b) and rerun the registered parity B comparison (same pipeline outputs, same tool and options) for both views.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
GPU_APPS=$(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>&1); rc=$?
PY_APPS=$(echo "$GPU_APPS" | grep -i "python" || true)
{ [ $rc -eq 0 ] && [ -z "$PY_APPS" ]; } || { echo "refused: a Python GPU process is running ($PY_APPS)"; exit 1; }
B=experiments/b1_baseline; S=experiments/b1_elite; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; FRUN=$B/run_panel_fe_pc_ap; MODEL=$B/rank_v8w7a/lambdarank.txt
FE=data/external/fpnet_fulleval_as_fold0; EM=$B/rank_e1r/lambdarank.txt; EK=$B/diag/e_window_keys_v2.parquet
[ -e $FRUN/b1_features_P_np250.parquet ] && { echo "exists: $FRUN"; exit 1; }
mkdir -p $FRUN
$PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FE --v3 data/external/v3_models/code --out $FRUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --sets P_np250 --alias_perview > $FRUN/features.log 2>&1; rc=$?
echo "== $(date '+%F %T') PC panel table (alias_perview) exit $rc $(grep -a '^saved' $FRUN/features.log | cut -c1-120)"; [ $rc -eq 0 ] || exit 1
FAIL=0
for mode in c2 c1; do
  W=$E/run_e132_${mode}; G=$E/run_v8w7a_${mode}
  $PY -X utf8 $S/b1_parity_e132.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_ap_${mode}.md \
    --pred_main $W/submission_pref.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $G --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
    --analog_parquet $B/diag/analog3_fe_pcpc.parquet --frag_w_fallback 1 --frag_parquet $B/diag/frag_panel_pc.parquet \
    --elite_model $EM --elite_keys $EK --pred_elite $W/submission.csv > $W/parity_ap.log 2>&1
  rc=$?; echo "parity132ap $mode exit $rc $(tail -1 $W/parity_ap.log | cut -c1-250)"; [ $rc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "PARITY132AP_DONE PASS $(date '+%F %T')" || { echo "PARITY132AP_DONE FAIL $(date '+%F %T')"; exit 1; }
