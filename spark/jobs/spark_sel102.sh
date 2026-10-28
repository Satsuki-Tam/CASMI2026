#!/bin/bash
# 102 confirmation, block B_D (102_prereg_elite.md section 6.10): fold 0, p2_select_v2 strata (exclusive E, F, C, G, D), one permutation seed 1020,
# disjoint from EVERY existing selection CSV (incl. c1cost098 raw/unused, np096_*) and the panel. Taken by FILE ORDER: D_np_single first 400 (the rest of
# the permutation stays protected for later confirmations). Then tables (b1_features, fold-safe fpnet_fold0) + GLACIER. Nothing evaluated.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python
EXCL="experiments/p1_baseline/run1/p1_molecules.csv $(ls $B/*/p1_molecules.csv $B/*/p2_molecules.csv $B/*/v2/p2_molecules.csv $B/eval_set2/p2_dev_molecules.csv 2>/dev/null | grep -v '/np102_' | tr '\n' ' ')"
echo "exclusions: $(echo $EXCL | wc -w) files"
$PY -X utf8 $B/p2_select_v2.py --census $B/eval_set2/census.parquet --store data/processed/spectra_store --folds data/external/identity_folds --exclude $EXCL \
  --n 400 --seed 1020 --fold 0 --out_dir $B/np102_raw --locked_dir $B/np102_unused > $B/np102_select.log 2>&1 || { echo "SELECT FAILED"; tail -5 $B/np102_select.log; exit 1; }
grep -a -E "^\{|_np_|_tims_|dev|locked" $B/np102_select.log | cut -c1-220 | head -20
$PY - <<'PY'
import pandas as pd, os, hashlib
B = "experiments/b1_baseline"; d = pd.read_csv(f"{B}/np102_raw/p2_molecules.csv")
out = d[d.set == "D_np_single"].head(400); os.makedirs(f"{B}/np102_d0conf", exist_ok=True); out.to_csv(f"{B}/np102_d0conf/p2_molecules.csv", index=False)
assert out.identity_group.is_unique and out.molecule.is_unique
print("np102_d0conf", len(out), out.set.value_counts().to_dict(), hashlib.sha256(open(f"{B}/np102_d0conf/p2_molecules.csv", "rb").read()).hexdigest()[:12])
PY
RUN=$B/run_np102_d0conf; mkdir -p $RUN/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/np102_d0conf/p2_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe data/external/fold_safe_fpnet --v3 data/external/v3_models/code --out $RUN --k 100 --workers 10 \
  --k_fpp 200 --k_pop 50 --dump_gen $RUN/gen --sets D_np_single > $RUN/features.log 2>&1
echo "== $(date +%T) features exit $? $(grep -a '^saved' $RUN/features.log | tr '\n' ' ' | cut -c1-240)"
.venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_D_np_single_in.json $RUN/work/gl_D_np_single.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_D_np_single_resume.log 2>&1
echo "== $(date +%T) gl D $(grep -a '\[resume\] done' $RUN/work/gl_D_np_single_resume.log | cut -c1-90)"
echo "SEL102_DONE $(date +%T)"
