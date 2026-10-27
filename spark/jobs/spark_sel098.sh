#!/bin/bash
# 093 C1-cost confirmation sets (096 reallocation, Codex 097): fold 0, p2_select_v2 strata (exclusive E, F, C, G, D), one permutation seed 980,
# disjoint from every existing selection CSV (incl. np096_*) and the panel. Taken by FILE ORDER: G first 400, C first 200, E first 100, F first 100; D not used.
# Then tables (b1_features, fold-safe fpnet_fold0) + GLACIER for C and G. Nothing evaluated.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $(ls $B/*/p1_molecules.csv $B/*/p2_molecules.csv $B/*/v2/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv 2>/dev/null | grep -v '/c1cost098' | tr '\n' ' ')"
echo "exclusions: $(echo $EXCL | wc -w) files"
$PY -X utf8 $B/p2_select_v2.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds --exclude $EXCL \
  --n 400 --seed 980 --fold 0 --out_dir $B/c1cost098_raw --locked_dir $B/c1cost098_unused > $B/c1cost098_select.log 2>&1 || { echo "SELECT FAILED"; tail -5 $B/c1cost098_select.log; exit 1; }
grep -a -E "^\{|_np_|_tims_|dev|locked" $B/c1cost098_select.log | cut -c1-220 | head -20
$PY - <<'PY'
import pandas as pd, os, hashlib
B = "experiments/b1_baseline"; d = pd.read_csv(f"{B}/c1cost098_raw/p2_molecules.csv")
take = {"G_tims_crosslib": 400, "C_np_crosslib": 200, "E_np_negonly": 100, "F_np_uncovered": 100}
parts = [d[d.set == s].head(n) for s, n in take.items()]
out = pd.concat(parts); os.makedirs(f"{B}/c1cost098", exist_ok=True); out.to_csv(f"{B}/c1cost098/p2_molecules.csv", index=False)
print("c1cost098", len(out), out.set.value_counts().to_dict(), hashlib.sha256(open(f"{B}/c1cost098/p2_molecules.csv", "rb").read()).hexdigest()[:12])
PY
RUN=$B/run_c1cost098; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/c1cost098/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 \
  --k_fpp 200 --k_pop 50 --dump_gen $RUN/gen --sets G_tims_crosslib C_np_crosslib E_np_negonly F_np_uncovered > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-240)"
until grep -q "TAB096_DONE" logs/spark_tab096.log 2>/dev/null; do sleep 60; done
for S in G_tims_crosslib C_np_crosslib E_np_negonly F_np_uncovered; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
  echo "== $(date +%T) gl $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-90)"
done
echo "SEL098_DONE $(date +%T)"
