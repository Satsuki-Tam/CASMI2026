#!/bin/bash
# 149 prep (Codex 147 S2 evaluation base on fold 3/4 identities that v8w7a never fitted: train_pool_f3b / f4b, np061_f3pool / f4pool):
# (1) generation dumps (b1_features --dump_gen, the original arguments, into run_*_g) for the three existing P runs; their tables are compared
#     with the existing ones (must be identical) and gen_eval2fd's f.z parity check ties the dumps to the existing tables + GL;
# (2) np061_f4pool had no P tables: full build (tables + dump_gen + GLACIER under gpu.lock) into run_np061_f4pool_p;
# (3) v8w7a main order top 25 per (set, view, molecule) (gen_eval2fd --dump_top, parents 0, views c1 / c2) -> diag/top149_<tag>.parquet.
# Nothing is evaluated; the ledgers / tops are not read here.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=2
B=experiments/b1_baseline; S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
feat() { csv=$1; fs=$2; out=$3; sets=$4
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $fs --v3 data/external/v3_models/code --out $out --k 100 --workers 5 --k_fpp 200 --k_pop 50 \
    --dump_gen $out/gen --sets $sets > $out/features.log 2>&1; }
cmpt() { old=$1; new=$2; sets=$3
  $PY -X utf8 -c "
import pandas as pd, numpy as np, sys
bad = 0
for s in '$sets'.split():
    a = pd.read_parquet('$old/b1_features_' + s + '.parquet'); b = pd.read_parquet('$new/b1_features_' + s + '.parquet')
    k = ['molecule', 'official_key']; a = a.sort_values(k + ['smiles']).reset_index(drop=True); b = b.sort_values(k + ['smiles']).reset_index(drop=True)
    same = len(a) == len(b) and (a[k + ['smiles']].values == b[k + ['smiles']].values).all() and np.allclose(a.fp.astype(float), b.fp.astype(float), equal_nan=True, atol=1e-4)
    print(s, len(a), len(b), 'identical' if same else 'DIFFERENT'); bad += not same
sys.exit(1 if bad else 0)"; }
dump() { tag=$1; run=$2; gen=$3; csv=$4; fs=$5; sets=$6
  $PY -X utf8 $B/gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --run $run --gen $gen --sets $sets --eval_csv $csv --fold_safe $fs --views c1,c2 \
    --dump_top diag/top149_$tag.parquet --out diag/t149_$tag --workers 3 > $B/diag/t149_$tag.log 2>&1; rc=$?; echo "== $(date +%T) top149 $tag rc=$rc $(grep -a 'parity max' $B/diag/t149_$tag.log | tr '\n' ' ' | cut -c1-200)"; return $rc; }
F3=data/external/fpnet_fold3_as_fold0; F4=data/external/fpnet_fold4_as_fold0
( mkdir -p $B/run_tp_f3b_g && feat $B/train_pool_f3b/p2_molecules.csv $F3 $B/run_tp_f3b_g "$S5" && cmpt $B/run_tp_f3b $B/run_tp_f3b_g "$S5" && dump f3b run_tp_f3b run_tp_f3b_g/gen train_pool_f3b/p2_molecules.csv $F3 "$S5" ) & A=$!
( mkdir -p $B/run_tp_f4b_g && feat $B/train_pool_f4b/p2_molecules.csv $F4 $B/run_tp_f4b_g "$S5" && cmpt $B/run_tp_f4b $B/run_tp_f4b_g "$S5" && dump f4b run_tp_f4b run_tp_f4b_g/gen train_pool_f4b/p2_molecules.csv $F4 "$S5" ) & Bp=$!
( mkdir -p $B/run_np061_f3pool_g && feat $B/np061_f3pool/p2_molecules.csv $F3 $B/run_np061_f3pool_g "$S3" && cmpt $B/run_np061_f3pool $B/run_np061_f3pool_g "$S3" && dump np061f3 run_np061_f3pool run_np061_f3pool_g/gen np061_f3pool/p2_molecules.csv $F3 "$S3" ) & C=$!
( R=$B/run_np061_f4pool_p; mkdir -p $R/work && feat $B/np061_f4pool/p2_molecules.csv $F4 $R "$S3" && for S in $S3; do
    flock spark/gpu.lock nice -n 10 .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $R/b1_runner_${S}_in.json $R/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $R/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) np061_f4pool gl $S $(grep -a '\[resume\] done' $R/work/gl_${S}_resume.log | cut -c1-90)"; done && dump np061f4 run_np061_f4pool_p run_np061_f4pool_p/gen np061_f4pool/p2_molecules.csv $F4 "$S3" ) & D=$!
FAIL=0; for p in $A $Bp $C $D; do wait $p || FAIL=1; done
[ $FAIL = 0 ] && echo "S2_PINFRA_DONE $(date '+%F %T')" || { echo "S2_PINFRA_FAIL $(date '+%F %T')"; exit 1; }
