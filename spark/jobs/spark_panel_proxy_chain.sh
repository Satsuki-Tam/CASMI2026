#!/bin/bash
# Forward-model adduct proxies on the panel (2026-10-25): the 34/250 panel molecules without a covered positive spectrum ([M+H]+/[M+Na]+)
# get no GLACIER/ICEBERG evidence. (1) run_panel_proxy: --adduct_proxy ([M+NH4]+ / [M-H2O+H]+ scored as [M+H]+, public N1A arm A recipe);
# (2) run_panel_proxy_neg: + --neg_proxy (negative-mode spectra mapped onto the positive axis; experimental). Forward scores are seeded from
# run_panel_v2 (same v3 shortlist; only molecules whose runner spectra / candidates changed are re-scored). Features run with WORKERS=6 so the
# v3b chain (16 workers) keeps the CPU. The comparison waits for the corrected base table run_panel_v3b (V3B_PANEL_DONE).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; J=spark/jobs/b1_features_job_v3b.sh; EV=$B/panel_np250/p1_molecules.csv
echo "== $(date +%T) proxies (nh4 / h2o)"
WORKERS=6 OLD_RUN=$B/run_panel_v2 FEAT_ARGS="--k_fpp 200 --k_pop 50 --adduct_proxy" RUNNERS="gl ice" bash $J $EV $B/run_panel_proxy P_np250
echo "== $(date +%T) proxies + negative-mode (experimental)"
WORKERS=6 OLD_RUN=$B/run_panel_v2 FEAT_ARGS="--k_fpp 200 --k_pop 50 --adduct_proxy --neg_proxy" RUNNERS="gl ice" bash $J $EV $B/run_panel_proxy_neg P_np250
echo "PANEL_PROXY_RUNS_DONE $(date +%T)"
until grep -q "V3B_PANEL_DONE" logs/spark_v3b_chain.log 2>/dev/null; do sleep 120; done
export OMP_NUM_THREADS=4
$PY -X utf8 $B/b1_proxy_compare.py --base $B/run_panel_v3b --runs nh4h2o:$B/run_panel_proxy neg:$B/run_panel_proxy_neg --set P_np250 --models rank_v4b:0 rank_v3:0 --out $B/diag/proxy_panel.md 2>&1 | grep -v "^|---" | cut -c1-260
echo "PANEL_PROXY_DONE $(date +%T)"
