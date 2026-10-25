#!/bin/bash
# E0 offline chain, second pass (after the cell-17 engine-2 coverage assert, now recorded instead of fatal): relaunch each W7 run reusing the caches of
# its first attempt (engine-2 / PubChem lists, engine-1 base lists + audit, ICE/GL outputs as ice_resume seeds, N1 output), then the panel runs.
# The first c1_full3 (old launcher) is left running until it ends (it collects the same caches and fails at cell 17); its relaunch follows.
# Usage: setsid nohup bash spark/jobs/spark_e0_chain2.sh > /home/svlg/CASMI2026/logs/spark_e0_chain2.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
E=experiments/e0_offline; S=$E/runs/_shared; W7=experiments/b1_baseline/eval_test_full3; PE=$S/eval_test_panel; MOLS=experiments/b1_baseline/eval_set/p1_molecules.csv
PMOLS=experiments/b1_baseline/panel_np250/p1_molecules.csv
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
run() {   # name test train view b1_run eval_dir mols reuse_dir
  local name=$1 test=$2 train=$3 view=$4 b1=$5 ev=$6 mols=$7 reuse=$8
  echo "== $(date -Is) E0_CHAIN2 start $name (reuse: ${reuse:-none})"
  REUSE_FROM="$reuse" bash spark/jobs/spark_e0_offline.sh $name $test $train 0 >> logs/e0_$name.log 2>&1; local rc=$?
  echo "E0_CHAIN2 $name rc=$rc $(date -Is)"
  if [ -n "$b1" ] && [ -s $b1/submission.csv ] && [ -s $E/runs/$name/work/submission.csv ]; then
    .venv/bin/python -X utf8 $E/e0_vs_b1_stages.py --e0 $E/runs/$name/work --b1 $b1 --eval_dir $ev --mols $mols --out $E/runs/$name/compare --view $view > logs/e0_compare_$name.log 2>&1 \
      && echo "E0_CHAIN2 compare $name done $(date -Is)" || echo "E0_CHAIN2 compare $name FAILED (see logs/e0_compare_$name.log)"
  else echo "E0_CHAIN2 compare $name skipped (no B1 pipeline run at '$b1' or no E0 output)"; fi
}
run c2_full3r $W7/test.parquet $S/train_c2_full3.parquet c2 $W7/run_c2 $W7 $MOLS /home/svlg/CASMI2026/$E/runs/c2_full3/work
while pgrep -f "^.venv/bin/python -X utf8 experiments/e0_offline/run_e0_offline.py --cells experiments/e0_offline/cells --input experiments/e0_offline/runs/c1_full3/" > /dev/null; do sleep 60; done
echo "== $(date -Is) first c1_full3 ended: $(grep -a -E 'E0 OFFLINE DONE|FAILED after' logs/e0_c1_full3.log | tail -1 | cut -c1-140)"
run c1_full3r $W7/test.parquet $S/train_c1_full3.parquet c1 $W7/run_c1 $W7 $MOLS /home/svlg/CASMI2026/$E/runs/c1_full3/work
run panel_c2 $PE/test.parquet $S/train_c2_panel.parquet c2 "${B1_PANEL_C2:-}" $PE $PMOLS ""
run panel_c1 $PE/test.parquet $S/train_c1_panel.parquet c1 "${B1_PANEL_C1:-}" $PE $PMOLS ""
echo "E0_CHAIN2_DONE $(date -Is)"
