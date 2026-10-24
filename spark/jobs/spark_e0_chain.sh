#!/bin/bash
# E0 offline chain (Codex 015 (a)): the public 0.464 pipeline on OUR molecules, run after run, each followed by the per-stage comparison with B1
# when a B1 pipeline run of the same molecules / view exists. Order: W7 600 class-2 proxy -> W7 600 class-1 proxy -> panel 250 class-2 -> panel 250 class-1.
# Budgets (s) generous so coverage is not truncated: ICE_BUDGET GL_BUDGET N1_BUDGET env (defaults 21600 / 10800 / 3600).
# Usage: setsid nohup bash spark/jobs/spark_e0_chain.sh > logs/spark_e0_chain.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
E=experiments/e0_offline; S=$E/runs/_shared; W7=experiments/b1_baseline/eval_test_full3; PE=$S/eval_test_panel; MOLS=experiments/b1_baseline/eval_set/p1_molecules.csv
PMOLS=experiments/b1_baseline/panel_np250/p1_molecules.csv
run() {   # name test train view b1_run eval_dir mols
  local name=$1 test=$2 train=$3 view=$4 b1=$5 ev=$6 mols=$7
  if [ -s $E/runs/$name/work/submission.csv ] && grep -q "E0 OFFLINE DONE" logs/e0_$name.log 2>/dev/null; then echo "E0_CHAIN $name already done"; else
    echo "== $(date -Is) E0_CHAIN start $name"
    bash spark/jobs/spark_e0_offline.sh $name $test $train 0 >> logs/e0_$name.log 2>&1; rc=$?
    echo "E0_CHAIN $name rc=$rc $(date -Is)"
  fi
  if [ -n "$b1" ] && [ -s $b1/submission.csv ] && [ -s $E/runs/$name/work/submission.csv ]; then
    .venv/bin/python -X utf8 $E/e0_vs_b1_stages.py --e0 $E/runs/$name/work --b1 $b1 --eval_dir $ev --mols $mols --out $E/runs/$name/compare --view $view > logs/e0_compare_$name.log 2>&1 \
      && echo "E0_CHAIN compare $name done $(date -Is)" || echo "E0_CHAIN compare $name FAILED (see logs/e0_compare_$name.log)"
  else echo "E0_CHAIN compare $name skipped (no B1 pipeline run at '$b1' or no E0 output)"; fi
}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
run c2_full3 $W7/test.parquet $S/train_c2_full3.parquet c2 $W7/run_c2 $W7 $MOLS
run c1_full3 $W7/test.parquet $S/train_c1_full3.parquet c1 $W7/run_c1 $W7 $MOLS
run panel_c2 $PE/test.parquet $S/train_c2_panel.parquet c2 "${B1_PANEL_C2:-}" $PE $PMOLS
run panel_c1 $PE/test.parquet $S/train_c1_panel.parquet c1 "${B1_PANEL_C1:-}" $PE $PMOLS
echo "E0_CHAIN_DONE $(date -Is)"
