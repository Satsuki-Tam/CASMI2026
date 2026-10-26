#!/bin/bash
# 051 development: ICEBERG added back to the fixed-rule component of the registered main (B1 dropped ICE on 2026-10-24 from early dev sets;
# the public lineage uses joint ICE+GL). ICE is run on the saved runner inputs of unseen fold-1/2 dev (C, D, G; E/F have no covered adduct)
# and of the panel (seen, class-1 regime), into run copies (originals untouched); gen_eval2i adds ice<w> outputs (main reproduced exactly).
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
PY=$HOME/CASMI2026/.venv/bin/python; IPY=$HOME/CASMI2026/.venv-ice/bin/python; R=$HOME/CASMI2026
echo "== $(date +%T) gen_eval2i $(sha256sum gen_eval2i.py | cut -c1-12) gen_eval2 $(sha256sum gen_eval2.py | cut -c1-12)"
SPECS="run_f1dev:eval_set_f1/p2_molecules.csv:data/external/fpnet_fold1_as_fold0:run_f1dev/gen:f1dev:C_np_crosslib,D_np_single,G_tims_crosslib
run_f2dev:eval_set_f2/p2_molecules.csv:data/external/fpnet_fold2_as_fold0:run_f2dev/gen:f2dev:C_np_crosslib,D_np_single,G_tims_crosslib
run_panel_fe:panel_np250/p1_molecules.csv:data/external/fpnet_fulleval_as_fold0:run_panel_fe_g/gen:panel:P_np250"
while IFS=: read RUN EV FS GEN TAG SETS; do
  SL=$(echo $SETS | tr ',' ' '); RI=${RUN}_ice; mkdir -p $RI/work
  for S in $SL; do
    [ -s $RI/work/ice_${S}.json ] && continue
    (cd $R && $IPY spark/jobs/ice_resume.py --python $IPY data/external/iceberg/ice_runner.py data/external/iceberg experiments/b1_baseline/$RUN/b1_runner_${S}_in.json experiments/b1_baseline/$RI/work/ice_${S}.json -- --device cuda --site none --budget 7200 > experiments/b1_baseline/$RI/work/ice_${S}_resume.log 2>&1)
    echo "== $(date +%T) $TAG $S ice $(grep -a '\[resume\] done' $RI/work/ice_${S}_resume.log | cut -c1-100)"
  done
  $PY -X utf8 gen_eval2i.py --model rank_v4b/lambdarank.txt --parents 0 --run $RUN --ice_run $RI --ice_w 0.5 1 --gen $GEN --sets $SL --eval_csv $EV --fold_safe $R/$FS --views c1,c2 --out diag/ice051_${TAG} --workers 8 > diag/ice051_${TAG}.log 2>&1
  echo "== $(date +%T) eval $TAG exit $?"
done <<< "$SPECS"
echo "ICE051_DEV_DONE $(date +%T)"
