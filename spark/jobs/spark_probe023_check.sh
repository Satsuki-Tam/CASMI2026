#!/bin/bash
# Codex 023: the probe kernel embeds experiments/b1_probe023 = the registered v4 pipeline (7e84ed6) + probe files. Run it on the 16-molecule panel
# parity set in both views, check the probe inequalities, and compare its main list with the current pipeline's main list (probe_check runs).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_probe023; PY=.venv/bin/python; E=$B/eval_test_parity16_fe; MODEL=$B/rank_v4b/lambdarank.txt; O=$B/probe023_check
rm -rf $O; mkdir -p $O
echo "== $(date +%T) probe023 check, pipeline sha $(sha256sum $S/b1_pipeline.py | cut -c1-16), common sha $(sha256sum $S/b1_common.py | cut -c1-16)"
for mode in c1 c2; do
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $O/run_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 > $O/run_$mode.log 2>&1
  echo "pipeline $mode exit $? ; $(grep -a 'OFFICIAL MRR' $O/run_$mode.log | cut -c1-160)"
  $PY -X utf8 -c "
import pandas as pd, json
d = pd.read_csv('$O/run_$mode/eval_per_molecule.csv'); s = json.load(open('$O/run_$mode/eval_scores.json'))
print('$mode', 'main', round(d.rr.mean(), 4), 'probe', s['official_mrr25_probe'], 'n', len(d)); print('  pool>=train', bool((d.rr_probe_pool >= d.rr_probe_train - 1e-12).all()), ' pool+pubchem>=main', bool((d.rr_probe_pool + d.rr_probe_pubchem >= d.rr - 1e-12).all())); print('  coconut+pubchem>=nontrain', bool((d.rr_probe_coconut + d.rr_probe_pubchem >= d.rr_probe_nontrain - 1e-12).all()), ' exclusive', bool(((d.rr_probe_coconut > 0) & (d.rr_probe_pubchem > 0)).sum() == 0))
if '$mode' == 'c1': print('  train>=main', bool((d.rr_probe_train >= d.rr - 1e-12).all()), ' nontrain==0', bool((d.rr_probe_nontrain == 0).all()))
else: print('  nontrain>=main', bool((d.rr_probe_nontrain >= d.rr - 1e-12).all()), ' train==0', bool((d.rr_probe_train == 0).all()))
a = pd.read_csv('$O/run_$mode/submission.csv').set_index('molecule_id'); b = pd.read_csv('$B/probe_check/run_$mode/submission.csv').set_index('molecule_id')
same = (a.loc[b.index, 'smiles'] == b['smiles']); print('  main list identical to current pipeline for', int(same.sum()), 'of', len(b), 'molecules; differing:', list(b.index[~same]))
"
done
echo "PROBE023CHECK_DONE $(date +%T)"
