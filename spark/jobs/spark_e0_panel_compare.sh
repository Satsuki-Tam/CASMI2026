#!/bin/bash
# Panel ledgers against the B1 panel pipeline runs (M2x blend21, eval mode: runs/_shared/eval_test_panel/run_{c2,c1}; completed 2026-10-25 ~10:30 JST,
# after spark_e0_chain2.sh had been launched with empty B1_PANEL_C2 / B1_PANEL_C1). Waits for each panel E0 run of chain2 to finish, then runs the ledger.
# Usage: setsid nohup bash spark/jobs/spark_e0_panel_compare.sh > /home/svlg/CASMI2026/logs/spark_e0_panel_compare.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
E=experiments/e0_offline; PE=$E/runs/_shared/eval_test_panel; PMOLS=experiments/b1_baseline/panel_np250/p1_molecules.csv
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for v in c2 c1; do
  name=panel_$v
  echo "== $(date -Is) waiting for E0 run $name"
  until grep -q "E0_RUN_DONE $name" logs/e0_$name.log 2>/dev/null; do sleep 120; done
  echo "== $(date -Is) $name: $(grep -a "E0_RUN_DONE $name" logs/e0_$name.log | tail -1)"
  if [ -s $E/runs/$name/work/submission.csv ] && [ -s $PE/run_$v/submission.csv ]; then
    .venv/bin/python -X utf8 $E/e0_vs_b1_stages.py --e0 $E/runs/$name/work --b1 $PE/run_$v --eval_dir $PE --mols $PMOLS --out $E/runs/$name/compare --view $v > logs/e0_compare_$name.log 2>&1 \
      && echo "PANEL_COMPARE $name done $(date -Is)" || echo "PANEL_COMPARE $name FAILED (see logs/e0_compare_$name.log) $(date -Is)"
  else echo "PANEL_COMPARE $name skipped: missing E0 output ($E/runs/$name/work/submission.csv) or B1 run ($PE/run_$v/submission.csv) $(date -Is)"; fi
done
echo "PANEL_COMPARE_DONE $(date -Is)"
