#!/bin/bash
# 043 (pre-registered): W7 fold-0 tables re-generated with --dump_gen (same args as run_v3b_eval), identity check, then gen_eval2 (gt3 is the registered rule).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; FS=data/external/fold_safe_fpnet
mkdir -p $B/run_v3b_eval_g
$PY -X utf8 $B/b1_features.py --eval_csv $B/eval_set/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $B/run_v3b_eval_g --k 100 --workers 10 --k_fpp 200 --k_pop 50 \
  --dump_gen $B/run_v3b_eval_g/gen --sets A_timstof B_nplib > $B/run_v3b_eval_g/features.log 2>&1
echo "== $(date +%T) W7 features exit $?"
$PY - <<'PY'
import pandas as pd
B = "experiments/b1_baseline"
for s in ("A_timstof", "B_nplib"):
    a = pd.read_parquet(f"{B}/run_v3b_eval_g/b1_features_{s}.parquet"); b = pd.read_parquet(f"{B}/run_v3b_eval/b1_features_{s}.parquet")
    cols = [c for c in b.columns if c in a.columns]
    ka = a.sort_values(["molecule", "smiles"]).reset_index(drop=True)[cols]; kb = b.sort_values(["molecule", "smiles"]).reset_index(drop=True)[cols]
    print(f"PARITY run_v3b_eval {s}: rows {len(a)} vs {len(b)}, cols {len(cols)}/{len(b.columns)}/{len(a.columns)}, identical={ka.shape == kb.shape and ka.astype(str).equals(kb.astype(str))}")
PY
cd $B
NUMBA_NUM_THREADS=8 $PY -X utf8 gen_eval2.py --run run_v3b_eval --gen run_v3b_eval_g/gen --sets A_timstof B_nplib --eval_csv eval_set/p1_molecules.csv --fold_safe $FS --views c1,c2,c3 --out diag/geneval2_w7 --workers 16 > diag/geneval2_w7.log 2>&1
echo "== $(date +%T) gen_eval2 W7 exit $?"
echo "GEN043_W7_DONE $(date +%T)"
