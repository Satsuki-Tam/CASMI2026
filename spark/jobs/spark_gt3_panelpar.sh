#!/bin/bash
# 043 pre-submission check (b): the frozen gt3 pipeline vs gen_eval2p on ALL 250 panel molecules (both views), so that gate decisions with alias
# rank-3 candidates (fp = max over spellings) are exercised. Base list must equal the registered anaw0.5 (b1_parity, shared forward cache).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_gen042b; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_panel250_fe; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
[ -s $E/test.parquet ] || $PY -X utf8 $B/make_eval_test.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --sets P_np250 > $E.build.log 2>&1
echo "== $(date +%T) test built: $(ls $E | tr '\n' ' ')"
until grep -q "GT3AUDIT_DONE\|panel exit" logs/spark_gt3_audit.log 2>/dev/null; do sleep 30; done   # needs diag/genchoice2p_panel.parquet
FAIL=0
for mode in c2 c1; do
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $E/run_gt3_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap --gen_rank 3 --gen_rule fzgate > $E/run_gt3_$mode.log 2>&1
  echo "== $(date +%T) pipeline $mode exit $? $(grep -a 'submission written' $E/run_gt3_$mode.log | cut -c1-220)"
  $PY -X utf8 $B/b1_parity.py --dump $E/run_gt3_$mode/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $E/run_gt3_$mode/parity_${mode}.md \
    --pred_main $E/run_gt3_$mode/submission_base.csv --pred_fixed $E/run_gt3_$mode/submission_fixed.csv --stage_stats $E/run_gt3_$mode/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_gt3_$mode --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap --analog_parquet $B/diag/analog3_fe.parquet > $E/run_gt3_$mode/parity.log 2>&1
  prc=$?; echo "base-list parity $mode exit $prc"; grep -a "PARITY\|analog feature parity\|^| main\|^| insurance" $E/run_gt3_$mode/parity_${mode}.md | cut -c1-200; [ $prc = 0 ] || FAIL=1
  $PY -X utf8 $B/gen_parity2.py --pipe_work $E/run_gt3_$mode --choice $B/diag/genchoice2p_panel.parquet --view $mode --gen_rank 3 --gen_rule fzgate --out $E/run_gt3_$mode/parity_gen_${mode}.md
  grc=$?; echo "gen parity $mode exit $grc"; grep -a "mismatches\|GENPARITY" $E/run_gt3_$mode/parity_gen_${mode}.md | head -3; [ $grc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "GT3PANELPAR_DONE PASS $(date +%T)" || echo "GT3PANELPAR_DONE FAIL $(date +%T)"
