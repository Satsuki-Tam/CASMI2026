#!/bin/bash
# 078 prep: exact reference comparability (refcmp_exact.py, verified against the tables) for every training / development table of the v8w recipe.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
rc() { R=$1; E=$2; shift 2; $PY -X utf8 refcmp_exact.py --run $R --eval_csv $E --sets "$@" --workers 2 > diag/refcmpx_$R.log 2>&1; echo "== $(date +%T) $R exit $? $(grep -a 'sim exact' diag/refcmpx_$R.log | awk '{print $2, $6, $7}' | tr '\n' ' ' | cut -c1-200)"; }
rc run_v3_p1 ../p1_baseline/run1/p1_molecules.csv A_timstof B_nplib
rc run_v3_eval eval_set/p1_molecules.csv A_timstof B_nplib
rc run_v3_c1 eval_c1/p1_molecules.csv B_nplib
rc run_tp_f3a train_pool_f3a/p2_molecules.csv $S5
rc run_tp_f4a train_pool_f4a/p2_molecules.csv $S5
rc run_f1dev eval_set_f1/p2_molecules.csv $S5
rc run_f2dev eval_set_f2/p2_molecules.csv $S5
rc run_np053_f1dev np053_f1dev/p2_molecules.csv NP_H NP_X NP_N
rc run_np053_f2dev np053_f2dev/p2_molecules.csv NP_H NP_X NP_N
rc run_panel_fe panel_np250/p1_molecules.csv P_np250
rc run_p2dev_fe eval_set2/v2/p2_molecules.csv $S5
echo "REFCMPX_DONE $(date +%T)"
