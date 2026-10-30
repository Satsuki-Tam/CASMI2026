#!/bin/bash
# 143 E2: E-window tables (experiments/e2/b1_ewin.py) for the E2 training molecules (fold 3 / 4 pools, fold-safe FPNet of their fold) and the
# development tables (fold 1 / 2 with their fold-safe FPNet, panel with full_eval). Three streams; exit values collected.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1; B=experiments/b1_baseline; O=experiments/e2/ewin; mkdir -p $O
one() { $PY -X utf8 experiments/e2/b1_ewin.py --eval_csv $B/$1/$3 --sets $4 --fold_safe $2 --out $O/$1 --workers 6 > $O/$1.log 2>&1; rc=$?; echo "== $(date +%T) $1 rc=$rc $(grep -a '^saved' $O/$1.log | tr '\n' ' ' | cut -c1-200)"; return $rc; }
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
F1=data/external/fpnet_fold1_as_fold0; F2=data/external/fpnet_fold2_as_fold0; F3=data/external/fpnet_fold3_as_fold0; F4=data/external/fpnet_fold4_as_fold0; FE=data/external/fpnet_fulleval_as_fold0
( one train_pool_f3a $F3 p2_molecules.csv "$S5" && one train_pool_f3b $F3 p2_molecules.csv "$S5" && one np061_f3pool $F3 p2_molecules.csv "$S3" ) & A=$!
( one train_pool_f4a $F4 p2_molecules.csv "$S5" && one train_pool_f4b $F4 p2_molecules.csv "$S5" && one np061_f4pool $F4 p2_molecules.csv "$S3" ) & Bp=$!
( one np053_f1dev $F1 p2_molecules.csv "$S3" && one eval_set_f1 $F1 p2_molecules.csv "$S5" && one np053_f2dev $F2 p2_molecules.csv "$S3" && one eval_set_f2 $F2 p2_molecules.csv "$S5" && one panel_np250 $FE p1_molecules.csv "P_np250" ) & C=$!
FAIL=0; wait $A || FAIL=1; wait $Bp || FAIL=1; wait $C || FAIL=1
[ $FAIL = 0 ] && echo "E2_EWIN_DONE $(date '+%F %T')" || { echo "E2_EWIN_FAIL $(date '+%F %T')"; exit 1; }
