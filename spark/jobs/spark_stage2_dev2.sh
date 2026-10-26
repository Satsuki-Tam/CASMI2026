#!/bin/bash
# 044 (after Codex 044): re-evaluate the stage-2 development tables with the fixed gen_eval3 (per-view top-K ledger, finiteness, scale validity,
# explicit ggt3 fallback). GL caches from pass 1 are reused (no GPU). main and gt3 must equal the previous tables.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0; FE=data/external/fpnet_fulleval_as_fold0
DEV2="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
mkdir -p diag/stage2_v1_buggy && mv diag/stage2_p2dev.* diag/stage2_f1dev.* diag/stage2_panel.* diag/stage2_v1_buggy/ 2>/dev/null
$PY -X utf8 gen_eval3.py --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --gl_gen glgen_p2dev/gl_gen --out diag/stage2_p2dev --workers 8 > diag/stage2_p2dev.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen_f1dev/gl_gen --out diag/stage2_f1dev --workers 8 > diag/stage2_f1dev.log 2>&1 &
wait
$PY -X utf8 gen_eval3.py --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --gl_gen glgen_panel/gl_gen --out diag/stage2_panel --workers 16 > diag/stage2_panel.log 2>&1
$PY - <<'PY'
import pandas as pd
for n in ("p2dev", "f1dev", "panel"):
    a = pd.read_csv(f"diag/stage2_{n}.csv"); b = pd.read_csv(f"diag/stage2_v1_buggy/stage2_{n}.csv")
    k = ["set", "view", "molecule"]; m = a.merge(b, on=k, suffixes=("", "_old"))
    print(n, "rows", len(a), len(b), "main identical", bool((m.main - m.main_old).abs().max() < 1e-12), "gt3 identical", bool((m.gt3 - m.gt3_old).abs().max() < 1e-12),
          "rows with n_gen_gl > 5 now", int((a.get("n_gen_gl", pd.Series(0)) > 5).sum()))
PY
echo "STAGE2_DEV2_DONE $(date +%T)"
