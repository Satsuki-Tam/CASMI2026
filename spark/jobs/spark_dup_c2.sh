#!/bin/bash
# Codex 032 checks (part 1 rerun after a manifest syntax fix) before the diagnostic submission (full_eval with the entropy duplicate rule off):
#  (1) C2 / C1 direction: dev2 tables rebuilt with --dup_sim 1.01 (full_eval FPNet, GL seeded) vs the existing full_eval tables, registered evaluator;
#  (2) implementation on firing molecules: dev2 molecules with suspected duplicates (truth- or decoy-side), pipeline with --dup_sim 0.98 vs 1.01
#      (no forward models), candidate dumps and duplicate counters compared per molecule and view.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; FS=data/external/fpnet_fulleval_as_fold0
echo "== $(date +%T) features sha $(sha256sum $B/b1_features.py | cut -c1-12) pipeline sha $(sha256sum $B/b1_pipeline.py | cut -c1-12)"
RUN=$B/run_p2dev_fe_dup; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/eval_set2/v2/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FS --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 --k_fpp 200 --k_pop 50 --dup_sim 1.01 \
  --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? : $(grep -a '^saved\|^done' $RUN/features.log | tr '\n' ' ' | cut -c1-200)"
for S in C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --seed $B/run_p2dev_fe/work/gl_${S}.json --reuse_complete --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-110)"
done
export OMP_NUM_THREADS=2; OUT=$B/dup_eval_p2dev; rm -rf $OUT; mkdir -p $OUT
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/eval_set2/v2/p2_molecules.csv --cands M2x_fe:$B/run_p2dev_fe:$B/rank_v4b/lambdarank.txt:0 DUP:$RUN:$B/rank_v4b/lambdarank.txt:0 \
  --main_of M2x_fe=blend21 DUP=blend21 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --sets C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib --out $OUT > $OUT/eval.log 2>&1
echo "== $(date +%T) evaluator exit $?"; grep -a "REGISTERED" $OUT/locked_results.md | cut -c1-150
echo "DUPC2_DONE $(date +%T)"
