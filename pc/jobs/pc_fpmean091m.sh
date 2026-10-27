#!/bin/bash
# 091 platform control (amendment): the same gen_eval2fd override pass with the PC-recomputed MERGED fp (fp_m) instead of fp_s, so that
# fp_s - fp_m isolates the per-spectrum averaging from the Spark/PC FPNet numeric differences in the tables. CPU only.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
until grep -q "FPMEAN_SCORED" /c/kaggle/CASMI/logs/pc_fpmean091.log 2>/dev/null; do sleep 30; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
$PY -I -X utf8 addrw_m.py diag/fpmean_np053f1dev.parquet diag/fpmean_np053f2dev.parquet diag/fpmean_f1dev.parquet diag/fpmean_f2dev.parquet diag/fpmean_panel.parquet diag/fpmean_p2dev.parquet
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model rank_v7a_pc/lambdarank.txt --v7f --fp_override diag/fpmean_${T}_m.parquet --fp_col fp_m --parents 0 "$@" --views c1,c2 --out diag/r091mm_rank_v7a_pc_$T --workers 4 > diag/r091mm_$T.log 2>&1
  echo "== $(date +%T) eval091m $T exit $?"; }
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
echo "EVAL091M_DONE $(date +%T)"
