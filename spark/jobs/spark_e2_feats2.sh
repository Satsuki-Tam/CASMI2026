#!/bin/bash
# 143 E2 step 2, re-split (10:2x): the first job's shell was stopped after train_pool_f3a / f4a; its running e2_feats.py for train_pool_f3b and
# train_pool_f4b continue on their own (orphaned) and write e2f_manifest.json when done. Four streams: A = f3b (wait) -> np061_f3pool,
# B = f4b (wait) -> np061_f4pool, C = np053_f1dev -> eval_set_f1 -> panel_np250, D = np053_f2dev -> eval_set_f2.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=2
B=experiments/b1_baseline; O=experiments/e2/ewin
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
waitf() { until [ -f $O/$1/e2f_manifest.json ]; do pgrep -f "e2_feats.py --ewin $O/$1 " > /dev/null || { sleep 5; [ -f $O/$1/e2f_manifest.json ] && break; echo "== $(date +%T) $1: feature run gone without manifest"; return 1; }; sleep 30; done; echo "== $(date +%T) feats $1 done (first job)"; }
one() { d=$1; csv=$2; sets=$3
  until [ -f $O/$d/ewin_manifest.json ]; do grep -q E2_EWIN_FAIL logs/spark_e2_ewin.log 2>/dev/null && { echo "== $(date +%T) $d: E-window job failed"; return 1; }; sleep 30; done
  $PY -X utf8 experiments/e2/e2_feats.py --ewin $O/$d --eval_csv $B/$d/$csv --sets $sets --workers 5 > $O/$d.feats.log 2>&1; rc=$?
  echo "== $(date +%T) feats $d rc=$rc"; return $rc; }
( waitf train_pool_f3b && one np061_f3pool p2_molecules.csv "$S3" ) & A=$!
( waitf train_pool_f4b && one np061_f4pool p2_molecules.csv "$S3" ) & Bp=$!
( one np053_f1dev p2_molecules.csv "$S3" && one eval_set_f1 p2_molecules.csv "$S5" && one panel_np250 p1_molecules.csv P_np250 ) & C=$!
( one np053_f2dev p2_molecules.csv "$S3" && one eval_set_f2 p2_molecules.csv "$S5" ) & D=$!
FAIL=0; for p in $A $Bp $C $D; do wait $p || FAIL=1; done
[ $FAIL = 0 ] && echo "E2_FEATS_DONE $(date '+%F %T')" || { echo "E2_FEATS_FAIL $(date '+%F %T')"; exit 1; }
