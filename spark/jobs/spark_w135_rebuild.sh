#!/bin/bash
# W135 rebuild after the Codex 136 C1 audit (corrected class CSVs; b1_world / w135_p v2): (1) parity re-checks of the v2 code (tables on the
# NP_H 12-molecule roster, P on NP_H / NP_X), (2) the six design worlds at pi3 = 0.3, (3) the same at pi3 = 0 / 0.6 (descriptive). Two streams;
# GL serialised by gpu.lock; every child's exit value is collected (a failed world stops the stream and the job reports FAIL). No reach number.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1
fail() { echo "W135_REBUILD_FAIL $* $(date '+%F %T')"; exit 1; }
B=experiments/b1_baseline; P2=experiments/w135/parity_v2; mkdir -p $P2
$PY -X utf8 experiments/w135/b1_world.py --parity_c2 --eval_csv $B/np053_f1dev/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fpnet_fold1_as_fold0 --v3 data/external/v3_models/code --folds data/external/identity_folds/structures.parquet \
  --out $P2/np053f1_NPH12 --k 100 --workers 8 --k_fpp 200 --k_pop 50 --sets NP_H --limit 12 > $P2/np053f1_NPH12.log 2>&1 || fail "parity tables run"
$PY -X utf8 experiments/w135/w135_parity_tables.py --ref $B/run_np053_f1dev/b1_features_NP_H.parquet --new $P2/np053f1_NPH12/b1_features_NP_H.parquet --eval_csv $B/np053_f1dev/p2_molecules.csv --set NP_H --limit 12 > $P2/tables.log 2>&1 || fail "parity tables"
for s in NP_H NP_X; do ( cd $B && OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=8 $PY -X utf8 ../w135/w135_p.py --parity_c2 --run run_np053_f1dev --gl run_np053_f1dev/work/gl_$s.json --sets $s --eval_csv np053_f1dev/p2_molecules.csv \
  --model rank_v8w7a/lambdarank.txt --out ../w135/parity_v2/p_np053f1_$s --ref_csv diag/r133_P_np053f1dev.csv ) > $P2/p_$s.log 2>&1 || fail "parity P $s"; done
echo "== $(date '+%F %T') parity v2: $(grep -h 'PARITY' $P2/tables.log $P2/p_NP_H.log $P2/p_NP_X.log | cut -c1-90 | tr '\n' ' ')"
stream() { for spec in "$@"; do b=${spec%:*}; p=${spec#*:}; bash spark/jobs/spark_w135_world.sh $b $p > logs/w135v2_${b}_p$p.log 2>&1 || return 1; done; }
stream dF1:30 dF2:30 dF3:30 & S1=$!; stream dR1:30 dR2:30 dR3:30 & S2=$!
wait $S1 || fail "p30 stream 1"; wait $S2 || fail "p30 stream 2"
echo "W135_P30_V2_DONE $(date '+%F %T')"
stream dF1:0 dF1:60 dF2:0 dF2:60 dF3:0 dF3:60 & S1=$!; stream dR1:0 dR1:60 dR2:0 dR2:60 dR3:0 dR3:60 & S2=$!
wait $S1 || fail "p0/p60 stream 1"; wait $S2 || fail "p0/p60 stream 2"
echo "W135_REBUILD_DONE $(date '+%F %T')"
