#!/bin/bash
# 133 evaluation (133_prereg_mist_ranker.md): gen_eval2fd_m133.py (sha checked) with P = rank_v8w7a (fe61dc42) and M = rank_m133 (sha checked)
# in the SAME run (two --model / --out pairs), MIST v4 tables (experiments/mist/scores_v4). FOLD=1: f1dev / np053f1dev / c1bankdev; FOLD=2:
# f2dev / np053f2dev. Writes diag/r133[f2]_{P,M}_<tag>.csv, an input record (sha256 of every input, re-checked at the end) and a row manifest.
# The reading is x133_summary.py, run separately. CPU only.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=2 PYTHONUTF8=1
PY=$HOME/CASMI2026/.venv/bin/python; FOLD=${FOLD:-1}; SUF=""; [ "$FOLD" = 2 ] && SUF="f2"
EXP_EVAL=${EXPECT_EVAL:?set EXPECT_EVAL}; EXP_M=${EXPECT_M:?set EXPECT_M}
fail() { echo "X133_FAIL $* $(date '+%F %T')"; exit 1; }
[ "$(sha256sum gen_eval2fd_m133.py | cut -c1-64)" = "$EXP_EVAL" ] || fail "evaluator sha"
[ "$(sha256sum rank_m133/lambdarank.txt | cut -c1-64)" = "$EXP_M" ] || fail "M sha"
[ "$(sha256sum rank_v8w7a/lambdarank.txt | cut -c1-64)" = "fe61dc429bd2722363100d7a749f56cf4e4de3606fdce535f31b391c83004fe3" ] || fail "P sha"
ls diag/r133${SUF}_* diag/x133${SUF}_* >/dev/null 2>&1 && fail "outputs exist"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"; FS=data/external/fold_safe_fpnet
BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('c1bank_f1/c1dev/p2_molecules.csv').set.unique())))")
if [ "$FOLD" = 1 ]; then SPECS=("f1dev|run_f1dev|eval_set_f1/p2_molecules.csv|$S5" "np053f1dev|run_np053_f1dev|np053_f1dev/p2_molecules.csv|$S3" "c1bankdev|run_c1bankdev_f1|c1bank_f1/c1dev/p2_molecules.csv|$BSETS")
else SPECS=("f2dev|run_f2dev|eval_set_f2/p2_molecules.csv|$S5" "np053f2dev|run_np053_f2dev|np053_f2dev/p2_molecules.csv|$S3"); fi
INP=diag/x133${SUF}_inputs.txt
{ for f in gen_eval2fd_m133.py b1_rankfeats.py wf_common.py b1_locked_eval.py b1_evaluate.py b1_analog.py b1_common.py b1_rank_train.py rank_v8w7a/lambdarank.txt rank_m133/lambdarank.txt \n    rank_m133_ctrl/lambdarank.txt rank_m133/fit_roster.csv rank_m133_ctrl/fit_roster.csv rank_m133/fit_composition.json rank_m133_ctrl/fit_composition.json rank_m133/rank_results.json \n    rank_m133_ctrl/rank_results.json x133_summary.py 133_registered_versions.json ../mist/mist_validate.py ../mist/mist_qflags.py; do echo "$(sha256sum $f | cut -c1-64) $f"; done
  for spec in "${SPECS[@]}"; do IFS='|' read -r T RUN CSV SETS <<< "$spec"; echo "$(sha256sum $CSV | cut -c1-64) $CSV"
    for s in $SETS; do for f in $RUN/b1_features_$s.parquet $RUN/b1_molecules_$s.csv ../mist/scores_v4/mist_${T}_$s.parquet ../mist/scores_v4/mist_${T}_${s}_qflags.parquet; do echo "$(sha256sum $f | cut -c1-64) $f"; done
      for f in $RUN/work/gl_$s.json $RUN/work/gl_$s.json.meta.json; do [ -e $f ] && echo "$(sha256sum $f | cut -c1-64) $f"; done; done
    echo "$(sha256sum ../mist/scores_v4/mist_${T}_manifest.json | cut -c1-64) ../mist/scores_v4/mist_${T}_manifest.json"; done; } > $INP
echo "== $(date '+%F %T') x133 fold $FOLD: $(wc -l < $INP) inputs recorded"
ev() { local T=$1 RUN=$2 CSV=$3 SETS=$4
  nice -n 5 $PY -X utf8 gen_eval2fd_m133.py --model rank_v8w7a/lambdarank.txt,rank_m133/lambdarank.txt --out diag/r133${SUF}_P_$T,diag/r133${SUF}_M_$T --v7f --parents 0 \
    --run $RUN --gen $RUN/gen --sets $SETS --eval_csv $CSV --fold_safe $FS --views c1,c2 --workers 3 --mist_main ../mist/scores_v4 --mist_main_tag $T > diag/r133${SUF}_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) eval $T rc=$rc"; return $rc; }
PIDS=()
for spec in "${SPECS[@]}"; do IFS='|' read -r T RUN CSV SETS <<< "$spec"; ev "$T" "$RUN" "$CSV" "$SETS" & PIDS+=($!); done
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
[ $FAIL -eq 0 ] || fail "evaluation (see diag/r133${SUF}_<tag>.log)"
while read -r h f; do [ "$(sha256sum $f | cut -c1-64)" = "$h" ] || fail "input changed during the run: $f"; done < $INP
{ for spec in "${SPECS[@]}"; do IFS='|' read -r T RUN CSV SETS <<< "$spec"; for k in P M; do echo "$(sha256sum diag/r133${SUF}_${k}_$T.csv | cut -c1-64) diag/r133${SUF}_${k}_$T.csv"; done; done
  echo "$(sha256sum $INP | cut -c1-64) $INP"; } > diag/x133${SUF}_rows_manifest.txt
echo "X133_EVAL_DONE fold $FOLD $(date '+%F %T')"
