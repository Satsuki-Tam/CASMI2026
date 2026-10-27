#!/bin/bash
# 087 (087_prereg_v8w7a.md): one gen_eval2m --v7f pass with rank_v7a (Spark), rank_v7a_pc (control) and rank_v8w7a (candidate) on the development tables. CPU only.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
MS="rank_v7a rank_v7a_pc rank_v8w7a"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  MOD=$(for M in $MS; do echo -n "$M/lambdarank.txt,"; done | sed 's/,$//'); OUT=$(for M in $MS; do echo -n "diag/r087m_${M}_$T,"; done | sed 's/,$//')
  $PY -X utf8 gen_eval2m.py --model $MOD --v7f --parents 0 "$@" --views c1,c2 --out $OUT --workers 4 > diag/r087m_$T.log 2>&1
  echo "== $(date +%T) eval087 $T exit $?"; }
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
echo "EVAL087_DONE $(date +%T)"
