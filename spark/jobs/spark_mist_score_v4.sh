#!/bin/bash
# 133 (Codex 131 Q2, MIST-feature ranker pair): MIST v4 per-candidate scores (mist_score_v4.py = v3 + assignment-quality columns) for the v8w7a
# training runs and the development tables; label-free. Regression gate: on the five development tags scored by v3 (experiments/mist/scores_v3)
# the v4 columns mist_cos / mist_ll / n_q / status must be identical row by row. CPU only (4 threads per table, 3 tables at a time, nice 10).
set -u
cd ~/CASMI2026 || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=4 PYTHONUTF8=1
PY=.venv-mist/bin/python; CK=data/external/mist/zenodo_23303289/mist_msg_aug.ckpt; B=experiments/b1_baseline; O=experiments/mist/scores_v4; ST=$O/status.txt
[ -e $O ] && { echo "refused: $O exists"; exit 1; }; mkdir -p $O
[ "$(sha256sum $CK | cut -c1-64)" = "9f251d772f68315ba6fe2dc75a3b2e1ec477d3f41ffbeaf5143749157b67b177" ] || { echo "MIST4_FAIL ckpt sha" > $ST; exit 1; }
sets_of() { .venv/bin/python -c "import glob, os, sys, pandas as pd; r, c = sys.argv[1], sys.argv[2]; s = set(pd.read_csv(c).set.astype(str)) & {os.path.basename(f)[12:-8] for f in glob.glob(r + '/b1_features_*.parquet')}; print(' '.join(sorted(s)))" $1 $2; }
sc() { local T=$1 RUN=$2 CSV=$3; local SETS=$(sets_of $RUN $CSV)
  [ -n "$SETS" ] || { echo "== $(date +%T) mist4 $T: no sets"; return 1; }
  nice -n 10 $PY -X utf8 experiments/mist/mist_score_v4.py --ckpt $CK --store data/processed/spectra_store --run $RUN --eval_csv $CSV --tag $T --sets $SETS --out $O --threads 4 > $O/mist_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) mist4 $T ($SETS) rc=$rc"; return $rc; }
FAIL=0
wave() { local P=(); for spec in "$@"; do IFS=: read -r T RUN CSV <<< "$spec"; sc $T $RUN $CSV & P+=($!); done; for p in "${P[@]}"; do wait $p || FAIL=1; done; }
wave "tr_v3p1:$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv" "tr_v3eval:$B/run_v3_eval:$B/eval_set/p1_molecules.csv" "tr_v3c1:$B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
wave "tr_f3a:$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv" "tr_f4a:$B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv" "panel:$B/run_panel_fe:$B/panel_np250/p1_molecules.csv"
wave "f1dev:$B/run_f1dev:$B/eval_set_f1/p2_molecules.csv" "np053f1dev:$B/run_np053_f1dev:$B/np053_f1dev/p2_molecules.csv" "c1bankdev:$B/run_c1bankdev_f1:$B/c1bank_f1/c1dev/p2_molecules.csv"
wave "f2dev:$B/run_f2dev:$B/eval_set_f2/p2_molecules.csv" "np053f2dev:$B/run_np053_f2dev:$B/np053_f2dev/p2_molecules.csv"
[ $FAIL -eq 0 ] || { echo "MIST4_FAIL scoring $(date '+%F %T')" | tee $ST; exit 1; }
.venv/bin/python -X utf8 - <<'PYEOF' > $O/regression_v3.txt 2>&1; rc=$?
import glob, os, sys
import numpy as np, pandas as pd
bad = 0; n = 0
for f3 in sorted(glob.glob("experiments/mist/scores_v3/mist_*.parquet")):
    f4 = f3.replace("scores_v3", "scores_v4"); a = pd.read_parquet(f3); b = pd.read_parquet(f4)
    k = ["set", "molecule", "smiles"]; j = a.merge(b, on=k, how="outer", suffixes=("_3", "_4"), indicator=True, validate="one_to_one")
    ok = (j._merge == "both").all()
    for c in ("mist_cos", "mist_ll", "n_q"): ok &= bool(np.array_equal(j[c + "_3"].values.astype(float), j[c + "_4"].values.astype(float), equal_nan=True))
    ok &= bool((j.status_3.astype(str) == j.status_4.astype(str)).all())
    n += len(j); bad += int(not ok); print(os.path.basename(f3), len(j), "identical" if ok else "DIFFERENT")
print("REGRESSION", "PASS" if bad == 0 and n > 0 else "FAIL", n, "rows")
sys.exit(0 if bad == 0 and n > 0 else 1)
PYEOF
[ $rc -eq 0 ] || { echo "MIST4_FAIL regression vs v3 (see $O/regression_v3.txt) $(date '+%F %T')" | tee $ST; exit 1; }
echo "MIST4_DONE $(date '+%F %T')" | tee $ST
