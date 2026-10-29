#!/bin/bash
# 133 v2: molecule-level MIST query flags (mist_qflags.py, no MIST forward pass) for every tag of experiments/mist/scores_v4 (consistency-checked
# against the candidate tables) and, when present, scores_v4_conf.
set -u
cd ~/CASMI2026 || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=2 PYTHONUTF8=1
PY=.venv-mist/bin/python; B=experiments/b1_baseline
sets_of() { .venv/bin/python -c "import glob, os, sys, pandas as pd; r, c = sys.argv[1], sys.argv[2]; s = set(pd.read_csv(c).set.astype(str)) & {os.path.basename(f)[12:-8] for f in glob.glob(r + '/b1_features_*.parquet')}; print(' '.join(sorted(s)))" $1 $2; }
qf() { local O=$1 T=$2 RUN=$3 CSV=$4; $PY -X utf8 experiments/mist/mist_qflags.py --store data/processed/spectra_store --eval_csv $CSV --tag $T --sets $(sets_of $RUN $CSV) --out $O || { echo "QFLAGS_FAIL $T"; exit 1; }; }
O=experiments/mist/scores_v4
qf $O tr_v3p1 $B/run_v3_p1 experiments/p1_baseline/run1/p1_molecules.csv; qf $O tr_v3eval $B/run_v3_eval $B/eval_set/p1_molecules.csv; qf $O tr_v3c1 $B/run_v3_c1 $B/eval_c1/p1_molecules.csv
qf $O tr_f3a $B/run_tp_f3a $B/train_pool_f3a/p2_molecules.csv; qf $O tr_f4a $B/run_tp_f4a $B/train_pool_f4a/p2_molecules.csv; qf $O panel $B/run_panel_fe $B/panel_np250/p1_molecules.csv
qf $O f1dev $B/run_f1dev $B/eval_set_f1/p2_molecules.csv; qf $O np053f1dev $B/run_np053_f1dev $B/np053_f1dev/p2_molecules.csv; qf $O c1bankdev $B/run_c1bankdev_f1 $B/c1bank_f1/c1dev/p2_molecules.csv
qf $O f2dev $B/run_f2dev $B/eval_set_f2/p2_molecules.csv; qf $O np053f2dev $B/run_np053_f2dev $B/np053_f2dev/p2_molecules.csv
echo "QFLAGS_DONE $(date '+%F %T')"
