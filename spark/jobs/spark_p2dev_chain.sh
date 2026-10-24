#!/bin/bash
# Codex 015/016 (b): evaluate both REGISTERED candidates on the stratified dev2 set (5 strata x 100). Two feature tables (full re-score, no seed):
#   run_p2dev_v3 = M2x configuration (k_fpp 200, k_pop 50, GL only)      run_p2dev_v2 = M1 configuration (k_fpp 100, k_pop 0, GL + ICE)
# then the registered-output evaluator (same code as the locked opening) with --main_of M1=learned M2x=blend21, all 5 strata, both views.
# Usage: WAIT_FOR_E0=1 bash spark_p2dev_chain.sh   (waits while an E0 offline run holds the GPU; set 0 to start immediately)
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; J=spark/jobs/b1_features_job_v3b.sh; EVAL=$B/eval_set2/p2_dev_molecules.csv
SETS="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
if [ "${WAIT_FOR_E0:-1}" = 1 ]; then
  while pgrep -f "^[^ ]*python[^ ]* [^ ]*run_e0_offline" > /dev/null 2>&1; do sleep 300; done
fi
echo "== $(date +%T) p2dev chain start (features sha $(sha256sum $B/b1_features.py | cut -c1-16))"
mkdir -p $B/run_p2dev_v3/work $B/run_p2dev_v2/work
# b1_features_job_v3b.sh requires OLD_RUN (seed); point it at an empty dir -> full re-score (WARNING lines expected)
mkdir -p $B/run_p2dev_noseed/work
OLD_RUN=$B/run_p2dev_noseed FEAT_ARGS="--k_fpp 200 --k_pop 50" RUNNERS=gl       WORKERS=${WORKERS:-12} bash $J $EVAL $B/run_p2dev_v3 $SETS
echo "P2DEV_V3_DONE $(date +%T)"
OLD_RUN=$B/run_p2dev_noseed FEAT_ARGS="--k_fpp 100 --k_pop 0"  RUNNERS="gl ice" WORKERS=${WORKERS:-12} bash $J $EVAL $B/run_p2dev_v2 $SETS
echo "P2DEV_V2_DONE $(date +%T)"
OUT=$B/p2dev_eval; mkdir -p $OUT
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $EVAL --cands M1:$B/run_p2dev_v2:$B/rank_v2/lambdarank.txt:1 M2x:$B/run_p2dev_v3:$B/rank_v4b/lambdarank.txt:0 --main_of M1=learned M2x=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets $SETS --out $OUT > $OUT/p2dev_eval.log 2>&1
echo "== $(date +%T) evaluator exit $?"; grep -a "^| \|^## " $OUT/*.md 2>/dev/null | cut -c1-220 | head -80
echo "P2DEV_DONE $(date +%T)"
