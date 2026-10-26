#!/bin/bash
# 050 development: GLACIER on forward-model proxies (b1_common.forward_proxies) for molecules WITHOUT a covered positive spectrum, measured on
# unseen identities (fold-1/2 dev, fold-safe FPNets; dev2 with full_eval = identity unseen) and on the panel (seen, stress). Tables are NOT
# recomputed: the saved runner inputs get the proxies (proxy_runner_in.py), GLACIER runs on those molecules only, the outputs are merged into a
# copy of the run (px_merge.py; molecules with original scores are never touched), and the registered main output (rank_v4b blend21 + GL-cover
# fallback + anaw0.5, gen_eval2 --parents 0) is evaluated on the copy and on the original run with the same code. Arms: a = NH4 / water-loss
# proxies; n = a + negative-mode proxies. Pre-registration: reports/agent_review/050_prereg_proxy.md
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
PY=$HOME/CASMI2026/.venv/bin/python; IPY=$HOME/CASMI2026/.venv-ice/bin/python; R=$HOME/CASMI2026
echo "== $(date +%T) proxy_runner_in $(sha256sum proxy_runner_in.py | cut -c1-12) px_merge $(sha256sum px_merge.py | cut -c1-12) gen_eval2 $(sha256sum gen_eval2.py | cut -c1-12) b1_common $(sha256sum b1_common.py | cut -c1-12)"
SPECS="run_f1dev:eval_set_f1/p2_molecules.csv:data/external/fpnet_fold1_as_fold0:run_f1dev/gen:f1dev:E_np_negonly,F_np_uncovered
run_f2dev:eval_set_f2/p2_molecules.csv:data/external/fpnet_fold2_as_fold0:run_f2dev/gen:f2dev:E_np_negonly,F_np_uncovered
run_p2dev_fe:eval_set2/v2/p2_molecules.csv:data/external/fpnet_fulleval_as_fold0:run_p2dev_fe_g/gen:p2dev:E_np_negonly,F_np_uncovered
run_panel_fe:panel_np250/p1_molecules.csv:data/external/fpnet_fulleval_as_fold0:run_panel_fe_g/gen:panel:P_np250"
while IFS=: read RUN EV FS GEN TAG SETS; do
  SL=$(echo $SETS | tr ',' ' ')
  for ARM in a n; do
    RPX=${RUN}_px$ARM; rm -rf $RPX; mkdir -p $RPX/work
    for f in $RUN/*; do [ "$(basename $f)" = work ] || ln -s $(realpath $f) $RPX/; done
    for f in $RUN/work/*; do ln -s $(realpath $f) $RPX/work/; done
    for S in $SL; do
      NEG=""; [ $ARM = n ] && NEG="--neg"
      $PY -X utf8 proxy_runner_in.py --inp $RUN/b1_runner_${S}_in.json --out $RPX/px_runner_${S}_in.json $NEG --stats $RPX/proxy_${S}.json || { echo "PX050 FAILED: proxy $RUN $S $ARM"; exit 1; }
      rm -f $RPX/work/gl_${S}.json $RPX/work/gl_${S}.json.meta.json
      if [ "$($PY -c "import json; print(json.load(open('$RPX/proxy_${S}.json'))['molecules_with_proxy'])")" != 0 ]; then
        (cd $R && $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier experiments/b1_baseline/$RPX/px_runner_${S}_in.json experiments/b1_baseline/$RPX/work/glpx_${S}.json -- --device cuda --site none --budget 3600 > experiments/b1_baseline/$RPX/work/glpx_${S}_resume.log 2>&1)
        echo "== $(date +%T) $TAG $ARM $S gl $(grep -a '\[resume\] done' $RPX/work/glpx_${S}_resume.log | cut -c1-100)"
      fi
      $PY -X utf8 px_merge.py --orig $RUN/work/gl_${S}.json --px $RPX/work/glpx_${S}.json --out $RPX/work/gl_${S}.json || { echo "PX050 FAILED: merge $RUN $S $ARM"; exit 1; }
    done
    $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run $RPX --gen $GEN --sets $SL --eval_csv $EV --fold_safe $R/$FS --views c1,c2 --out diag/px050_${TAG}_$ARM --workers 8 > diag/px050_${TAG}_$ARM.log 2>&1
    echo "== $(date +%T) eval $TAG $ARM exit $?"
  done
  $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run $RUN --gen $GEN --sets $SL --eval_csv $EV --fold_safe $R/$FS --views c1,c2 --out diag/px050_${TAG}_base --workers 8 > diag/px050_${TAG}_base.log 2>&1
  echo "== $(date +%T) eval $TAG base exit $?"
done <<< "$SPECS"
echo "PX050_DEV_DONE $(date +%T)"
