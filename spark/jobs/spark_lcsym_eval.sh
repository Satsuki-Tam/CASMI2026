#!/bin/bash
# Diagnostic (031 context): how much does the asymmetric C1 reference mask depress the registered output? GL for the symmetric-mask tables
# (seeded from the standard runs; only new shortlist candidates are scored), then the registered evaluator on standard vs symmetric tables.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
for E in "run_panel_fe_lcsym run_panel_fe P_np250" "run_p2dev_fe_lcsym run_p2dev_fe C_np_crosslib G_tims_crosslib"; do
  set -- $E; RUN=$B/$1; SEED=$B/$2; shift 2
  for S in "$@"; do
    .venv-ice/bin/python spark/jobs/ice_resume.py --seed $SEED/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) gl $1 $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-120)"
  done
done
for E in "panel panel_np250/p1_molecules.csv run_panel_fe_lc run_panel_fe_lcsym P_np250" "p2dev eval_set2/v2/p2_molecules.csv run_p2dev_fe_lc run_p2dev_fe_lcsym C_np_crosslib G_tims_crosslib"; do
  set -- $E; name=$1; csv=$B/$2; std=$3; sym=$4; shift 4; OUT=$B/lcsym_eval_$name; rm -rf $OUT; mkdir -p $OUT
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands STD:$B/$std:$B/rank_v4b/lambdarank.txt:0 SYM:$B/$sym:$B/rank_v4b/lambdarank.txt:0 --main_of STD=blend21 SYM=blend21 \
    --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "== $(date +%T) $name evaluator exit $?"; grep -a "blend21 \|insurance " $OUT/eval.log | grep -a "c1 " | cut -c1-120
done
echo "LCSYMEVAL_DONE $(date +%T)"
