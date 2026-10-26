#!/bin/bash
# 042 confirmation (pre-registered in reports/agent_review/042_prereg_gen.md): rerun the fold-0 confirmation tables with --dump_gen,
# check table identity, then gen_eval (main = M2x + anaw0.5) on conf3 / conffit / conffit2.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FS=data/external/fold_safe_fpnet
feats() {   # feats <eval_csv> <out_run> <workers> <sets...>
  local EVAL=$1 RUN=$2 W=$3; shift 3; mkdir -p $RUN
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers $W --k_fpp 200 --k_pop 50 \
    --dump_gen $RUN/gen --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features $RUN exit $?"
}
feats $B/eval_set3/p2_molecules.csv $B/run_conf3_m2x_g 10 D_np_single
feats $B/eval_conf_fit/p2_molecules.csv $B/run_conffit_m2x_g 10 C_np_crosslib E_np_negonly F_np_uncovered G_tims_crosslib
feats $B/eval_conf_fit2/p2_molecules.csv $B/run_conffit2_m2x_g 10 D_np_single E_np_negonly
$PY - <<'PY'
import pandas as pd
B = "experiments/b1_baseline"
for new, old, sets in (("run_conf3_m2x_g", "run_conf3_m2x", ["D_np_single"]), ("run_conffit_m2x_g", "run_conffit_m2x", ["C_np_crosslib", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
                       ("run_conffit2_m2x_g", "run_conffit2_m2x", ["D_np_single", "E_np_negonly"])):
    for s in sets:
        a = pd.read_parquet(f"{B}/{new}/b1_features_{s}.parquet"); b = pd.read_parquet(f"{B}/{old}/b1_features_{s}.parquet")
        cols = [c for c in b.columns if c in a.columns]
        ka = a.sort_values(["molecule", "smiles"]).reset_index(drop=True)[cols]; kb = b.sort_values(["molecule", "smiles"]).reset_index(drop=True)[cols]
        print(f"PARITY {old} {s}: rows {len(a)} vs {len(b)}, identical={ka.shape == kb.shape and ka.astype(str).equals(kb.astype(str))}")
PY
cd $B
$PY -X utf8 gen_eval.py --run run_conf3_m2x --gen run_conf3_m2x_g/gen --sets D_np_single --eval_csv eval_set3/p2_molecules.csv --fold_safe $FS --out diag/geneval_conf3 --workers 12 > diag/geneval_conf3.log 2>&1; echo "== conf3 exit $?"
$PY -X utf8 gen_eval.py --run run_conffit_m2x --gen run_conffit_m2x_g/gen --sets C_np_crosslib E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_conf_fit/p2_molecules.csv --fold_safe $FS --out diag/geneval_conffit --workers 12 > diag/geneval_conffit.log 2>&1; echo "== conffit exit $?"
$PY -X utf8 gen_eval.py --run run_conffit2_m2x --gen run_conffit2_m2x_g/gen --sets D_np_single E_np_negonly --eval_csv eval_conf_fit2/p2_molecules.csv --fold_safe $FS --out diag/geneval_conffit2 --workers 12 > diag/geneval_conffit2.log 2>&1; echo "== conffit2 exit $?"
echo "GEN042_CONF_DONE $(date +%T)"
