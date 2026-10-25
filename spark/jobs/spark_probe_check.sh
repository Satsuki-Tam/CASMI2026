#!/bin/bash
# Codex 023: check the diagnostic class-decomposition probes (submission_probe_{train,nontrain}.csv) of the registered M2x configuration on the
# 16-molecule panel parity set, in both views: c1 (truth identity stays a training structure -> rr_probe_train >= rr, rr_probe_nontrain = 0) and
# c2 (truth identity masked -> treated as non-training -> rr_probe_nontrain >= rr, rr_probe_train = 0). The main list must be unchanged by the patch.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; E=$B/eval_test_parity16_fe; MODEL=$B/rank_v4b/lambdarank.txt; O=$B/probe_check
rm -rf $O; mkdir -p $O
echo "== $(date +%T) probe check, pipeline sha $(sha256sum $B/b1_pipeline.py | cut -c1-16)"
for mode in c1 c2; do
  $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $O/run_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 > $O/run_$mode.log 2>&1
  echo "pipeline $mode exit $? ; $(grep -a 'OFFICIAL MRR' $O/run_$mode.log | cut -c1-160)"
  $PY -X utf8 -c "
import pandas as pd, json
d = pd.read_csv('$O/run_$mode/eval_per_molecule.csv'); s = json.load(open('$O/run_$mode/eval_scores.json'))
print('$mode', 'main', round(d.rr.mean(), 4), 'probe', s['official_mrr25_probe'], 'n', len(d))
if '$mode' == 'c1': print('  train>=main', bool((d.rr_probe_train >= d.rr - 1e-12).all()), ' nontrain==0', bool((d.rr_probe_nontrain == 0).all()))
else: print('  nontrain>=main', bool((d.rr_probe_nontrain >= d.rr - 1e-12).all()), ' train==0', bool((d.rr_probe_train == 0).all()))
print(d[['molecule_id', 'rr', 'rr_probe_train', 'rr_probe_nontrain']].to_string(index=False))
"
done
echo "PROBECHECK_DONE $(date +%T)"
