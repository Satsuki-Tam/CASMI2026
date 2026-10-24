#!/bin/bash
# Codex 013 step 2: the frozen control M1 on the CORRECTED reference condition, and the direct comparison with the candidate M2x on a common
# ledger. (1) run1b_v2 / run_c1b_v2 = v2 shortlist (K=100, no prior branch) feature tables of eval_set / eval_c1 with the fixed evaluator,
# GL + ICE seeded from run1_v2 / run_c1_v2 (only molecules whose candidates changed are re-scored); (2) frozen-ledger evaluation on the dev
# tune+eval molecules: M1 (run1b_v2, rank_v2, w_ice 1) vs M2x (run_v3b_eval, rank_v4b, w_ice 0), outputs learned / insurance / fixed / switch /
# blend21 / blend11, tau 0.9; (3) the same on the dev C1 set (run_c1b_v2 vs run_v3b_c1). Waits for the v3b chain to finish (CPU).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; J=spark/jobs/b1_features_job_v3b.sh; V2="--k_fpp 100 --k_pop 0"
until grep -q "V3B_ALL_DONE" logs/spark_v3b_chain.log 2>/dev/null; do sleep 120; done
echo "== $(date +%T) v2b tables (corrected C1 reference selection) for the frozen control"
OLD_RUN=$B/run1_v2   FEAT_ARGS="$V2" RUNNERS="gl ice" bash $J $B/eval_set/p1_molecules.csv $B/run1b_v2 A_timstof B_nplib
OLD_RUN=$B/run_c1_v2 FEAT_ARGS="$V2" RUNNERS="gl ice" bash $J $B/eval_c1/p1_molecules.csv $B/run_c1b_v2 B_nplib
echo "V2B_DEV_TABLES_DONE $(date +%T)"
export OMP_NUM_THREADS=2
echo "== $(date +%T) frozen-ledger comparison on dev tune+eval: M1 (rank_v2, v2 tables) vs M2x (rank_v4b, v3b tables), tau 0.9"
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/eval_set/p1_molecules_tune_eval.csv --cands M1:$B/run1b_v2:$B/rank_v2/lambdarank.txt:1 M2x:$B/run_v3b_eval:$B/rank_v4b/lambdarank.txt:0 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --out $B/dev_pair_final > $B/dev_pair_final.log 2>&1; echo "exit $?"
grep -v "^|---" $B/dev_pair_final/locked_results.md | grep -a "^| A_timstof | c2 (n\|^| B_nplib | c2 (n\|^| B_nplib | c1 (n\|M2x − M1\|M2x: blend21\|M1: blend21\|M2x: learned − fixed\|M1: learned − fixed" | cut -c1-200
echo "== $(date +%T) frozen-ledger comparison on the dev C1 set (B_nplib): M1 (run_c1b_v2) vs M2x (run_v3b_c1)"
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/eval_c1/p1_molecules.csv --sets B_nplib --cands M1:$B/run_c1b_v2:$B/rank_v2/lambdarank.txt:1 M2x:$B/run_v3b_c1:$B/rank_v4b/lambdarank.txt:0 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --out $B/dev_pair_final_c1set > $B/dev_pair_final_c1set.log 2>&1; echo "exit $?"
grep -v "^|---" $B/dev_pair_final_c1set/locked_results.md | grep -a "^| B_nplib | c1 (n\|^| B_nplib | c2 (n\|M2x − M1\|M2x: blend21\|M1: blend21" | cut -c1-200
echo "V2B_COMPARE_DONE $(date +%T)"
