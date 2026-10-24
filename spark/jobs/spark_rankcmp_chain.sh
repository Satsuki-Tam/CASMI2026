#!/bin/bash
# After the LambdaRank v2 baseline (28 features) is trained by the post-chain: the one small comparison Codex 008 asked for
# (v3s = per-model tie-aware ranks + per-model margins + window size) and the minimal monotone variant, same runs / same groups.
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "TRAIN_V2_DONE" logs/spark_post_chain.log 2>/dev/null; do sleep 180; done
git fetch -q origin && git checkout -q origin/main -- $B/b1_rank_train.py $B/b1_rankfeats.py && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
RUNS="$B/run_p1_v2:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run1_v2:$B/eval_set/p1_molecules.csv $B/run_c1_v2:$B/eval_c1/p1_molecules.csv"
for V in "v3s:" "v2:--monotone" "v3s:--monotone"; do
  F=${V%%:*}; OPT=${V#*:}; OUT=$B/rank_v2_${F}${OPT:+_mono}
  echo "== $(date +%T) train feats=$F $OPT -> $OUT"
  $PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $OUT --feats $F $OPT > $OUT.log 2>&1; echo "exit $?"
  $PY - "$OUT" <<'EOF'
import json, sys; o = sys.argv[1]; r = json.load(open(f"{o}/rank_results.json"))
print(o, '| selected', {k: r['selected']['params'][k] for k in ('num_leaves', 'learning_rate')}, r['selected']['rounds'])
print('  EVAL strict: fixed', {k: round(v['strict'], 3) for k, v in r['eval_fixed'].items()}, '| lambdarank', {k: round(v['strict'], 3) for k, v in r['eval_lambdarank'].items()})
print('  delta strict vs S(2,1,0.5):', {k: (round(v['delta_strict'], 3), [round(x, 3) for x in v['ci95_strict']], v['n']) for k, v in r['eval_delta'].items()})
print('  top importance:', sorted(r['importance'].items(), key=lambda kv: -kv[1])[:8])
EOF
done
echo "== baseline v2 for reference:"; $PY - <<'EOF'
import json; r = json.load(open("experiments/b1_baseline/rank_v2/rank_results.json"))
print('  EVAL strict: fixed', {k: round(v['strict'], 3) for k, v in r['eval_fixed'].items()}, '| lambdarank', {k: round(v['strict'], 3) for k, v in r['eval_lambdarank'].items()})
print('  delta strict vs S(2,1,0.5):', {k: (round(v['delta_strict'], 3), [round(x, 3) for x in v['ci95_strict']], v['n']) for k, v in r['eval_delta'].items()})
EOF
echo "RANKCMP_DONE $(date +%T)"
