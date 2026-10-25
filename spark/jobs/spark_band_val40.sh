#!/bin/bash
# Codex 027: validate the band26 probe pipeline (experiments/b1_probe027, sha f9122e77) on the 40 dev2 validation molecules, both views.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; S=experiments/b1_probe027; PY=.venv/bin/python; E=$B/eval_test_val40; O=$B/eval_band_val40
echo "== $(date +%T) band validation, pipeline sha $(sha256sum $S/b1_pipeline.py | cut -c1-16)"; rm -rf $O; mkdir -p $O
for mode in c1 c2; do
  $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $O/run_$mode --workers 8 --mask_json $E/mask_$mode.json --solution $E/solution.csv --rank_model $B/rank_v4b/lambdarank.txt --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 > $O/run_$mode.log 2>&1
  echo "pipeline $mode exit $? ; $(grep -a 'OFFICIAL MRR' $O/run_$mode.log | cut -c1-110)"
  $PY -X utf8 $S/validate_band.py --run $O/run_$mode --view $mode 2>&1 | tail -3
  $PY -X utf8 experiments/b1_probe023/validate_probes.py --run $O/run_$mode --molecules experiments/b1_probe023/val40_molecules.csv --view $mode 2>&1 | tail -2
done
echo "BANDVAL_DONE $(date +%T)"
