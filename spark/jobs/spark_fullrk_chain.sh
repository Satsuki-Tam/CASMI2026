#!/bin/bash
# Codex 021 (+023): ranker re-fit on tables built with the locally trained full_rk FPNet (fresh init; holdouts hold/lock/rkfit; the query
# acquisitions of W7 and eval_c1 removed, so their trained identities become "identity seen, query unseen" = the hidden class-1 regime).
#   1. B1 feature tables (M2x configuration: k_fpp 200, k_pop 50, GL only, GL seeded with --reuse_complete) with full_rk as the FPNet on the three
#      ranker-training runs of rank_v4b (p1 run1 = rkfit holdout, W7 eval_set, eval_c1) and on dev2 v2 (held out) and the panel (identity seen);
#   2. new ranker rank_rk_fx: rank_v4b recipe with the SELECTED params/rounds of rank_v4b (no search), C1 x3, and the C2 rows of FPNet-seen
#      identities dropped (--c2_drop_exposure query_identity_exposure.csv); rank_rk_fx0 = same tables without the drop (control);
#   3. registered evaluation (reference = RK_old; RK_new last so that registered_delta_*.csv holds RK_new − RK_old): main pair full_rk + rank_v4b vs full_rk + rank_rk_fx (same tables, blend21 + fallback); adoption control M2x
#      (fold-0 tables + rank_v4b) on dev2 / panel / W7.
# Usage: setsid nohup bash spark_fullrk_chain.sh > logs/spark_fullrk_chain.log 2>&1 < /dev/null &
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; RK=data/external/fpnet_fullrk_as_fold0; EXPO=experiments/fpnet_full/full_rk/query_identity_exposure.csv
until [ -f $RK/READY ]; do sleep 120; done
echo "== $(date +%T) full_rk checkpoint ready: $(cat $RK/READY)"
[ -s $EXPO ] || { echo "FULLRK FAILED: exposure table missing"; exit 1; }
for f in data/external/fold_safe_fpnet/*; do bn=$(basename $f); [ "$bn" = fpnet_fold0.pt ] && continue; [ -e $RK/$bn ] || ln -s $(realpath $f) $RK/$bn; done
$PY - <<'PY' || { echo "FULLRK FAILED: checkpoint does not load"; exit 1; }
import sys; sys.path.insert(0, "data/external/v3_models/code")
from casmi import fpnet
m = fpnet.load_model("data/external/fpnet_fullrk_as_fold0/fpnet_fold0.pt", "cpu"); print("full_rk loads:", sum(p.numel() for p in m.parameters()), "params")
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
run_feats $RK experiments/p1_baseline/run1/p1_molecules.csv $B/run_rk_p1 $B/run_v3_p1 A_timstof B_nplib
run_feats $RK $B/eval_set/p1_molecules.csv $B/run_rk_eval $B/run_v3_eval A_timstof B_nplib
run_feats $RK $B/eval_c1/p1_molecules.csv $B/run_rk_c1 $B/run_v3_c1 B_nplib
run_feats $RK $B/eval_set2/v2/p2_molecules.csv $B/run_rk_p2dev $B/run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib
run_feats $RK $B/panel_np250/p1_molecules.csv $B/run_rk_panel $B/run_panel_v3b P_np250
export OMP_NUM_THREADS=4
P0=$B/rank_v4b/rank_results.json
RUNS="$B/run_rk_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_rk_eval:$B/eval_set/p1_molecules.csv $B/run_rk_c1:$B/eval_c1/p1_molecules.csv"
echo "== $(date +%T) train rank_rk_fx (rank_v4b params, C1 x3, C2 rows of FPNet-seen identities dropped) and rank_rk_fx0 (no drop; control)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_rk_fx --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 --c2_drop_exposure $EXPO > $B/rank_rk_fx_train.log 2>&1; echo "rank_rk_fx exit $?"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_rk_fx0 --feats v2_noice --drop lib_nref in_train --c1_repeat 3 --params_from $P0 > $B/rank_rk_fx0_train.log 2>&1; echo "rank_rk_fx0 exit $?"
for m in rk_fx rk_fx0; do echo "-- rank_$m: $(grep -a 'params fixed\|dropped\|fit groups after' $B/rank_${m}_train.log | tr '\n' ' ' | cut -c1-260)"; done
export OMP_NUM_THREADS=2
for E in "panel $B/panel_np250/p1_molecules.csv run_panel_v3b run_rk_panel P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_p2dev_v3 run_rk_p2dev C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib" "devAB $B/eval_set/p1_molecules.csv run_v3b_eval run_rk_eval A_timstof B_nplib"; do
  set -- $E; name=$1; csv=$2; base=$3; rk=$4; shift 4; OUT=$B/rk_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name: RK_old (full_rk + rank_v4b) vs RK_new (full_rk + rank_rk_fx) [+ RK_new0, control M2x], sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands RK_old:$B/$rk:$B/rank_v4b/lambdarank.txt:0 M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 RK_new0:$B/$rk:$B/rank_rk_fx0/lambdarank.txt:0 RK_new:$B/$rk:$B/rank_rk_fx/lambdarank.txt:0 \
    --main_of RK_old=blend21 RK_new=blend21 RK_new0=blend21 M2x=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-170
done
echo "FULLRK_DONE $(date +%T)"
