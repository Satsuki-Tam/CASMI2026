#!/bin/bash
# B1 v3 development on the Spark (after the v2 locked features, to share the GPU): shortlist = FP 100 ∪ FP+prior 200 ∪ library 20 ∪ prior 50,
# GLACIER only. Feature tables + GL + fixed-rule evaluation for the development sets and the fit set, LambdaRank with the v2_noice features,
# then the locked-set feature table (built, NOT scored here: the locked set is opened once for both candidates by the post-chain).
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "LOCKED_DONE" logs/spark_locked_chain.log 2>/dev/null; do sleep 180; done
git fetch -q origin && git checkout -q origin/main -- $B/b1_features.py $B/b1_evaluate.py $B/b1_rank_train.py $B/b1_rankfeats.py $B/b1_locked_eval.py $B/b1_diagnose.py $B/b1_shortlist_audit.py spark/jobs/b1_features_job_v3.sh spark/jobs/ice_resume.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
chmod +x spark/jobs/*.sh
export FEAT_ARGS="--k_fpp 200 --k_pop 50" RUNNERS="gl"
bash spark/jobs/b1_features_job_v3.sh $B/eval_set/p1_molecules.csv $B/run_v3_eval A_timstof B_nplib
bash spark/jobs/b1_features_job_v3.sh $B/eval_c1/p1_molecules.csv $B/run_v3_c1 B_nplib
bash spark/jobs/b1_features_job_v3.sh experiments/p1_baseline/run1/p1_molecules.csv $B/run_v3_p1 A_timstof B_nplib
$PY -X utf8 $B/b1_shortlist_audit.py $B/run_v3_eval $B/run_v3_c1:B_nplib | grep -a "^==" | cut -c1-240
echo "V3_DEV_DONE $(date +%T)"
echo "== $(date +%T) training LambdaRank v3 (v2_noice features)"
$PY -X utf8 $B/b1_rank_train.py --runs $B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv --out $B/rank_v3 --feats v2_noice > $B/rank_v3_train.log 2>&1; echo "train v3 exit $?"
grep -a "^rows\|identity groups\|^selected\|Traceback\|Error" $B/rank_v3_train.log | cut -c1-200
$PY - <<'EOF'
import json; r = json.load(open('experiments/b1_baseline/rank_v3/rank_results.json'))
print('V3 EVAL strict fixed (no ICE):', {k: round(v['strict'], 3) for k, v in r['eval_fixed'].items()}, '| lambdarank:', {k: round(v['strict'], 3) for k, v in r['eval_lambdarank'].items()})
print('V3 delta strict vs fixed:', {k: (round(v['delta_strict'], 3), [round(x, 3) for x in v['ci95_strict']], v['n']) for k, v in r['eval_delta'].items()})
print('importance:', sorted(r['importance'].items(), key=lambda kv: -kv[1])[:10])
EOF
echo "V3_TRAIN_DONE $(date +%T)"
# locked-set feature table for the v3 candidate (not scored here)
FEAT_ARGS="--k_fpp 200 --k_pop 50" RUNNERS="gl" bash spark/jobs/b1_features_job_v3.sh $B/locked_eval/p1_molecules.csv $B/run_v3_locked A_timstof B_nplib > /dev/null 2>&1
echo "== $(date +%T) v3 locked features built: $(tail -1 $B/run_v3_locked/runners.log)"
echo "V3_DONE $(date +%T)"
