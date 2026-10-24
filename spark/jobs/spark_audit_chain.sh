#!/bin/bash
# Shortlist-recall audit on the Spark: after the post-chain's first stage, rebuild the feature tables (with the truth's window ranks) for the
# development sets at low priority, then summarise the recall of hypothetical shortlist rules. GPU/CPU shared with the main chain (nice).
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
until grep -q "EVAL_FIX_DONE" logs/spark_post_chain.log 2>/dev/null; do sleep 120; done
git fetch -q origin && git checkout -q origin/main -- experiments/b1_baseline/b1_features.py experiments/b1_baseline/b1_shortlist_audit.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
F() {  # eval_csv run_dir sets...  (LIMIT array may hold --limit N)
  EVAL=$1; RUN=$2; shift 2; mkdir -p "$RUN/work"
  nice -n 10 .venv/bin/python -X utf8 experiments/b1_baseline/b1_features.py --eval_csv "$EVAL" --store data/processed/spectra_store --tier data/external/pubchem_tier \
    --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet \
    --v3 data/external/v3_models/code --out "$RUN" --k 100 --workers 8 --sets "$@" "${LIMIT[@]}" > "$RUN/features.log" 2>&1
  echo "== $(date +%T) features $RUN exit $? : $(grep -a '^saved\|^done\|Error' "$RUN/features.log" | tr '\n' ' ' | cut -c1-200)"
}
LIMIT=(--limit 3); F experiments/b1_baseline/eval_set/p1_molecules.csv experiments/b1_baseline/run_audit_smoke B_nplib
.venv/bin/python -c "import pandas as pd; M=pd.read_csv('experiments/b1_baseline/run_audit_smoke/b1_molecules_B_nplib.csv'); print(M[['molecule','truth_fp_rank','truth_pop_rank','truth_fppop_rank','truth_fppop50_rank','truth_lib_rank_c2','truth_in_short_c2']].to_string())" || { echo "AUDIT SMOKE FAILED $(date +%T)"; exit 1; }
LIMIT=()
F experiments/b1_baseline/eval_set/p1_molecules.csv experiments/b1_baseline/run_audit_v2 A_timstof B_nplib
F experiments/b1_baseline/eval_c1/p1_molecules.csv experiments/b1_baseline/run_audit_c1 B_nplib
.venv/bin/python -X utf8 experiments/b1_baseline/b1_shortlist_audit.py experiments/b1_baseline/run_audit_v2 experiments/b1_baseline/run_audit_c1:B_nplib
echo "AUDIT_DONE $(date +%T)"
