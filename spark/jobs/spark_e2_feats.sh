#!/bin/bash
# 143 E2 step 2: experiments/e2/e2_feats.py (MetFrag-lite + analog features per view) for every E-window dir as soon as its table is
# complete (ewin_manifest.json written by b1_ewin.py at the end). Training dirs first, then the development dirs. Two streams.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=2
B=experiments/b1_baseline; O=experiments/e2/ewin
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
one() { d=$1; csv=$2; sets=$3
  until [ -f $O/$d/ewin_manifest.json ]; do grep -q E2_EWIN_FAIL logs/spark_e2_ewin.log 2>/dev/null && { echo "== $(date +%T) $d: E-window job failed"; return 1; }; sleep 30; done
  $PY -X utf8 experiments/e2/e2_feats.py --ewin $O/$d --eval_csv $B/$d/$csv --sets $sets --workers 6 > $O/$d.feats.log 2>&1; rc=$?
  echo "== $(date +%T) feats $d rc=$rc"; return $rc; }
( one train_pool_f3a p2_molecules.csv "$S5" && one train_pool_f3b p2_molecules.csv "$S5" && one np061_f3pool p2_molecules.csv "$S3" && one np053_f1dev p2_molecules.csv "$S3" && one eval_set_f1 p2_molecules.csv "$S5" ) & A=$!
( one train_pool_f4a p2_molecules.csv "$S5" && one train_pool_f4b p2_molecules.csv "$S5" && one np061_f4pool p2_molecules.csv "$S3" && one np053_f2dev p2_molecules.csv "$S3" && one eval_set_f2 p2_molecules.csv "$S5" && one panel_np250 p1_molecules.csv P_np250 ) & Bp=$!
FAIL=0; wait $A || FAIL=1; wait $Bp || FAIL=1
[ $FAIL = 0 ] && echo "E2_FEATS_DONE $(date '+%F %T')" || { echo "E2_FEATS_FAIL $(date '+%F %T')"; exit 1; }
