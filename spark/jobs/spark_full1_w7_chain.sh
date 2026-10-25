#!/bin/bash
# Codex 018 step 2 (same-window FPNet comparison), continuation of spark_panel_full1_chain.sh: feature tables with the public full-train
# checkpoint (fpnet_full1_as_fold0) on the W7 dev sets A/B and the dev2 strata D/E/F (reach headroom), then the same-window comparison of
# the truth's FP-only / FP+prior window ranks across fold-0 (unseen), fold-1 (trained on fold 0 = these molecules' acquisitions) and full1.
# GL is seeded with --reuse_complete (molecules whose candidate set changed are fully re-scored; no accidental fallbacks). Waits for FULL1_DONE.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
until grep -q "FULL1_DONE\|FULL1 FAILED" logs/spark_panel_full1_chain.log 2>/dev/null; do sleep 300; done
run_feats() {   # run_feats <fold_safe_dir> <eval_csv> <out_run> <seed_run> <sets...>
  local FS=$1 EVAL=$2 RUN=$3 SEED=$4; shift 4
  echo "== $(date +%T) features $RUN (FPNet dir $FS -> $(readlink -f $FS/fpnet_fold0.pt | xargs basename); GL seeded from $SEED) sets $*"
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
run_feats data/external/fpnet_full1_as_fold0 $B/eval_set/p1_molecules.csv $B/run_v3b_eval_full1 $B/run_v3b_eval A_timstof B_nplib
run_feats data/external/fpnet_full1_as_fold0 $B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_full1 $B/run_p2dev_v3 D_np_single E_np_negonly F_np_uncovered
run_feats data/external/fpnet_fold1_as_fold0 $B/eval_set2/v2/p2_molecules.csv $B/run_p2dev_fold1 $B/run_p2dev_v3 D_np_single E_np_negonly F_np_uncovered
export OMP_NUM_THREADS=4
mkdir -p $B/diag
$PY -X utf8 $B/fp_reach_compare.py --eval_csv $B/eval_set/p1_molecules.csv --runs fold0=$B/run_v3b_eval fold1_seen=$B/run_v3b_eval_seen full1=$B/run_v3b_eval_full1 --sets A_timstof B_nplib --out $B/diag/fp_reach_devAB.md | tail -40
$PY -X utf8 $B/fp_reach_compare.py --eval_csv $B/eval_set2/v2/p2_molecules.csv --runs fold0=$B/run_p2dev_v3 fold1_seen=$B/run_p2dev_fold1 full1=$B/run_p2dev_full1 --sets D_np_single E_np_negonly F_np_uncovered --out $B/diag/fp_reach_p2dev.md | tail -60
$PY -X utf8 $B/fp_reach_compare.py --eval_csv $B/panel_np250/p1_molecules.csv --runs fold0=$B/run_panel_v3b full1=$B/run_panel_full1 --sets P_np250 --out $B/diag/fp_reach_panel.md | tail -20
echo "FULL1_W7_DONE $(date +%T)"
