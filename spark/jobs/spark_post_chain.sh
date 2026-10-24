#!/bin/bash
# Post-chain orchestration on the Spark (the PC stays idle, user request 2026-10-24 15:05):
#  1. after the ICEBERG repair of set B: re-evaluate + diagnose run1_v2 and run_c1_v2
#  2. fit set run_p1_v2: repair its ICE B with the resumable driver if the runner crashed, re-evaluate
#  3. LambdaRank v2 training (fit = P1 600 + fit groups; tune/eval groups of the development sets)
#  4. locked eval (seed 4) with the model, official scorer replica
#  5. the submission pipeline itself on the development eval set (W7): C2 and C1 proxies, learned main + fixed-rule insurance
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
PY=.venv/bin/python; B=experiments/b1_baseline
sync_code() {
  git fetch -q origin && git checkout -q origin/main -- $B/b1_rank_train.py $B/b1_rankfeats.py $B/b1_diagnose.py $B/b1_pipeline.py $B/b1_evaluate.py $B/b1_locked_eval.py $B/b1_common.py spark/jobs/ice_resume.py src/metric.py
  echo "code synced to origin/main $(git rev-parse --short origin/main) $(date +%T)"
}
sync_code
# ---- 1
until grep -q "ICE_FIX_DONE" logs/spark_ice_fix_chain.log 2>/dev/null; do sleep 120; done
echo "== $(date +%T) ICE repair done: $(grep -a 'run1_v2 B\|END' logs/spark_ice_fix_chain.log | tr '\n' ' ' | cut -c1-400)"
$PY -X utf8 $B/b1_evaluate.py --run $B/run1_v2 --eval_csv $B/eval_set/p1_molecules.csv --sets A_timstof B_nplib > $B/run1_v2/evaluate.log 2>&1; echo "run1_v2 evaluate exit $?"
$PY -X utf8 $B/b1_evaluate.py --run $B/run_c1_v2 --eval_csv $B/eval_c1/p1_molecules.csv --sets B_nplib > $B/run_c1_v2/evaluate.log 2>&1; echo "run_c1_v2 evaluate exit $?"
grep -a "^## \|^| S(2,1,0.5) |\|^| S(2,1,0.15) |\|libpri(tau=0.8,m=0.2)\|^C1 diagnostics" $B/run1_v2/results/b1_results.md $B/run_c1_v2/results/b1_results.md | cut -c1-230
$PY -X utf8 $B/b1_diagnose.py --run $B/run1_v2 --eval_csv $B/eval_set/p1_molecules.csv --sets A_timstof B_nplib > $B/run1_v2/diagnose.log 2>&1; echo "diagnose run1_v2 exit $?"
$PY -X utf8 $B/b1_diagnose.py --run $B/run_c1_v2 --eval_csv $B/eval_c1/p1_molecules.csv --sets B_nplib > $B/run_c1_v2/diagnose.log 2>&1; echo "diagnose run_c1_v2 exit $?"
grep -a "^strict MRR\|^oracle\|^mean push\|^best library" $B/run1_v2/results/diagnose_B_nplib.md $B/run_c1_v2/results/diagnose_B_nplib.md | cut -c1-260
echo "EVAL_FIX_DONE $(date +%T)"
# ---- 2
until grep -q "END experiments/b1_baseline/run_p1_v2" logs/b1_all_v2.log 2>/dev/null; do sleep 120; done
st=$($PY -c "import json; print(json.load(open('$B/run_p1_v2/work/ice_B_nplib.json.meta.json')).get('status'))" 2>/dev/null); echo "== $(date +%T) run_p1_v2 ICE B status: $st"
if [ "$st" != "ok" ]; then
  IN=$B/run_p1_v2/b1_runner_B_nplib_in.filtered.json; [ -f $IN ] || IN=$B/run_p1_v2/b1_runner_B_nplib_in.json
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/iceberg/ice_runner.py data/external/iceberg $IN $B/run_p1_v2/work/ice_B_nplib.json -- --device cuda --site none --budget 7200 > $B/run_p1_v2/work/ice_B_resume.log 2>&1
  echo "run_p1_v2 B ICE: $(grep -a '\[resume\] done' $B/run_p1_v2/work/ice_B_resume.log)"
  $PY -X utf8 $B/b1_evaluate.py --run $B/run_p1_v2 --eval_csv experiments/p1_baseline/run1/p1_molecules.csv --sets A_timstof B_nplib > $B/run_p1_v2/evaluate.log 2>&1; echo "run_p1_v2 re-evaluate exit $?"
fi
grep -a "^## \|^| S(2,1,0.5) |" $B/run_p1_v2/results/b1_results.md | cut -c1-200
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
# ---- 4
until grep -q "LOCKED_DONE" logs/spark_locked_chain.log 2>/dev/null; do sleep 120; done
echo "== $(date +%T) locked eval (seed 4)"
$PY -X utf8 $B/b1_locked_eval.py --run $B/run_locked_v2 --eval_csv $B/locked_eval/p1_molecules.csv --model $B/rank_v2/lambdarank.txt > $B/run_locked_v2/locked_eval.log 2>&1; echo "locked eval exit $?"
grep -v Warning $B/run_locked_v2/locked_eval.log | tail -14 | cut -c1-230
echo "LOCKED_EVAL_DONE $(date +%T)"
# ---- 5
sync_code
E=$B/eval_test_set
for mode in c2 c1; do
  if [ "$mode" = c2 ]; then M="--exclude_identities $E/exclude_identities_c2.json --exclude_rows $E/exclude_rows_c1.json"; else M="--exclude_rows $E/exclude_rows_c1.json"; fi
  echo "== $(date +%T) pipeline eval $mode (learned main + fixed insurance)"
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_$mode --workers 16 --folds 0 $M --solution $E/solution.csv --rank_model $B/rank_v2/lambdarank.txt > $E/run_$mode.log 2>&1
  echo "== $(date +%T) exit $? : $(grep -a 'OFFICIAL' $E/run_$mode.log | tail -1 | cut -c1-300)"
done
echo "PIPEEVAL_DONE $(date +%T)"
