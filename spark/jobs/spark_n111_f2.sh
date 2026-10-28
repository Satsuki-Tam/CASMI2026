#!/bin/bash
# 111 FOLD-2 REPLICATION (111_prereg_nscorer.md section 4; only if a budget passed on fold 1). Usage: bash spark_n111_f2.sh <selected budget>
# Same recipe with everything moved to fold 2 (Codex 111 / 116): init = public fpnet_fold2 (fold-2 slot), run n111/r2 (split: fold 2 + NP examples
# held out, audited), the SAME budget (never re-selected on fold 2), the same fixed connection; tables f2dev / np053f2dev (existing, fold-2 FPNet,
# stored GLACIER, baseline diag/r102_*) and the fold-2 C1 bank (c1bank_f2 c1dev, tables built here with the fold-2 slot; never the fold-1 bank).
# Reader: x111_summary.py --fold 2 --cks s<budget> (same gate on its own; no pooling with fold 1). Status: diag/x111f2_status.txt.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
S=${1:?budget}; H=$HOME/CASMI2026; B=experiments/b1_baseline; PY=$H/.venv/bin/python; PYI=$H/.venv-ice/bin/python; R=$H/experiments/n111/r2
F2=data/external/fpnet_fold2_as_fold0; SLOT2=257062cb6ece3332
ST=$H/$B/diag/x111f2_status.txt; MAN=$H/$B/diag/x111f2_manifest.txt; rm -f $ST
fail() { echo "N111F2_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ "$(sha256sum $F2/fpnet_fold0.pt | cut -c1-16)" = "$SLOT2" ] || fail "fold-2 slot sha"
FULL2=$(sha256sum $F2/fpnet_fold0.pt | cut -c1-64)
$PY -I experiments/fpnet_seed/split_audit.py $R data/external/identity_folds/structures.parquet data/external/fold_safe_fpnet 2 > $R/split_audit.log 2>&1 || fail "split audit fold 2"
T=n111f2_s$S; [ -e $R/${T}_s$S.pt ] && fail "checkpoint exists (no reuse)"
{ echo "111 fold 2 budget $S $(date '+%F %T')"; for f in experiments/n111/train_n111.py experiments/n111/n111_model.py $F2/fpnet_fold0.pt $F2/fp_bits.npy $R/work/split.parquet spark/jobs/spark_n111_f2.sh; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $R/train_manifest.txt
$PY experiments/n111/train_n111.py --code $H/data/external/v3_models/code --run $R --init $H/$F2/fpnet_fold0.pt --folds $H/data/external/identity_folds/structures.parquet \
  --tag $T --steps $S --workers 6 > $R/$T.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "train rc=$rc"
echo "$(sha256sum $R/${T}_s$S.pt | cut -c1-64) $R/${T}_s$S.pt" >> $R/train_manifest.txt
$PY -X utf8 experiments/n111/ck111_check.py $R $T $S $H/$F2/fpnet_fold0.pt $R/work/split.parquet $R/train_manifest.txt $FULL2 > $R/ck111_check.log 2>&1 || fail "checkpoint check"
# fold-2 C1 bank (development half) tables + GLACIER + audit
CSV=$B/c1bank_f2/c1dev/p2_molecules.csv; BK=$B/run_c1bankdev_f2; BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$CSV').set.unique())))")
rm -rf $BK; mkdir -p $BK/work
$PY -X utf8 $B/b1_features.py --eval_csv $CSV --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F2 --v3 data/external/v3_models/code --out $BK --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --dump_gen $BK/gen --sets $BSETS > $BK/features.log 2>&1 || fail "bank features"
A=""
for SS in $BSETS; do
  .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $BK/b1_runner_${SS}_in.json $BK/work/gl_${SS}.json -- --device cuda --site none --budget 7200 > $BK/work/gl_${SS}_resume.log 2>&1 || fail "bank gl $SS"
  A="$A $BK/b1_runner_${SS}_in.json $BK/work/gl_${SS}.json"
done
for SS in C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib; do A="$A $B/run_f2dev/b1_runner_${SS}_in.json $B/run_f2dev/work/gl_${SS}.json"; done
for SS in NP_H NP_X NP_N; do A="$A $B/run_np053_f2dev/b1_runner_${SS}_in.json $B/run_np053_f2dev/work/gl_${SS}.json"; done
$PYI -X utf8 $B/gl_audit.py $A > $BK/gl_audit_f2.log 2>&1 || fail "GLACIER audit (fold-2 tables / bank)"
# scores and evaluation
SC=$H/experiments/n111/scores_f2/s$S; mkdir -p $SC
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
for TG in f2dev np053f2dev c1bankf2dev; do
  case $TG in f2dev) RUN=$B/run_f2dev; ECSV=$B/eval_set_f2/p2_molecules.csv; SETS=$S5;; np053f2dev) RUN=$B/run_np053_f2dev; ECSV=$B/np053_f2dev/p2_molecules.csv; SETS=$S3;; c1bankf2dev) RUN=$BK; ECSV=$CSV; SETS=$BSETS;; esac
  $PY experiments/n111/n111_score.py --model $R/${T}_s$S.pt --base $F2/fpnet_fold0.pt --code $H/data/external/v3_models/code --bits $F2/fp_bits.npy --store data/processed/spectra_store \
    --run $RUN --eval_csv $ECSV --tag $TG --sets $SETS --out $SC --workers 8 > $SC/score_$TG.log 2>&1 || fail "score $TG"
done
cd $B || exit 1
ev() { local ck=$1 tag=$2; shift 2
  $PY -X utf8 gen_eval2fd_n111.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 "$@" --fold_safe data/external/fold_safe_fpnet --views c1,c2 --out diag/r111f2_${ck}_$tag --workers 2 > diag/r111f2_${ck}_$tag.log 2>&1; }
ev base c1bankf2dev --run run_c1bankdev_f2 --gen run_c1bankdev_f2/gen --sets $BSETS --eval_csv c1bank_f2/c1dev/p2_molecules.csv || fail "bank base evaluation"
PIDS=()
ev s$S f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --nscore ../n111/scores_f2/s$S --ntag f2dev & PIDS+=($!)
ev s$S np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets $S3 --eval_csv np053_f2dev/p2_molecules.csv --nscore ../n111/scores_f2/s$S --ntag np053f2dev & PIDS+=($!)
ev s$S c1bankf2dev --run run_c1bankdev_f2 --gen run_c1bankdev_f2/gen --sets $BSETS --eval_csv c1bank_f2/c1dev/p2_molecules.csv --nscore ../n111/scores_f2/s$S --ntag c1bankf2dev & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || fail "evaluation"
for f in diag/r111f2_*.csv; do echo "$(sha256sum $f | cut -c1-64) $f" >> $MAN; done
$PY -X utf8 x111_summary.py --fold 2 --cks s$S > diag/x111f2_summary.log 2>&1 || fail "reader ($(tail -1 diag/x111f2_summary.log | cut -c1-200))"
echo "N111F2_DONE $(date '+%F %T')" | tee $ST
