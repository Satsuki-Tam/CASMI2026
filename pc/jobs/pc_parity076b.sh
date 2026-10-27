#!/bin/bash
# 076 parity, same-platform rerun: the c2 run showed top-1 / RR identical 250/250 but FP scores differ by GPU (Spark-built evaluator table vs PC
# pipeline; fp abs diff mean 0.13) -> ordered top-25 cannot match. Build the panel evaluator table on the PC (full_eval FPNet, same features as
# run_panel_fe; GL is taken from the pipeline outputs) and rerun b1_parity for both views against the SAME pipeline runs. CUDA (features).
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "PARITY076_DONE" logs/pc_parity076.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; FRUN=$B/run_panel_fe_pc; MODEL=$B/rank_v4b/lambdarank.txt
FE=data/external/fpnet_fulleval_as_fold0
mkdir -p $FRUN
$PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FE --v3 data/external/v3_models/code --out $FRUN --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --sets P_np250 > $FRUN/features.log 2>&1
echo "== $(date +%T) PC panel table exit $? $(grep -a '^saved' $FRUN/features.log | cut -c1-120)"
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=3 $PY -X utf8 $B/analog_probe.py --runs run_panel_fe_pc:panel_np250/p1_molecules.csv:P_np250 --out diag/analog3_fe_pcpc.parquet --threads 3 > $B/diag/analog3_fe_pcpc.log 2>&1
echo "== $(date +%T) analog probe exit $?"
FAIL=0
for mode in c2 c1; do
  W=$E/run_ea_${mode}
  $PY -X utf8 $B/b1_parity.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_pc_${mode}.md \
    --pred_main $W/submission.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $W --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap \
    --analog_parquet $B/diag/analog3_fe_pcpc.parquet --ea_w 1 --ea_theta 0.5 > $W/parity_pc.log 2>&1
  rc=$?; echo "parity_pc $mode exit $rc $(tail -1 $W/parity_pc.log | cut -c1-200)"; [ $rc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "PARITY076B_DONE PASS $(date +%T)" || echo "PARITY076B_DONE FAIL $(date +%T)"
