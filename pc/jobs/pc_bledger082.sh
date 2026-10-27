#!/bin/bash
# 082 B-route ledger (Codex 081 Q1; exploratory diagnostic): per-molecule truth rank R, B-restricted rank r_B (B = COCONUT and not train in the
# view; C2 = counterfactual B^C2 proxy), probe-policy RR (1[R <= 25] / r_B), top-25 composition (B / T / PubChem-only), GL branch, for the 0.379 main
# (rank_v4b, gen_eval2p), the v7f main (rank_v7a, gen_eval2pv) and each + ea0.5w1, on 053 dev and the panel. Starts after the 077/078 and 080 evaluations.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "EVAL077078_DONE" logs/pc_eval077078.log 2>/dev/null && grep -q "V7FEA080_DONE" logs/pc_v7fea080.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; cd experiments/b1_baseline; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
for EV in "gen_eval2p.py rank_v4b v4b" "gen_eval2pv.py rank_v7a v7f"; do
  set -- $EV; SCR=$1; MOD=$2; TAG=$3
  for K in 1 2; do
    $PY -X utf8 $SCR --model $MOD/lambdarank.txt --parents 0 --run run_np053_f${K}dev --gen run_np053_f${K}dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f${K}dev/p2_molecules.csv \
      --fold_safe $FS --views c1,c2 --out diag/bl082_${TAG}_np053f${K}dev --dump_rank diag/bl082_${TAG}_np053f${K}dev_rank.parquet --workers 6 > diag/bl082_${TAG}_np053f${K}dev.log 2>&1
    echo "== $(date +%T) ledger $TAG np053f${K}dev exit $?"
  done
  $PY -X utf8 $SCR --model $MOD/lambdarank.txt --parents 0 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv \
    --fold_safe $FE --views c1,c2 --out diag/bl082_${TAG}_panel --dump_rank diag/bl082_${TAG}_panel_rank.parquet --workers 6 > diag/bl082_${TAG}_panel.log 2>&1
  echo "== $(date +%T) ledger $TAG panel exit $?"
done
echo "BLEDGER082_DONE $(date +%T)"
