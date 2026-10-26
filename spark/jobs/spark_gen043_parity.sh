#!/bin/bash
# 042 parity of the FROZEN sources (experiments/b1_gen042) on parity16, both views: the 0.379 configuration (--analog_w 0.5) + --gen_rank 3 --gen_rule fzgate.
#  (1) b1_parity on submission_base.csv (= the list before the derivability / generation terms) must PASS exactly like ana035;
#  (2) gen_parity: chosen novel structure, derivable keys and the insertion vs gen_eval --dump_choice on the same molecules.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_gen042b; PY=$HOME/CASMI2026/.venv/bin/python; E=$B/eval_test_parity16_fe; FRUN=$B/run_panel_fe; MODEL=$B/rank_v4b/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt
echo "== $(date +%T) frozen pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) gen $(sha256sum $S/b1_gen.py | cut -c1-12) analog $(sha256sum $S/b1_analog.py | cut -c1-12)"
(cd $B && NUMBA_NUM_THREADS=8 $PY -X utf8 gen_eval2p.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/parity16_molecules.csv --views c1,c2 --out diag/geneval2p_parity16 --dump_choice diag/genchoice2p_parity16.parquet --workers 8 > diag/geneval2p_parity16.log 2>&1; echo "== $(date +%T) gen_eval parity16 exit $?")
FAIL=0
for mode in c2 c1; do
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $E/run_gen043_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0.5 --analog_feat ap --gen_rank 3 --gen_rule fzgate > $E/run_gen043_$mode.log 2>&1
  echo "== $(date +%T) pipeline $mode exit $? $(grep -a 'submission written' $E/run_gen043_$mode.log | cut -c1-220)"
  $PY -X utf8 $B/b1_parity.py --dump $E/run_gen043_$mode/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $E/run_gen043_$mode/parity_${mode}.md \
    --pred_main $E/run_gen043_$mode/submission_base.csv --pred_fixed $E/run_gen043_$mode/submission_fixed.csv --stage_stats $E/run_gen043_$mode/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $E/run_gen043_$mode --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0.5 --analog_feat ap --analog_parquet $B/diag/analog3_fe.parquet > $E/run_gen043_$mode/parity.log 2>&1
  prc=$?; echo "base-list parity $mode exit $prc"; grep -a "PARITY\|analog feature parity\|^| main\|^| insurance" $E/run_gen043_$mode/parity_${mode}.md | cut -c1-200
  [ $prc = 0 ] || FAIL=1
  $PY -X utf8 $B/gen_parity2.py --pipe_work $E/run_gen043_$mode --choice $B/diag/genchoice2p_parity16.parquet --view $mode --gen_rank 3 --gen_rule fzgate --out $E/run_gen043_$mode/parity_gen_${mode}.md
  grc=$?; echo "gen parity $mode exit $grc"; [ $grc = 0 ] || FAIL=1
done
[ $FAIL = 0 ] && echo "GEN043PAR_DONE PASS $(date +%T)" || echo "GEN043PAR_DONE FAIL $(date +%T)"
