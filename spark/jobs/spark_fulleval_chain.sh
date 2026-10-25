#!/bin/bash
# Evaluation of the locally trained full_eval FPNet (019 decision §3). Waits for the checkpoint marker copied from the PC, then:
#   1. B1 feature tables (M2x configuration: k_fpp 200, k_pop 50, GL only; GL seeded with --reuse_complete so changed candidate sets are
#      fully re-scored) with full_eval as the FPNet on: the panel (C1 view = class-1 proxy: identity trained, query acquisition not),
#      dev2 v2 all strata (identity groups held out = unseen), W7 A/B (trained = diagnostic);
#   2. same-window reach/MRR comparison fold0 / fold1-seen / full1 / full_eval (fp_reach_compare.py);
#   3. registered-output comparison M2x (fold-0 FPNet tables) vs M2x_fe (full_eval tables), same ranker rank_v4b, main blend21, fallback.
# Usage: setsid nohup bash spark_fulleval_chain.sh > logs/spark_fulleval_chain.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FE=data/external/fpnet_fulleval_as_fold0
until [ -f $FE/READY ]; do sleep 120; done
echo "== $(date +%T) full_eval checkpoint ready: $(cat $FE/READY)"
for f in data/external/fold_safe_fpnet/*; do bn=$(basename $f); [ "$bn" = fpnet_fold0.pt ] && continue; [ -e $FE/$bn ] || ln -s $(realpath $f) $FE/$bn; done
$PY - <<'PY' || { echo "FULLEVAL FAILED: checkpoint does not load"; exit 1; }
import sys; sys.path.insert(0, "data/external/v3_models/code")
from casmi import fpnet
m = fpnet.load_model("data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt", "cpu"); print("full_eval loads:", sum(p.numel() for p in m.parameters()), "params")
PY
run_feats() {   # run_feats <fold_safe_dir> <eval_csv> <out_run> <seed_run> <sets...>
  local FS=$1 EVAL=$2 RUN=$3 SEED=$4; shift 4
  echo "== $(date +%T) features $RUN (FPNet $(readlink -f $FS/fpnet_fold0.pt | xargs basename); GL seeded from $SEED) sets $*"
  mkdir -p $RUN/work
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features exit $? : $(grep -a '^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-160)"
  for S in "$@"; do
    IN=$RUN/b1_runner_${S}_in.json; [ -s $IN ] || { echo "no runner input for $S"; continue; }
    .venv-ice/bin/python spark/jobs/ice_resume.py --seed $SEED/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== gl $S $(grep -o '"status": "[a-z]*"' $RUN/work/gl_${S}.json.meta.json) $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-120)"
  done
}
run_feats $FE $B/panel_np250/p1_molecules.csv $B/run_panel_fe $B/run_panel_v3b P_np250
run_feats $FE $B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_fe $B/run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib
run_feats $FE $B/eval_set/p1_molecules.csv $B/run_v3b_eval_fe $B/run_v3b_eval A_timstof B_nplib
export OMP_NUM_THREADS=4
R() { [ -d $1 ] && echo "$2=$1"; }
$PY -X utf8 $B/fp_reach_compare.py --eval_csv $B/panel_np250/p1_molecules.csv --runs fold0=$B/run_panel_v3b $(R $B/run_panel_full1 full1) full_eval=$B/run_panel_fe --sets P_np250 --out $B/diag/fp_reach_panel_fe.md | tail -22
$PY -X utf8 $B/fp_reach_compare.py --eval_csv $B/eval_set2/v2/p2_molecules.csv --runs fold0=$B/run_p2dev_v3 $(R $B/run_p2dev_fold1 fold1_seen) $(R $B/run_p2dev_full1 full1) full_eval=$B/run_p2dev_fe --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --out $B/diag/fp_reach_p2dev_fe.md | tail -60
$PY -X utf8 $B/fp_reach_compare.py --eval_csv $B/eval_set/p1_molecules.csv --runs fold0=$B/run_v3b_eval $(R $B/run_v3b_eval_seen fold1_seen) $(R $B/run_v3b_eval_full1 full1) full_eval=$B/run_v3b_eval_fe --sets A_timstof B_nplib --out $B/diag/fp_reach_devAB_fe.md | tail -40
export OMP_NUM_THREADS=2
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_v3b run_panel_fe P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 run_p2dev_fe C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval run_v3b_eval_fe A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; base=$3; fe=$4; shift 4; OUT=$B/fe_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name: M2x (fold-0 FPNet) vs M2x_fe (full_eval FPNet), sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 M2x_fe:$B/$fe:$B/rank_v4b/lambdarank.txt:0 --main_of M2x=blend21 M2x_fe=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-160
done
echo "FULLEVAL_DONE $(date +%T)"
