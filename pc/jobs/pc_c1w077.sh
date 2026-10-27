#!/bin/bash
# 077 (077_prereg_c1weight.md): C1-weight control v9b_w with the same 6 development tables, one gen_eval2m pass (rank_v4b, v8w_pc, v9a, v9b, v9b_w). Starts after the 076 confirmation (CPU slot).
# rank_v9h, rank_v9a, rank_v9b on every development table. Check first: v4b / v8w outputs must equal the Spark CSVs (r047 / r056) on f1dev
# (implementation + environment check); stop if not. CPU only.
set -u
cd /c/kaggle/CASMI || exit 1
until grep -q "CONF076_DONE" logs/pc_conf076.log 2>/dev/null; do sleep 60; done
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P0=$B/rank_v4b/rank_results.json
cd $B
MS="rank_v4b rank_v8w_pc rank_v9a rank_v9b rank_v9b_w"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  MOD=$(for M in $MS; do echo -n "$M/lambdarank.txt,"; done | sed 's/,$//'); OUT=$(for M in $MS; do echo -n "diag/r077m_${M}_$T,"; done | sed 's/,$//')
  $PY -X utf8 gen_eval2m.py --model $MOD --parents 0 "$@" --views c1,c2 --out $OUT --workers 6 > diag/r077m_$T.log 2>&1
  echo "== $(date +%T) eval $T exit $?"; }
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS

ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE
echo "C1W077_DONE $(date +%T)"
