#!/bin/bash
# Codex 018 proposal 4-1 (decisive experiment for the memorization hypothesis): B1 feature tables with a FULL-TRAIN FPNet instead of the
# fold-0 (held-out) model, on (a) the panel 250 (NP, timsTOF, train molecules; C1 view = hidden class-1 proxy) and (b) the W7 dev sets A/B
# (fold-0 molecules) with the fold-1 model, which was trained on fold 0 = a 'seen' control for the C2 proxy. Everything else = the M2x
# configuration (k_fpp 200, k_pop 50, GL only). Then the registered-output evaluator compares M2x (fold-0 FPNet) vs M2x_seen (seen FPNet)
# on the same molecules. The full-train checkpoint is the public asset casmi26-fpnet-full1 (training code published with the asset).
# Waits for the fit-pool chain so that at most two GPU jobs run at once. Usage: setsid nohup bash spark_panel_full1_chain.sh > logs/spark_panel_full1_chain.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; J=spark/jobs/b1_features_job_v3b.sh
FULL1=data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-fpnet-full1/casmi26-fpnet-full1/fpnet_full1.pt
until grep -q "FITPOOL_DONE\|FITPOOL FAILED" logs/spark_fitpool_chain.log 2>/dev/null; do sleep 300; done
[ -s $FULL1 ] || { echo "FULL1 FAILED: checkpoint missing"; exit 1; }
# model directories that look like fold_safe_fpnet but with a different 'fpnet_fold0.pt' (the features job loads <dir>/fpnet_fold0.pt)
for spec in "fpnet_full1_as_fold0:$FULL1" "fpnet_fold1_as_fold0:data/external/fold_safe_fpnet/fpnet_fold1.pt"; do
  name=${spec%%:*}; ck=${spec#*:}; D=data/external/$name; mkdir -p $D
  for f in data/external/fold_safe_fpnet/*; do bn=$(basename $f); [ "$bn" = fpnet_fold0.pt ] && continue; [ -e $D/$bn ] || ln -s $(realpath $f) $D/$bn; done
  ln -sfn $(realpath $ck) $D/fpnet_fold0.pt; echo "$D/fpnet_fold0.pt -> $(readlink $D/fpnet_fold0.pt) sha $(sha256sum $ck | cut -c1-16)"
done
run_feats() {   # run_feats <fold_safe_dir> <eval_csv> <out_run> <seed_run> <sets...>
  local FS=$1 EVAL=$2 RUN=$3 SEED=$4; shift 4
  echo "== $(date +%T) features $RUN (FPNet dir $FS; GL seeded from $SEED) sets $*"
  mkdir -p $RUN/work
  # b1_features_job_v3b.sh hard-codes --fold_safe data/external/fold_safe_fpnet -> run the same steps inline with the alternative directory
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features exit $? : $(grep -a '^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-160)"
  for S in "$@"; do
    IN=$RUN/b1_runner_${S}_in.json; [ -s $IN ] || { echo "no runner input for $S"; continue; }
    .venv-ice/bin/python spark/jobs/ice_resume.py --seed $SEED/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== gl $S $(grep -o '"status": "[a-z]*"' $RUN/work/gl_${S}.json.meta.json) $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-120)"
  done
}
run_feats data/external/fpnet_full1_as_fold0 $B/panel_np250/p1_molecules.csv $B/run_panel_full1 $B/run_panel_v3b P_np250
run_feats data/external/fpnet_fold1_as_fold0 $B/eval_set/p1_molecules.csv $B/run_v3b_eval_seen $B/run_v3b_eval A_timstof B_nplib
export OMP_NUM_THREADS=2
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_v3b run_panel_full1 P_np250" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval run_v3b_eval_seen A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; base=$3; seen=$4; shift 4; OUT=$B/seen_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name: M2x (fold-0 FPNet) vs M2x_seen (seen FPNet) sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 M2x_seen:$B/$seen:$B/rank_v4b/lambdarank.txt:0 --main_of M2x=blend21 M2x_seen=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED\|truth_in_short\|shortlist" $OUT/locked_results.md 2>/dev/null | cut -c1-200 | head -20
  for S in "$@"; do echo "shortlist reach $S: fold0 $(.venv/bin/python -c "import pandas as pd; m=pd.read_csv('$B/$base/b1_molecules_$S.csv'); print(round(m.truth_in_short_c2.mean(),3), round(m.truth_in_short_c1.mean(),3))") | seen $(.venv/bin/python -c "import pandas as pd; m=pd.read_csv('$B/$seen/b1_molecules_$S.csv'); print(round(m.truth_in_short_c2.mean(),3), round(m.truth_in_short_c1.mean(),3))")"; done
done
echo "FULL1_DONE $(date +%T)"
