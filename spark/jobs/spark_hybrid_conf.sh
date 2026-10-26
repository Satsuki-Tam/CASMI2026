#!/bin/bash
# 046 confirmation (pre-registered in 046_prereg_hybrid.md; read once): fold-2 LOCKED (run_f2lock, fpnet_fold2). ggt3h (gen_eval5, db_parents 10)
# and the comparator ggt3 (gen_eval3 = analog parents only), each with its own top-5 GL inputs, outputs restricted to ggt3h / ggt3.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
PY=$HOME/CASMI2026/.venv/bin/python; F2=data/external/fpnet_fold2_as_fold0
SETS="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
grep -q "F2LOCK_TABLES_DONE" ~/CASMI2026/logs/spark_f2lock_tables.log || { echo "HYBRID CONF FAILED: fold-2 locked tables missing"; exit 1; }
$PY -X utf8 gen_eval5.py --db_parents 10 --run run_f2lock --gen run_f2lock/gen --sets $SETS --eval_csv locked_eval_f2/p2_molecules.csv --fold_safe $F2 --views c1,c2,c3 --emit_gl glgen5_f2lock --workers 9 > diag/hybrid_emit_f2lock.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f2lock --gen run_f2lock/gen --sets $SETS --eval_csv locked_eval_f2/p2_molecules.csv --fold_safe $F2 --views c1,c2,c3 --emit_gl glgen3_f2lock --workers 9 > diag/s2ref_emit_f2lock.log 2>&1 &
wait
echo "== $(date +%T) emits done"
cd ~/CASMI2026
for D in glgen5_f2lock glgen3_f2lock; do
  for IN in experiments/b1_baseline/$D/gl_gen_*_in.json; do
    S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=experiments/b1_baseline/$D/gl_gen_${S}.json
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > experiments/b1_baseline/$D/gl_gen_${S}_resume.log 2>&1
    echo "== $(date +%T) GL $D $S $(grep -a '\[resume\] done' experiments/b1_baseline/$D/gl_gen_${S}_resume.log | cut -c1-90)"
  done
done
cd experiments/b1_baseline
$PY -X utf8 gen_eval5.py --db_parents 10 --run run_f2lock --gen run_f2lock/gen --sets $SETS --eval_csv locked_eval_f2/p2_molecules.csv --fold_safe $F2 --views c1,c2,c3 --gl_gen glgen5_f2lock/gl_gen --rules ggt3h --out diag/hybrid_f2lock --workers 9 > diag/hybrid_f2lock.log 2>&1 &
$PY -X utf8 gen_eval3.py --run run_f2lock --gen run_f2lock/gen --sets $SETS --eval_csv locked_eval_f2/p2_molecules.csv --fold_safe $F2 --views c1,c2,c3 --gl_gen glgen3_f2lock/gl_gen --rules ggt3 --out diag/s2ref_f2lock --workers 9 > diag/s2ref_f2lock.log 2>&1 &
wait
$PY - <<'PY'
import pandas as pd, numpy as np
k = ["set", "view", "molecule"]
h = pd.read_csv("diag/hybrid_f2lock.csv"); r = pd.read_csv("diag/s2ref_f2lock.csv"); m = h.merge(r, on=k, suffixes=("", "_ref"))
assert bool((m.main - m.main_ref).abs().max() < 1e-12), "main differs between the two runs"
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
c3 = m[m.view == "c3"]; d = [(c3[c3.set == s].ggt3h - c3[c3.set == s].ggt3).mean() for s in NP]
print("C3 NP equal-weight ggt3h - ggt3:", round(float(np.mean(d)), 4), {s[:1]: round(float(x), 4) for s, x in zip(NP, d)})
for v in ("c1", "c2"):
    for s in sorted(m[m.view == v].set.unique()):
        x = m[(m.view == v) & (m.set == s)]; print(v, s, "n", len(x), "ggt3h - main %+.4f" % (x.ggt3h - x.main).mean(), "ggt3 - main %+.4f" % (x.ggt3 - x.main).mean())
PY
echo "HYBRID_CONF_DONE $(date +%T)"
