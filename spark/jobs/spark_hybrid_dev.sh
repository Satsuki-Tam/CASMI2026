#!/bin/bash
# 046 development (pre-registered in 046_prereg_hybrid.md): gen_eval5 pass 2 (GL caches of stage 3 reused: same parents, same top-5) on dev2 v2,
# fold-1 dev and the panel; consistency: gen_eval5 gt3 == stage-2 gt3, gen_eval5 ggt3 == stage-3 ggt3 (ggt3b) per molecule.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0; FE=data/external/fpnet_fulleval_as_fold0
DEV2="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
$PY -X utf8 gen_eval5.py --db_parents 10 --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $DEV2 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE --views c1,c2,c3 --gl_gen glgen4_p2dev/gl_gen --out diag/hybrid_p2dev --workers 9 > diag/hybrid_p2dev.log 2>&1 &
$PY -X utf8 gen_eval5.py --db_parents 10 --run run_f1dev --gen run_f1dev/gen --sets $DEV2 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen4_f1dev/gl_gen --out diag/hybrid_f1dev --workers 9 > diag/hybrid_f1dev.log 2>&1 &
wait
$PY -X utf8 gen_eval5.py --db_parents 10 --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --gl_gen glgen4_panel/gl_gen --out diag/hybrid_panel --workers 18 > diag/hybrid_panel.log 2>&1
$PY - <<'PY'
import pandas as pd
k = ["set", "view", "molecule"]
for n in ("p2dev", "f1dev", "panel"):
    h = pd.read_csv(f"diag/hybrid_{n}.csv"); s2 = pd.read_csv(f"diag/stage2_{n}.csv"); s3 = pd.read_csv(f"diag/stage3_{n}.csv")
    m2 = h.merge(s2, on=k, suffixes=("", "_s2")); m3 = h.merge(s3, on=k, suffixes=("", "_s3"))
    print(n, "rows", len(h), "| main==stage2 main", bool((m2.main - m2.main_s2).abs().max() < 1e-12), "| gt3(analog-only)==stage2 gt3", bool((m2.gt3 - m2.gt3_s2).abs().max() < 1e-12),
          "n diff", int(((m2.gt3 - m2.gt3_s2).abs() > 1e-12).sum()), "| ggt3==stage3 ggt3", bool((m3.ggt3 - m3.ggt3_s3).abs().max() < 1e-12), "n diff", int(((m3.ggt3 - m3.ggt3_s3).abs() > 1e-12).sum()))
PY
echo "HYBRID_DEV_DONE $(date +%T)"
