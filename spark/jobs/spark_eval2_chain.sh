#!/bin/bash
# Re-evaluate the development runs with the evaluator of 008_decision.md (partial runner outputs accepted, negative-evidence rules)
# once the post-chain's first stage is done; results go to results_008/ so the stage-1 results stay as they were.
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline
until grep -q "EVAL_FIX_DONE" logs/spark_post_chain.log 2>/dev/null; do sleep 120; done
git fetch -q origin && git checkout -q origin/main -- $B/b1_evaluate.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
.venv/bin/python -X utf8 $B/b1_evaluate.py --run $B/run1_v2 --eval_csv $B/eval_set/p1_molecules.csv --sets A_timstof B_nplib --out $B/run1_v2/results_008 > $B/run1_v2/evaluate_008.log 2>&1; echo "run1_v2 exit $?"
.venv/bin/python -X utf8 $B/b1_evaluate.py --run $B/run_c1_v2 --eval_csv $B/eval_c1/p1_molecules.csv --sets B_nplib --out $B/run_c1_v2/results_008 > $B/run_c1_v2/evaluate_008.log 2>&1; echo "run_c1_v2 exit $?"
grep -a "^## \|^| S(2,1,0.5) |\|negev\|libpri(tau=0.8,m=0.2)\|libpri(tau=0.9,m=0.2)" $B/run1_v2/results_008/b1_results.md $B/run_c1_v2/results_008/b1_results.md | cut -c1-240
echo "EVAL2_DONE $(date +%T)"
