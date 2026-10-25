#!/bin/bash
# 2026-10-26 01:10 (pre-registered in reports/agent_review/027_prereg_ens2.md before the run): FPNet ensemble ENS2 = mean logits of
# full_eval (5b8d1c31) and full_rk (1f47f1ba). Both hold out dev2 (unseen) and both have seen the panel identities (queries removed), so
# dev2 and panel C1 are clean for the ensemble. Feature tables with the ensemble (GL seeded from the full_eval runs), then the registered
# evaluator: ENS2 (+ rank_v4b) vs M2x_fe (full_eval + rank_v4b = submitted 57630996, Public 0.370) vs M2x (fold-0 + rank_v4b, Public 0.354).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FS=data/external/fpnet_fulleval_as_fold0; EXTRA=data/external/fpnet_fullrk_as_fold0/fpnet_fold0.pt
echo "== $(date +%T) ENS2: fold0 slot $(sha256sum $(readlink -f $FS/fpnet_fold0.pt) | cut -c1-16), extra $(sha256sum $(readlink -f $EXTRA) | cut -c1-16), features sha $(sha256sum $B/b1_features.py | cut -c1-16)"
run_feats() {   # run_feats <eval_csv> <out_run> <seed_run> <sets...>
  local EVAL=$1 RUN=$2 SEED=$3; shift 3
  echo "== $(date +%T) features $RUN (ENS2; GL seeded from $SEED) sets $*"
  mkdir -p $RUN/work
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --extra_ckpts $EXTRA --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features exit $? : $(grep -a '^FPNet ensemble\|^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-220)"
  for S in "$@"; do
    IN=$RUN/b1_runner_${S}_in.json; [ -s $IN ] || { echo "no runner input for $S"; continue; }
    .venv-ice/bin/python spark/jobs/ice_resume.py --seed $SEED/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== gl $S $(grep -o '"status": "[a-z]*"' $RUN/work/gl_${S}.json.meta.json) $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-120)"
  done
}
run_feats $B/panel_np250/p1_molecules.csv $B/run_ens2_panel $B/run_panel_fe P_np250
run_feats $B/eval_set2/v2/p2_molecules.csv $B/run_ens2_p2dev $B/run_p2dev_fe C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib
export OMP_NUM_THREADS=2
for E in "panel $B/panel_np250/p1_molecules.csv run_ens2_panel run_panel_fe run_panel_v3b P_np250" "p2dev $B/eval_set2/v2/p2_molecules.csv run_ens2_p2dev run_p2dev_fe run_p2dev_v3 C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; do
  set -- $E; name=$1; csv=$2; ens=$3; fe=$4; base=$5; shift 5; OUT=$B/ens2_eval_$name; rm -rf $OUT; mkdir -p $OUT
  echo "== $(date +%T) registered evaluation $name: M2x_fe ($fe) / M2x ($base) / ENS2 ($ens), rank_v4b, sets $*"
  $PY -X utf8 $B/b1_locked_eval.py --eval_csv $csv --cands M2x_fe:$B/$fe:$B/rank_v4b/lambdarank.txt:0 M2x:$B/$base:$B/rank_v4b/lambdarank.txt:0 ENS2:$B/$ens:$B/rank_v4b/lambdarank.txt:0 \
    --main_of M2x_fe=blend21 M2x=blend21 ENS2=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets "$@" --out $OUT > $OUT/eval.log 2>&1
  echo "evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md 2>/dev/null | cut -c1-170
done
echo "ENS2_DONE $(date +%T)"
