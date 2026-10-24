#!/bin/bash
# B1 submission pipeline (M2x blend21 configuration, evaluation mode) on the PANEL test file built for the E0 offline chain, both views, so the
# E0-vs-B1 stage comparison can also be made on the panel (Codex 015 (a); the E0 chain skips the panel comparison when no B1 pipeline run exists).
# Waits for the dev2 chain to finish first so that at most two GPU jobs (E0 + this) run at once. Usage: setsid nohup bash spark_panel_pipe_chain.sh > logs/spark_panel_pipe_chain.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; PE=experiments/e0_offline/runs/_shared/eval_test_panel; MODEL=$B/rank_v4b/lambdarank.txt
until grep -q "P2DEV_DONE\|FAILED" logs/spark_p2dev_chain.log 2>/dev/null; do sleep 300; done
for f in $PE/test.parquet $PE/mask_c2.json $PE/mask_c1.json $PE/solution.csv; do [ -s $f ] || { echo "PANEL_PIPE FAILED: missing $f"; exit 1; }; done
echo "== $(date +%T) panel pipeline runs start (pipeline sha $(sha256sum $B/b1_pipeline.py | cut -c1-16), model $(sha256sum $MODEL | cut -c1-16))"
for mode in c2 c1; do
  $PY -X utf8 $B/b1_pipeline.py --test $PE/test.parquet --out $PE/run_$mode --workers 12 --folds 0 --mask_json $PE/mask_$mode.json --solution $PE/solution.csv --rank_model $MODEL --tau 0.9 --main blend21 --k_fpp 200 --k_pop 50 --w_ice 0 > $PE/run_$mode.log 2>&1
  echo "== $(date +%T) panel run_$mode exit $? : $(grep -a 'official_mrr25\|submission written' $PE/run_$mode.log | tail -2 | cut -c1-200)"
  echo "PANEL_PIPE_${mode}_DONE $(date +%T)"
done
echo "PANEL_PIPE_DONE $(date +%T)"
