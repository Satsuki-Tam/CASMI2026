#!/bin/bash
# 149 prep (Codex 147 S2 (i)): MIST v4 per-candidate scores of the E-window tables of the six fold 3/4 pool dirs (training + evaluation of
# the C / M cross-fit), through the audited experiments/mist/mist_score_v4.py unchanged (E tables exposed by e2_mist_inputs.py).
# CPU only (4 threads per table, two tables at a time, nice 10). No performance number is computed here.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; PM=$HOME/CASMI2026/.venv-mist/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=4
B=experiments/b1_baseline; CK=data/external/mist/zenodo_23303289/mist_msg_aug.ckpt; S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
one() { d=$1; sets=$2; I=experiments/e2/mist_in/$d; O=experiments/e2/mist_out/$d
  $PY -X utf8 experiments/e2/e2_mist_inputs.py --ewin experiments/e2/ewin/$d --eval_csv $B/$d/p2_molecules.csv --sets $sets --out $I > $I.log 2>&1 || { echo "== $(date +%T) $d inputs FAIL"; return 1; }
  nice -n 10 $PM -X utf8 experiments/mist/mist_score_v4.py --ckpt $CK --store data/processed/spectra_store --run $I --eval_csv $B/$d/p2_molecules.csv --tag e2 --sets $sets --out $O --threads 4 > $O.log 2>&1; rc=$?
  echo "== $(date +%T) $d mist rc=$rc $(grep -a -E '^(C_|D_|E_|F_|G_|NP_)' $O.log | cut -c1-120 | tr '\n' ' ')"; return $rc; }
mkdir -p experiments/e2/mist_in experiments/e2/mist_out
( one train_pool_f3a "$S5" && one train_pool_f3b "$S5" && one np061_f3pool "$S3" ) & A=$!
( one train_pool_f4a "$S5" && one train_pool_f4b "$S5" && one np061_f4pool "$S3" ) & Bp=$!
FAIL=0; wait $A || FAIL=1; wait $Bp || FAIL=1
[ $FAIL = 0 ] && echo "S2_MIST_DONE $(date '+%F %T')" || { echo "S2_MIST_FAIL $(date '+%F %T')"; exit 1; }
