#!/bin/bash
# 042 v2 development (b1_gen v2, gen_eval2): dev2 v2 full_eval = main (identity unseen); panel full_eval = C1/C2 protection only (identity seen);
# panel fold-0 (fold-safe FPNet trained without the panel NPs) = auxiliary C3. Needs the fold-0 panel dump (b1_features --dump_gen, same args as run_panel_v3b).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
(cd $B && $PY -X utf8 gen_eval2.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_set2/v2/p2_molecules.csv --out diag/geneval2_p2dev --workers 12 > diag/geneval2_p2dev.log 2>&1; echo "== $(date +%T) p2dev exit $?") &
mkdir -p $B/run_panel_v3b_g
NUMBA_NUM_THREADS=1 $PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $B/run_panel_v3b_g --k 100 --workers 6 --k_fpp 200 --k_pop 50 \
  --dump_gen $B/run_panel_v3b_g/gen --sets P_np250 > $B/run_panel_v3b_g/features.log 2>&1
echo "== $(date +%T) panel fold-0 features exit $?"
$PY - <<'PY'
import pandas as pd
B = "experiments/b1_baseline"
a = pd.read_parquet(f"{B}/run_panel_v3b_g/b1_features_P_np250.parquet"); b = pd.read_parquet(f"{B}/run_panel_v3b/b1_features_P_np250.parquet")
cols = [c for c in b.columns if c in a.columns]
ka = a.sort_values(["molecule", "smiles"]).reset_index(drop=True)[cols]; kb = b.sort_values(["molecule", "smiles"]).reset_index(drop=True)[cols]
print(f"PARITY run_panel_v3b P_np250: rows {len(a)} vs {len(b)}, cols {len(cols)}/{len(b.columns)}/{len(a.columns)}, identical={ka.shape == kb.shape and ka.astype(str).equals(kb.astype(str))}")
PY
wait
(cd $B && $PY -X utf8 gen_eval2.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --views c1,c2 --out diag/geneval2_panel_fe --workers 8 > diag/geneval2_panel_fe.log 2>&1; echo "== $(date +%T) panel_fe exit $?") &
(cd $B && $PY -X utf8 gen_eval2.py --run run_panel_v3b --gen run_panel_v3b_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe data/external/fold_safe_fpnet --views c1,c2,c3,c3m,c3n --out diag/geneval2_panel_f0 --workers 8 > diag/geneval2_panel_f0.log 2>&1; echo "== $(date +%T) panel_f0 exit $?") &
wait
echo "GEN042V2_DEV_DONE $(date +%T)"
