#!/bin/bash
# 149 prep (replaces streams A / B of spark_s2_pinfra.sh, stopped at 12:28 before they overwrote anything except features.log): the generation
# dumps of run_tp_f3b_g / run_tp_f4b_g already exist (built 10/27 with the same b1_features arguments). Compare their tables with run_tp_f3b /
# run_tp_f4b (must be identical), then v8w7a top-25 dumps with --run = the original runs (tables + GL) and --gen = the existing dumps
# (gen_eval2fd's f.z parity check ties them). Nothing is evaluated.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=2
B=experiments/b1_baseline; S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; F3=data/external/fpnet_fold3_as_fold0; F4=data/external/fpnet_fold4_as_fold0
cmpt() { $PY -X utf8 -c "
import pandas as pd, numpy as np, sys
bad = 0
for s in '$S5'.split():
    a = pd.read_parquet('$1/b1_features_' + s + '.parquet'); b = pd.read_parquet('$2/b1_features_' + s + '.parquet')
    k = ['molecule', 'official_key']; a = a.sort_values(k + ['smiles']).reset_index(drop=True); b = b.sort_values(k + ['smiles']).reset_index(drop=True)
    same = len(a) == len(b) and (a[k + ['smiles']].values == b[k + ['smiles']].values).all() and np.allclose(a.fp.astype(float), b.fp.astype(float), equal_nan=True, atol=1e-4)
    print(s, len(a), len(b), 'identical' if same else 'DIFFERENT'); bad += not same
sys.exit(1 if bad else 0)"; }
dump() { tag=$1; run=$2; gen=$3; csv=$4; fs=$5
  $PY -X utf8 $B/gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --run $run --gen $gen --sets $S5 --eval_csv $csv --fold_safe $fs --views c1,c2 \
    --dump_top diag/top149_$tag.parquet --out diag/t149_$tag --workers 3 > $B/diag/t149_$tag.log 2>&1; rc=$?; echo "== $(date +%T) top149 $tag rc=$rc $(grep -a 'parity max' $B/diag/t149_$tag.log | tr '\n' ' ' | cut -c1-200)"; return $rc; }
( cmpt $B/run_tp_f3b $B/run_tp_f3b_g && dump f3b run_tp_f3b run_tp_f3b_g/gen train_pool_f3b/p2_molecules.csv $F3 ) & A=$!
( cmpt $B/run_tp_f4b $B/run_tp_f4b_g && dump f4b run_tp_f4b run_tp_f4b_g/gen train_pool_f4b/p2_molecules.csv $F4 ) & Bp=$!
FAIL=0; wait $A || FAIL=1; wait $Bp || FAIL=1
[ $FAIL = 0 ] && echo "S2_DUMP34B_DONE $(date '+%F %T')" || { echo "S2_DUMP34B_FAIL $(date '+%F %T')"; exit 1; }
