#!/bin/bash
# 042 generation study, step 1: rerun the registered full_eval feature tables (same arguments as spark_fulleval_chain.sh) with --dump_gen
# (query logits, neutral masses, window keys), then check that the tables are identical to the registered run_panel_fe / run_p2dev_fe.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FE=data/external/fpnet_fulleval_as_fold0
run_feats() {   # run_feats <eval_csv> <out_run> <sets...>
  local EVAL=$1 RUN=$2; shift 2
  mkdir -p $RUN
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FE --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features $RUN exit $? : $(grep -a '^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
}
run_feats $B/panel_np250/p1_molecules.csv $B/run_panel_fe_g P_np250
run_feats $B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_fe_g C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib
$PY - <<'PY'
import pandas as pd
B = "experiments/b1_baseline"
for new, old, sets in (("run_panel_fe_g", "run_panel_fe", ["P_np250"]), ("run_p2dev_fe_g", "run_p2dev_fe", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"])):
    for s in sets:
        a = pd.read_parquet(f"{B}/{new}/b1_features_{s}.parquet"); b = pd.read_parquet(f"{B}/{old}/b1_features_{s}.parquet")
        cols = [c for c in b.columns if c in a.columns]
        ka = a.sort_values(["molecule", "key"]).reset_index(drop=True)[cols]; kb = b.sort_values(["molecule", "key"]).reset_index(drop=True)[cols]
        same = ka.shape == kb.shape and ka.astype(str).equals(kb.astype(str))
        print(f"PARITY {s}: rows {len(a)} vs {len(b)}, identical={same}")
PY
echo "GEN042_FEATS_DONE $(date +%T)"
