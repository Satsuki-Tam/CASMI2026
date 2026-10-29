#!/bin/bash
# 133 preparation (label-free, nothing evaluated): MIST v4 scores of the confirmation tables -- np096c (run_np096_f0conf, np096_conf093 H / N),
# np102d (run_np102_d0conf, np102_d0conf D), c1conf (run_c1bankconf_f1, c1bank_f1/c1conf) -- into experiments/mist/scores_v4_conf. Waits for the
# c1conf table build (C1CONF_DONE). Regression: np096c / np102d v4 columns mist_cos / mist_ll / n_q / status == scores_v3_conf. CPU only.
set -u
cd ~/CASMI2026 || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=4 PYTHONUTF8=1
PY=.venv-mist/bin/python; CK=data/external/mist/zenodo_23303289/mist_msg_aug.ckpt; B=experiments/b1_baseline; O=experiments/mist/scores_v4_conf; ST=$O/status.txt
until [ -s $B/run_c1bankconf_f1/c1bankconf_status.txt ]; do sleep 60; done
grep -q '^C1CONF_DONE' $B/run_c1bankconf_f1/c1bankconf_status.txt || { echo "c1conf build failed: $(cat $B/run_c1bankconf_f1/c1bankconf_status.txt)"; exit 1; }
[ -e $O ] && { echo "refused: $O exists"; exit 1; }; mkdir -p $O
[ "$(sha256sum $CK | cut -c1-64)" = "9f251d772f68315ba6fe2dc75a3b2e1ec477d3f41ffbeaf5143749157b67b177" ] || { echo "MIST4C_FAIL ckpt sha" > $ST; exit 1; }
sets_of() { .venv/bin/python -c "import glob, os, sys, pandas as pd; r, c = sys.argv[1], sys.argv[2]; s = set(pd.read_csv(c).set.astype(str)) & {os.path.basename(f)[12:-8] for f in glob.glob(r + '/b1_features_*.parquet')}; print(' '.join(sorted(s)))" $1 $2; }
sc() { local T=$1 RUN=$2 CSV=$3; local SETS=$(sets_of $RUN $CSV)
  nice -n 10 $PY -X utf8 experiments/mist/mist_score_v4.py --ckpt $CK --store data/processed/spectra_store --run $RUN --eval_csv $CSV --tag $T --sets $SETS --out $O --threads 4 > $O/mist_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) mist4 $T ($SETS) rc=$rc"; return $rc; }
FAIL=0
sc np096c $B/run_np096_f0conf $B/np096_conf093/p2_molecules.csv & P1=$!; sc np102d $B/run_np102_d0conf $B/np102_d0conf/p2_molecules.csv & P2=$!; sc c1conf $B/run_c1bankconf_f1 $B/c1bank_f1/c1conf/p2_molecules.csv & P3=$!
for p in $P1 $P2 $P3; do wait $p || FAIL=1; done
[ $FAIL -eq 0 ] || { echo "MIST4C_FAIL scoring $(date '+%F %T')" | tee $ST; exit 1; }
.venv/bin/python -X utf8 - <<'PYEOF' > $O/regression_v3conf.txt 2>&1; rc=$?
import glob, os, sys
import numpy as np, pandas as pd
bad = n = 0
for f3 in sorted(glob.glob("experiments/mist/scores_v3_conf/mist_*.parquet")):
    f4 = f3.replace("scores_v3_conf", "scores_v4_conf"); a = pd.read_parquet(f3); b = pd.read_parquet(f4)
    j = a.merge(b, on=["set", "molecule", "smiles"], how="outer", suffixes=("_3", "_4"), indicator=True, validate="one_to_one"); ok = bool((j._merge == "both").all())
    for c in ("mist_cos", "mist_ll", "n_q"): ok &= bool(np.array_equal(j[c + "_3"].values.astype(float), j[c + "_4"].values.astype(float), equal_nan=True))
    ok &= bool((j.status_3.astype(str) == j.status_4.astype(str)).all()); n += len(j); bad += int(not ok); print(os.path.basename(f3), len(j), "identical" if ok else "DIFFERENT")
print("REGRESSION", "PASS" if bad == 0 and n > 0 else "FAIL", n); sys.exit(0 if bad == 0 and n > 0 else 1)
PYEOF
[ $rc -eq 0 ] || { echo "MIST4C_FAIL regression vs v3 conf $(date '+%F %T')" | tee $ST; exit 1; }
echo "MIST4C_DONE $(date '+%F %T')" | tee $ST
