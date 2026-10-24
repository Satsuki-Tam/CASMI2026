#!/bin/bash
# Post-chain, second version (replaces spark_post_chain.sh from its stage 2 on; 2026-10-24 17:30):
#  2. finish the fit set's ICE repair (set A repair started by the first post-chain; set B checked here), re-evaluate
#  3. LambdaRank v2 training (28 features)
#  4. the submission pipeline itself on the development eval set (W7): C2 and C1 proxies, learned main + fixed insurance
#  5. locked set (seed 4), opened ONCE for both pre-registered candidates: v2 (28 features, ICE) and v3 (FP+prior 200 + prior 50, GLACIER only,
#     v2_noice features) -- after the v3 chain has built its locked feature table.
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
sync_code() {
  git fetch -q origin && git checkout -q origin/main -- $B/b1_rank_train.py $B/b1_rankfeats.py $B/b1_diagnose.py $B/b1_pipeline.py $B/b1_evaluate.py $B/b1_locked_eval.py $B/b1_common.py spark/jobs/ice_resume.py src/metric.py
  echo "code synced to origin/main $(git rev-parse --short origin/main) $(date +%T)"
}
repair_ice() {  # run_dir set -> 0 if a repair ran
  local RUN=$1 S=$2 st
  st=$($PY -c "import json; print(json.load(open('$RUN/work/ice_${S}.json.meta.json')).get('status'))" 2>/dev/null); echo "== $(date +%T) $RUN ICE $S status: $st"
  [ "$st" = "ok" ] && return 1
  local IN=$RUN/b1_runner_${S}_in.filtered.json; [ -f $IN ] || IN=$RUN/b1_runner_${S}_in.json
  .venv-ice/bin/python spark/jobs/ice_resume.py --reuse --python .venv-ice/bin/python data/external/iceberg/ice_runner.py data/external/iceberg $IN $RUN/work/ice_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/ice_${S}_resume.log 2>&1
  echo "$RUN ICE $S: $(grep -a '\[resume\] done' $RUN/work/ice_${S}_resume.log)"; return 0
}
sync_code
# ---- 2
until grep -q "\[resume\] done" $B/run_p1_v2/work/ice_A_timstof_resume.log 2>/dev/null; do sleep 60; done
echo "== $(date +%T) run_p1_v2 ICE A repair: $(grep -a '\[resume\] done' $B/run_p1_v2/work/ice_A_timstof_resume.log)"
repair_ice $B/run_p1_v2 B_nplib || true
$PY -X utf8 $B/b1_evaluate.py --run $B/run_p1_v2 --eval_csv experiments/p1_baseline/run1/p1_molecules.csv --sets A_timstof B_nplib > $B/run_p1_v2/evaluate.log 2>&1; echo "run_p1_v2 re-evaluate exit $?"
grep -a "^## \|^| S(2,1,0.5) |\|^| S(2,0,0.5) |" $B/run_p1_v2/results/b1_results.md | cut -c1-200
# ---- 3
sync_code
echo "== $(date +%T) training LambdaRank v2"
$PY -X utf8 $B/b1_rank_train.py --runs $B/run_p1_v2:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run1_v2:$B/eval_set/p1_molecules.csv $B/run_c1_v2:$B/eval_c1/p1_molecules.csv --out $B/rank_v2 > $B/rank_v2_train.log 2>&1; echo "train exit $?"
grep -a "^rows\|identity groups\|^selected\|Traceback\|Error" $B/rank_v2_train.log | cut -c1-200
$PY - <<'EOF'
import json; r = json.load(open('experiments/b1_baseline/rank_v2/rank_results.json'))
print('EVAL strict fixed S(2,1,0.5):', {k: round(v['strict'], 3) for k, v in r['eval_fixed'].items()}, '| fixed 0.15:', {k: round(v['strict'], 3) for k, v in r['eval_fixed15'].items()}, '| lambdarank:', {k: round(v['strict'], 3) for k, v in r['eval_lambdarank'].items()})
print('EVAL delta vs S(2,1,0.5):', {k: dict(all=round(v['delta'], 3), ci=[round(x, 3) for x in v['ci95']], strict=round(v['delta_strict'], 3), ci_strict=[round(x, 3) for x in v['ci95_strict']], n=v['n']) for k, v in r['eval_delta'].items()})
print('importance:', sorted(r['importance'].items(), key=lambda kv: -kv[1])[:12])
EOF
echo "TRAIN_V2_DONE $(date +%T)"
# ---- 4 (W7) -- the development eval set, so it does not touch the locked set
sync_code
E=$B/eval_test_set
for mode in c2 c1; do
  if [ "$mode" = c2 ]; then M="--exclude_identities $E/exclude_identities_c2.json --exclude_rows $E/exclude_rows_c1.json"; else M="--exclude_rows $E/exclude_rows_c1.json"; fi
  echo "== $(date +%T) pipeline eval $mode (learned main + fixed insurance)"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 16 --folds 0 $M --solution $E/solution.csv --rank_model $B/rank_v2/lambdarank.txt > $E/run_$mode.log 2>&1
  echo "== $(date +%T) exit $? : $(grep -a 'OFFICIAL' $E/run_$mode.log | tail -1 | cut -c1-300)"
done
echo "PIPEEVAL_DONE $(date +%T)"
# ---- 5 locked set, opened once for both candidates
until grep -q "LOCKED_DONE" logs/spark_locked_chain.log 2>/dev/null && grep -q "V3_DONE" logs/spark_v3_chain.log 2>/dev/null; do sleep 180; done
sync_code
for S in A_timstof B_nplib; do repair_ice $B/run_locked_v2 $S || true; done
echo "== $(date +%T) locked eval (seed 4): candidate v2"
$PY -X utf8 $B/b1_locked_eval.py --run $B/run_locked_v2 --eval_csv $B/locked_eval/p1_molecules.csv --model $B/rank_v2/lambdarank.txt > $B/run_locked_v2/locked_eval.log 2>&1; echo "locked v2 exit $?"
grep -v Warning $B/run_locked_v2/locked_eval.log | tail -14 | cut -c1-230
echo "== $(date +%T) locked eval (seed 4): candidate v3"
$PY -X utf8 $B/b1_locked_eval.py --run $B/run_v3_locked --eval_csv $B/locked_eval/p1_molecules.csv --model $B/rank_v3/lambdarank.txt > $B/run_v3_locked/locked_eval.log 2>&1; echo "locked v3 exit $?"
grep -v Warning $B/run_v3_locked/locked_eval.log | tail -14 | cut -c1-230
echo "LOCKED_EVAL_DONE $(date +%T)"
