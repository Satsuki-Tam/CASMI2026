#!/bin/bash
# Codex 017 proposal 2 (preparation): feature tables for the extra ranker-training pool = remaining fold-0 molecules of the p2 strata
# (identity groups disjoint from dev2 / locked2 / every earlier set), M2x configuration (k_fpp 200, k_pop 50, GL only). Used later as
# additional 'fit' rows (G-type: timsTOF query + other-library references; E/F: no forward; D: no references). Waits for the panel pipeline
# chain so that at most two GPU jobs run at once. Usage: setsid nohup bash spark_fitpool_chain.sh > logs/spark_fitpool_chain.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; J=spark/jobs/b1_features_job_v3b.sh; EVAL=$B/eval_set2/fit_pool/fit_molecules.csv
SETS=${SETS:-"G_tims_crosslib C_np_crosslib F_np_uncovered E_np_negonly D_np_single"}
until grep -q "PANEL_PIPE_DONE\|PANEL_PIPE FAILED" logs/spark_panel_pipe_chain.log 2>/dev/null; do sleep 300; done
[ -s $EVAL ] || { echo "FITPOOL FAILED: missing $EVAL"; exit 1; }
echo "== $(date +%T) fit-pool features start ($(wc -l < $EVAL) rows; sets $SETS)"
mkdir -p $B/run_fitpool_noseed/work
OLD_RUN=$B/run_fitpool_noseed FEAT_ARGS="--k_fpp 200 --k_pop 50" RUNNERS=gl WORKERS=${WORKERS:-10} bash $J $EVAL $B/run_fitpool_v3 $SETS
echo "FITPOOL_DONE $(date +%T)"
