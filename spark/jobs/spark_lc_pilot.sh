#!/bin/bash
# Codex 030 pilot: feature tables with --lib_conditions (full_eval FPNet, same shortlists as run_*_fe; GL reused by seeding) for the audits
# before any ranker training (label-free computation check, reference-mask shortcut check, matched comparisons).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FS=data/external/fpnet_fulleval_as_fold0
echo "== $(date +%T) features sha $(sha256sum $B/b1_features.py | cut -c1-12)"
run_feats() {   # run_feats <eval_csv> <out_run> <seed_run> <sets...>
  local EVAL=$1 RUN=$2 SEED=$3; shift 3; mkdir -p $RUN/work
  $PY -X utf8 $B/b1_features.py --eval_csv $EVAL --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --lib_conditions --sets "$@" > $RUN/features.log 2>&1
  echo "== $(date +%T) features $RUN exit $? : $(grep -a '^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
  for S in "$@"; do
    IN=$RUN/b1_runner_${S}_in.json; [ -s $IN ] || continue
    .venv-ice/bin/python spark/jobs/ice_resume.py --seed $SEED/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-120)"
  done
}
run_feats $B/panel_np250/p1_molecules.csv $B/run_panel_fe_lc $B/run_panel_fe P_np250
run_feats $B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_fe_lc $B/run_p2dev_fe C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib
echo "LCPILOT_DONE $(date +%T)"
