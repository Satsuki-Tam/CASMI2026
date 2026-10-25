#!/bin/bash
# 028_decision section 5 (pre-registered before the run): exposure-feature ranker rank_rk_exp. Regression tests first (abort if they fail).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; P0=$B/rank_v4b/rank_results.json; EXPO=experiments/fpnet_full/full_rk/query_identity_exposure.csv; LED=$B/ledgers
RUNS="$B/run_rk_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_rk_eval:$B/eval_set/p1_molecules.csv $B/run_rk_c1:$B/eval_c1/p1_molecules.csv"
echo "== $(date +%T) code: rankfeats $(sha256sum $B/b1_rankfeats.py | cut -c1-12) rank_train $(sha256sum $B/b1_rank_train.py | cut -c1-12) locked_eval $(sha256sum $B/b1_locked_eval.py | cut -c1-12)"
# regression 1: the modified trainer without a ledger reproduces rank_rk_fx exactly
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out /tmp/rk_fx_regress --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 --c2_drop_exposure $EXPO > /tmp/rk_fx_regress.log 2>&1
if cmp -s <(grep -v "^\[\|feature_infos\|^$" $B/rank_rk_fx/lambdarank.txt) <(grep -v "^\[\|feature_infos\|^$" /tmp/rk_fx_regress/lambdarank.txt) || [ "$(sha256sum < $B/rank_rk_fx/lambdarank.txt)" = "$(sha256sum < /tmp/rk_fx_regress/lambdarank.txt)" ]; then echo "REGRESSION 1 PASS (retrained rank_rk_fx identical)"; else echo "REGRESSION 1 FAIL"; diff <(head -40 $B/rank_rk_fx/lambdarank.txt) <(head -40 /tmp/rk_fx_regress/lambdarank.txt) | head; exit 1; fi
# regression 2: the modified evaluator reproduces the existing rank_v4b predictions (panel, full_rk tables)
rm -rf /tmp/eval_regress; $PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/panel_np250/p1_molecules.csv --cands RK_old:$B/run_rk_panel:$B/rank_v4b/lambdarank.txt:0 --main_of RK_old=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets P_np250 --out /tmp/eval_regress > /tmp/eval_regress.log 2>&1
R2=PASS; for v in c1 c2; do cmp -s $B/rk_eval_panel/pred_P_np250_${v}_RK_old_blend21.csv /tmp/eval_regress/pred_P_np250_${v}_RK_old_blend21.csv || R2=FAIL; done; echo "REGRESSION 2 $R2"; [ $R2 = PASS ] || exit 1
# train the exposure ranker (same recipe + full_rk ledger)
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_rk_exp --feats v2_noice_exp --drop lib_nref in_train --c1_repeat 3 --params_from $P0 --c2_drop_exposure $EXPO --exposure_ledger $LED/ledger_full_rk.parquet > $B/rank_rk_exp_train.log 2>&1
echo "== $(date +%T) rank_rk_exp exit $? : $(grep -a 'exposure ledger\|features:' $B/rank_rk_exp_train.log | tr '\n' ' ' | cut -c1-200)"; grep -a "importance" $B/rank_rk_exp_train.log | cut -c1-300
export OMP_NUM_THREADS=2
# (A) full_rk tables, (B) full_eval tables
for E in "A_panel panel_np250/p1_molecules.csv run_rk_panel full_rk P_np250" "A_p2dev eval_set2/v2/p2_molecules.csv run_rk_p2dev full_rk C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$B/$2; run=$3; led=$4; shift 4; OUT=$B/rkexp_eval_$name; rm -rf $OUT; mkdir -p $OUT
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands RK_old:$B/$run:$B/rank_v4b/lambdarank.txt:0 RK_new:$B/$run:$B/rank_rk_fx/lambdarank.txt:0 RK_exp:$B/$run:$B/rank_rk_exp/lambdarank.txt:0 \
    --cand_ledger RK_exp=$LED/ledger_$led.parquet --main_of RK_old=blend21 RK_new=blend21 RK_exp=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "== $(date +%T) $name evaluator exit $?"
done
for E in "B_panel panel_np250/p1_molecules.csv run_panel_fe run_panel_v3b P_np250" "B_p2dev eval_set2/v2/p2_molecules.csv run_p2dev_fe run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$B/$2; fe=$3; base=$4; shift 4; OUT=$B/rkexp_eval_$name; rm -rf $OUT; mkdir -p $OUT
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x_fe:$B/$fe:$B/rank_v4b/lambdarank.txt:0 M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 FE_new:$B/$fe:$B/rank_rk_fx/lambdarank.txt:0 FE_exp:$B/$fe:$B/rank_rk_exp/lambdarank.txt:0 \
    --cand_ledger FE_exp=$LED/ledger_full_eval.parquet --main_of M2x_fe=blend21 M2x=blend21 FE_new=blend21 FE_exp=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "== $(date +%T) $name evaluator exit $?"
done
echo "RKEXP_DONE $(date +%T)"
