#!/bin/bash
# Faithful M1 panel check (Codex 012 §1): the v2 shortlist (K=100, no prior branch) on the 250-molecule panel with the corrected evaluator.
# GL/ICE are seeded from run_panel_v2 (the v3 shortlist is a superset, so only molecules with new candidates are re-scored). Runs with
# WORKERS=6 beside the v3b chain, after the proxy runs. Then probes of rank_v2 (M1, w_ice 1) and rank_v4g on this run, and the public comparison.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "PANEL_PROXY_RUNS_DONE" logs/spark_panel_proxy_chain.log 2>/dev/null; do sleep 60; done
WORKERS=6 OLD_RUN=$B/run_panel_v2 FEAT_ARGS="--k_fpp 100 --k_pop 0" RUNNERS="gl ice" bash spark/jobs/b1_features_job_v3b.sh $B/panel_np250/p1_molecules.csv $B/run_panel_v2k P_np250
export OMP_NUM_THREADS=4
for M in "rank_v2 1" "rank_v4g 1"; do set -- $M
  echo "-- probe panel_v2k $1 (w_ice $2)"; $PY -X utf8 $B/b1_learned_probe.py --run $B/run_panel_v2k --set P_np250 --model $B/$1/lambdarank.txt --w_ice $2 --views c1 c2 --guards 0.9:0.2 --out $B/diag/probe_panel_v2k_$1.md 2>&1 | grep -a "^## view\|^| learned \|^| pipeline \|^| fixed \|^| lib \|^| blend\|^| switch\|^learned loses" | cut -c1-160
done
$PY -X utf8 $B/b1_vs_public_panel.py --panel_dir data/external/panel_benchmark --run $B/run_panel_v2k --set P_np250 --out $B/run_panel_v2k/results/b1_vs_public.md 2>&1 | grep -a "^## \|^| public\|^| B1\|^paired" | cut -c1-160
echo "PANEL_M1_DONE $(date +%T)"
