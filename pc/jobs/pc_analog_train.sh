#!/bin/bash
# prep for v7a-type rankers on the PC (Codex 082 next step): analog features (analog_probe, same masks as the evaluator) for the training tables.
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 PYTHONUTF8=1; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe
ap() { N=$1; shift; NUMBA_NUM_THREADS=4 $PY -X utf8 analog_probe.py --runs "$@" --out diag/analog_tr_$N.parquet --threads 4 > diag/analog_tr_$N.log 2>&1; echo "== $(date +%T) analog $N exit $? $(tail -1 diag/analog_tr_$N.log | cut -c1-80)"; }
ap v3p1 run_v3_p1:../p1_baseline/run1/p1_molecules.csv:A_timstof,B_nplib
ap v3eval run_v3_eval:eval_set/p1_molecules.csv:A_timstof,B_nplib
ap v3c1 run_v3_c1:eval_c1/p1_molecules.csv:B_nplib
S5=C_np_crosslib,D_np_single,E_np_negonly,F_np_uncovered,G_tims_crosslib
ap tpf3a run_tp_f3a:train_pool_f3a/p2_molecules.csv:$S5
ap tpf4a run_tp_f4a:train_pool_f4a/p2_molecules.csv:$S5
ap tpf3b run_tp_f3b:train_pool_f3b/p2_molecules.csv:$S5
ap tpf4b run_tp_f4b:train_pool_f4b/p2_molecules.csv:$S5
ap np061f3 run_np061_f3pool:np061_f3pool/p2_molecules.csv:NP_H,NP_X,NP_N
echo "ANALOG_TRAIN_DONE $(date +%T)"
