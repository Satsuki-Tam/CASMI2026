#!/bin/bash
# Forward-model adduct proxies on the panel (2026-10-25): the 34/250 panel molecules without a covered positive spectrum ([M+H]+/[M+Na]+)
# get no GLACIER/ICEBERG evidence. (1) run_panel_proxy: --adduct_proxy ([M+NH4]+ / [M-H2O+H]+ scored as [M+H]+, public N1A arm A recipe);
# (2) run_panel_proxy_neg: + --neg_proxy (negative-mode spectra mapped onto the positive axis; experimental). Forward scores are seeded from
# run_panel_v3b, so only the molecules whose runner spectra changed (the uncovered ones) are re-scored. Then the fixed rules and the probe
# on the affected molecules only (b1_proxy_compare.py). Waits for PANEL_M1_DONE (CPU/GPU contention).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; J=spark/jobs/b1_features_job_v3b.sh; EV=$B/panel_np250/p1_molecules.csv
until grep -q "PANEL_M1_DONE" logs/spark_panel_m1_chain.log 2>/dev/null; do sleep 120; done
echo "== $(date +%T) proxies (nh4 / h2o)"
OLD_RUN=$B/run_panel_v3b FEAT_ARGS="--k_fpp 200 --k_pop 50 --adduct_proxy" RUNNERS="gl ice" bash $J $EV $B/run_panel_proxy P_np250
echo "== $(date +%T) proxies + negative-mode (experimental)"
OLD_RUN=$B/run_panel_v3b FEAT_ARGS="--k_fpp 200 --k_pop 50 --adduct_proxy --neg_proxy" RUNNERS="gl ice" bash $J $EV $B/run_panel_proxy_neg P_np250
export OMP_NUM_THREADS=4
$PY -X utf8 $B/b1_proxy_compare.py --base $B/run_panel_v3b --runs nh4h2o:$B/run_panel_proxy neg:$B/run_panel_proxy_neg --set P_np250 --models rank_v4b:0 rank_v3:0 --out $B/diag/proxy_panel.md 2>&1 | grep -v "^|---" | cut -c1-200
echo "PANEL_PROXY_DONE $(date +%T)"
