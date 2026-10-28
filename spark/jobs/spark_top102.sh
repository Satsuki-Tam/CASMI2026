#!/bin/bash
# fam_audit2 input: the v8w7a main order's top 25 per (set, view, molecule) on the development tables (gen_eval2fd --dump_top, no E models),
# then fam_audit2.py. Waits for the 104 dev evaluation to finish first (CPU).
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
until grep -q "E104_DONE" ../../spark/jobs/spark_e104dev.out 2>/dev/null; do sleep 30; done
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=~/CASMI2026/.venv/bin/python
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
tp() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 "$@" --views c1,c2 --dump_top diag/top102_$T.parquet --out diag/t102_$T --workers 2 > diag/t102_$T.log 2>&1
  rc=$?; echo "== $(date +%T) top102 $T exit $rc"; return $rc; }
PIDS=()
tp np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
tp np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
tp panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE & PIDS+=($!)
tp f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
tp f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
$PY -X utf8 fam_audit2.py > diag/fam_audit2.log 2>&1; echo "== $(date +%T) fam_audit2 exit $?"
echo "TOP102_DONE fail=$FAIL $(date +%T)"
