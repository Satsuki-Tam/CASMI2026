#!/bin/bash
# 048 confirmation (pre-registered; selection ggt3t in 048_dev_selection.md; read once): conf_g_f1a (fpnet_fold1), gen_eval3 with outputs
# restricted to ggt3 (comparator) and ggt3t.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=8
PY=$HOME/CASMI2026/.venv/bin/python; F1=data/external/fpnet_fold1_as_fold0
SETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('conf_g_f1a/p2_molecules.csv').set.unique())))")
$PY -X utf8 gen_eval3.py --run run_confg_f1a --gen run_confg_f1a/gen --sets $SETS --eval_csv conf_g_f1a/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --emit_gl glgen_confg --workers 14 > diag/g048_emit_confg.log 2>&1
echo "== $(date +%T) emit exit $?"
cd ~/CASMI2026
for IN in experiments/b1_baseline/glgen_confg/gl_gen_*_in.json; do
  S=$(basename $IN _in.json | sed 's/^gl_gen_//'); OUT=experiments/b1_baseline/glgen_confg/gl_gen_${S}.json
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $IN $OUT -- --device cuda --site none --budget 3600 > experiments/b1_baseline/glgen_confg/gl_gen_${S}_resume.log 2>&1
  echo "== $(date +%T) GL $S $(grep -a '\[resume\] done' experiments/b1_baseline/glgen_confg/gl_gen_${S}_resume.log | cut -c1-90)"
done
cd experiments/b1_baseline
$PY -X utf8 gen_eval3.py --run run_confg_f1a --gen run_confg_f1a/gen --sets $SETS --eval_csv conf_g_f1a/p2_molecules.csv --fold_safe $F1 --views c1,c2,c3 --gl_gen glgen_confg/gl_gen --rules ggt3,ggt3t --out diag/g048_confg --workers 14 > diag/g048_confg.log 2>&1
echo "== $(date +%T) confirmation exit $?"
$PY - <<'PY'
import pandas as pd, numpy as np
R = pd.read_csv("diag/g048_confg.csv")
NP = [s for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered") if s in set(R.set)]
c3 = R[R.view == "c3"]
d = [(c3[c3.set == s].ggt3t - c3[c3.set == s].ggt3).mean() for s in NP]
print("C3 NP equal-weight ggt3t - ggt3: %+.4f" % np.mean(d), {s[:1]: round(float(x), 4) for s, x in zip(NP, d)})
for v in ("c1", "c2"):
    for s in sorted(R[R.view == v].set.unique()):
        x = R[(R.view == v) & (R.set == s)]; print(v, s, "n", len(x), "ggt3t - main %+.4f" % (x.ggt3t - x.main).mean(), "ggt3 - main %+.4f" % (x.ggt3 - x.main).mean())
PY
echo "GATE048_CONF_DONE $(date +%T)"
