#!/bin/bash
# 029_decision section 2 (pre-registered before the run): rankers A (existing rank_rk_fx), B (C1 rows of FPNet-seen identities only), C (B + fp_pos),
# evaluated on the full_rk tables (full_rk ledger) and on the adoption tables (full_eval, full_eval ledger) vs M2x_fe and M2x.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; P0=$B/rank_v4b/rank_results.json; EXPO=experiments/fpnet_full/full_rk/query_identity_exposure.csv; LED=$B/ledgers
RUNS="$B/run_rk_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_rk_eval:$B/eval_set/p1_molecules.csv $B/run_rk_c1:$B/eval_c1/p1_molecules.csv"
echo "== $(date +%T) code: rankfeats $(sha256sum $B/b1_rankfeats.py | cut -c1-12) rank_train $(sha256sum $B/b1_rank_train.py | cut -c1-12) locked_eval $(sha256sum $B/b1_locked_eval.py | cut -c1-12)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_rk_c1s --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 --c2_drop_exposure $EXPO --c1_seen_only $EXPO > $B/rank_rk_c1s_train.log 2>&1
echo "== $(date +%T) B rank_rk_c1s exit $? : $(grep -a 'c1 rows of identities\|fit groups after' $B/rank_rk_c1s_train.log | tr '\n' ' ' | cut -c1-260)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_rk_c1s_fp --feats v2_noice_exp --drop lib_nref in_train negpool --c1_repeat 3 --params_from $P0 --c2_drop_exposure $EXPO --c1_seen_only $EXPO --exposure_ledger $LED/ledger_full_rk.parquet > $B/rank_rk_c1s_fp_train.log 2>&1
echo "== $(date +%T) C rank_rk_c1s_fp exit $? : $(grep -a 'features:\|c1 rows of identities' $B/rank_rk_c1s_fp_train.log | tr '\n' ' ' | cut -c1-260)"
$PY - <<PY
import lightgbm as lgb
f = lgb.Booster(model_file="$B/rank_rk_c1s_fp/lambdarank.txt").feature_name(); print("C features:", len(f), "| fp_pos" if "fp_pos" in f else "| NO fp_pos", "| negpool PRESENT (abort)" if "negpool" in f else "| no negpool")
assert "negpool" not in f and "fp_pos" in f
PY
[ $? = 0 ] || { echo "C1S FAILED: feature list check"; exit 1; }
grep -a "importance" $B/rank_rk_c1s_fp_train.log | cut -c1-260
export OMP_NUM_THREADS=2
for E in "1_panel panel_np250/p1_molecules.csv run_rk_panel P_np250" "1_p2dev eval_set2/v2/p2_molecules.csv run_rk_p2dev C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$B/$2; run=$3; shift 3; OUT=$B/c1s_eval_$name; rm -rf $OUT; mkdir -p $OUT
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands RK_old:$B/$run:$B/rank_v4b/lambdarank.txt:0 A:$B/$run:$B/rank_rk_fx/lambdarank.txt:0 B:$B/$run:$B/rank_rk_c1s/lambdarank.txt:0 C:$B/$run:$B/rank_rk_c1s_fp/lambdarank.txt:0 \
    --cand_ledger C=$LED/ledger_full_rk.parquet --main_of RK_old=blend21 A=blend21 B=blend21 C=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "== $(date +%T) $name evaluator exit $?"
done
for E in "2_panel panel_np250/p1_molecules.csv run_panel_fe run_panel_v3b P_np250" "2_p2dev eval_set2/v2/p2_molecules.csv run_p2dev_fe run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$B/$2; fe=$3; base=$4; shift 4; OUT=$B/c1s_eval_$name; rm -rf $OUT; mkdir -p $OUT
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x_fe:$B/$fe:$B/rank_v4b/lambdarank.txt:0 M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 FE_A:$B/$fe:$B/rank_rk_fx/lambdarank.txt:0 FE_B:$B/$fe:$B/rank_rk_c1s/lambdarank.txt:0 FE_C:$B/$fe:$B/rank_rk_c1s_fp/lambdarank.txt:0 \
    --cand_ledger FE_C=$LED/ledger_full_eval.parquet --main_of M2x_fe=blend21 M2x=blend21 FE_A=blend21 FE_B=blend21 FE_C=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "== $(date +%T) $name evaluator exit $?"
done
echo "C1S_DONE $(date +%T)"
