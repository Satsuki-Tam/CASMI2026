#!/bin/bash
# 042b confirmation (pre-registered in reports/agent_review/042b_prereg_gen_v2.md, rule gk3 + dv1): gen_eval2 v2 on the fold-0 confirmation runs
# (dumps from spark_gen042_conf.sh, tables identical to the registered runs). Waits for the v2 development job.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
until grep -q "GEN042V2_DEV_DONE" logs/spark_gen042v2_dev.log 2>/dev/null; do sleep 30; done
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; FS=data/external/fold_safe_fpnet
cd $B
echo "== $(date +%T) b1_gen $(sha256sum b1_gen.py | cut -c1-12) gen_eval2 $(sha256sum gen_eval2.py | cut -c1-12)"
$PY -X utf8 gen_eval2.py --run run_conf3_m2x --gen run_conf3_m2x_g/gen --sets D_np_single --eval_csv eval_set3/p2_molecules.csv --fold_safe $FS --out diag/geneval2_conf3 --workers 12 > diag/geneval2_conf3.log 2>&1 &
$PY -X utf8 gen_eval2.py --run run_conffit_m2x --gen run_conffit_m2x_g/gen --sets C_np_crosslib E_np_negonly F_np_uncovered G_tims_crosslib --eval_csv eval_conf_fit/p2_molecules.csv --fold_safe $FS --out diag/geneval2_conffit --workers 12 > diag/geneval2_conffit.log 2>&1 &
wait
$PY -X utf8 gen_eval2.py --run run_conffit2_m2x --gen run_conffit2_m2x_g/gen --sets D_np_single E_np_negonly --eval_csv eval_conf_fit2/p2_molecules.csv --fold_safe $FS --out diag/geneval2_conffit2 --workers 16 > diag/geneval2_conffit2.log 2>&1
echo "== $(date +%T) exits: $(grep -c Traceback diag/geneval2_conf3.log diag/geneval2_conffit.log diag/geneval2_conffit2.log | tr '\n' ' ')"
echo "GEN042V2_CONF_DONE $(date +%T)"
