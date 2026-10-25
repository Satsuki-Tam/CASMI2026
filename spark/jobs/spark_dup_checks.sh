#!/bin/bash
# Codex 032 checks before the diagnostic submission (full_eval with the entropy duplicate rule off):
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
# (2) implementation check on firing molecules
$PY -X utf8 - <<PY
import pandas as pd
ev = pd.read_csv("$B/eval_set2/v2/p2_molecules.csv"); ids = set()
for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"):
    m = pd.read_csv(f"$B/run_p2dev_fe/b1_molecules_{s}.csv")
    ids |= set(m.loc[(m.n_susp_dup_truth > 0) | (m.n_susp_dup_other > 0), "molecule"].astype(str))
sub = ev[ev.molecule.astype(str).isin(ids)]; sub.to_csv("/tmp/dup_fire_molecules.csv", index=False); print("firing molecules", len(sub), sub.groupby("set").size().to_dict())
PY
E=$B/eval_test_dupfire; rm -rf $E; mkdir -p $E
$PY -X utf8 $B/make_eval_test.py --eval_csv /tmp/dup_fire_molecules.csv --store data/processed/spectra_store --raw data/raw --out $E --max_spectra 8 --sets C_np_crosslib E_np_negonly F_np_uncovered > $E/build.log 2>&1 || echo "make_eval_test failed"
for mode in c1 c2; do for d in 0.98 1.01; do
  OMP_NUM_THREADS=2 $PY -X utf8 $B/b1_pipeline.py --test $E/test.parquet --out $E/run_${mode}_$d --workers 8 --mask_json $E/mask_$mode.json --rank_model $B/rank_v4b/lambdarank.txt --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $FS/fpnet_fold0.pt --no_forward --dup_sim $d > $E/run_${mode}_$d.log 2>&1; echo "pipeline $mode dup_sim $d exit $?"
done; done
$PY -X utf8 - <<PY
import pandas as pd
E = "$B/eval_test_dupfire"
for mode in ("c1", "c2"):
    a = pd.read_parquet(f"{E}/run_{mode}_0.98/b1_candidates.parquet"); b = pd.read_parquet(f"{E}/run_{mode}_1.01/b1_candidates.parquet")
    sa = pd.read_csv(f"{E}/run_{mode}_0.98/b1_stage_stats.csv").set_index("molecule"); sb = pd.read_csv(f"{E}/run_{mode}_1.01/b1_stage_stats.csv").set_index("molecule")
    fired = set(sa.index[sa.n_dup_sim > 0])
    j = a.merge(b, on=["molecule", "key"], how="outer", suffixes=("_a", "_b"), indicator=True)
    nf = j[~j.molecule.astype(str).isin(fired)]; f_ = j[j.molecule.astype(str).isin(fired)]
    print(f"{mode}: molecules {sa.shape[0]} | exact drops 0.98/1.01 {int(sa.n_dup_exact.sum())}/{int(sb.n_dup_exact.sum())} | entropy drops 0.98/1.01 {int(sa.n_dup_sim.sum())}/{int(sb.n_dup_sim.sum())} | molecules where the entropy rule fired {len(fired)}")
    print(f"   non-firing molecules: rows only in one version {int((nf._merge != 'both').sum())}, lib changed {int((nf._merge.eq('both') & (nf.lib_a != nf.lib_b)).sum())} | firing molecules: lib changed on {int((f_._merge.eq('both') & (f_.lib_a != f_.lib_b)).sum())} candidates, shortlist in/out {int((f_._merge != 'both').sum())}")
PY
echo "DUPCHECK_DONE $(date +%T)"
