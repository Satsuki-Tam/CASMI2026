#!/bin/bash
# After the panel chain: (1) re-evaluate the panel run with the forward-free prior rules S(0,0,λ) (results_prior/), (2) B1 vs public main list
# on the same molecules (where does B1 lose the truth), (3) print the key rows.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; RUN=$B/run_panel_v2
until grep -q "PANEL_DONE" logs/spark_panel_chain.log 2>/dev/null; do sleep 120; done
git fetch -q origin && git checkout -q origin/main -- $B/b1_evaluate.py $B/b1_vs_public_panel.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
$PY -X utf8 $B/b1_evaluate.py --run $RUN --eval_csv $B/panel_np250/p1_molecules.csv --sets P_np250 --out $RUN/results_prior > $RUN/evaluate_prior.log 2>&1; echo "evaluate (prior rules) exit $?"
echo "== fixed rules on the panel (strict = all 250; C2 = identity hidden; C1 = other-library references)"
grep -a "^## \|^| prior |\|^| fp |\|^| lib |\|^| S(0,0,0.15) |\|^| S(0,0,0.5) |\|^| S(0,0,1) |\|^| S(0,0,2) |\|^| S(0,0,4) |\|^| S(2,0,0.5) |\|^| S(2,0,1) |\|^| S(2,0,2) |\|^| S(2,1,0.5) |\|^| S(2,1,1) |\|^| S(2,1,2) |\|^| S(2,1,4) |\|libpri(tau=0.9,m=0.2)\|libpri(tau=0.8,m=0.2)\|^C1 diagnostics" $RUN/results_prior/b1_results.md | cut -c1-200
echo "== B1 vs public main list"
$PY -X utf8 $B/b1_vs_public_panel.py --panel_dir data/external/panel_benchmark --run $RUN --set P_np250 --out $RUN/results_prior/b1_vs_public.md 2>&1 | cut -c1-200
echo "PANEL_FOLLOWUP_DONE $(date +%T)"
