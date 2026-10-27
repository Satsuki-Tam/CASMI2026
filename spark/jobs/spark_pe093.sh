#!/bin/bash
# 093 on the Spark (moved from the PC 2026-10-27 22:30): gen_eval2pv (v7f main + EA variant ea0.5w1) with rank_v7a (V / V+E) and rank_v8w7a (V+P / V+P+E)
# on the 5 development tables, both models on the same platform. CPU only.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
PY=~/CASMI2026/.venv/bin/python
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { M=$1; T=$2; shift 2
  $PY -X utf8 gen_eval2pv.py --model $M/lambdarank.txt --refcmp --parents 0 "$@" --views c1,c2 --out diag/e093s_${M#rank_}_${T} --workers 8 > diag/e093s_${M#rank_}_${T}.log 2>&1
  echo "== $(date +%T) pe093s $M $T exit $?"; }
for M in rank_v7a rank_v8w7a; do
  ( ev $M np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
    ev $M np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
    ev $M panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
    ev $M f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
    ev $M f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS ) &
done
wait
$PY -X utf8 x093_summary.py e093s_v7a_ e093s_v8w7a_ > diag/x093s_summary.log 2>&1
echo "PE093S_DONE $(date +%T)"
