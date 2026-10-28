#!/bin/bash
# 111 EVALUATION PHASE (111_prereg_nscorer.md, amended after Codex 112 / 113). The three budgets (2,000 / 8,000 / 20,000 updates) are trained by
# spark_n111_train.sh (concurrently with the 110 FPNet training); this job starts only after BOTH training series AND the 110 evaluation, then per budget: n111_score.py on the fold-1 dev tables and the c1dev bank (N with the budget's
# checkpoint; Fs / Fm with the base fold-1 FPNet), gen_eval2fd --nscore (main = rank_v8w7a on the existing tables / the bank's own tables), the
# bank's P-only base run, and the registered reading x111_summary.py.
# Start: N111_TRAIN_DONE in experiments/n111/r1/train_status.txt (N111_TRAIN_FAIL stops) and diag/x110_status.txt = X110_DONE or X110_STAGE1_NO of
# the current 110 run (X110_FAIL or a vanished 110 job without status stops). The bank part waits for C1BANK_DONE and audits the bank's GLACIER output.
# Status line: diag/x111_status.txt.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
H=$HOME/CASMI2026; B=experiments/b1_baseline; PY=$H/.venv/bin/python; R=$H/experiments/n111/r1; F1=data/external/fpnet_fold1_as_fold0
MAN=$B/diag/x111_manifest.txt; ST=$B/diag/x111_status.txt
EXPECT_EVAL_SHA=__EXPECT_EVAL_SHA__   # sha256 of the reviewed gen_eval2fd.py (PC), written at deploy time
rm -f $ST
fail() { echo "N111_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ "$(sha256sum $B/gen_eval2fd_n111.py | cut -c1-64)" = "$EXPECT_EVAL_SHA" ] || fail "gen_eval2fd_n111.py is not the reviewed evaluator"
while [ ! -s $R/train_status.txt ]; do pgrep -f "[s]park_n111_train.sh" >/dev/null || fail "111 training job not running and no status"; sleep 120; done
grep -q "^N111_TRAIN_DONE" $R/train_status.txt || fail "111 training: $(cat $R/train_status.txt)"
while true; do
  if [ -s $B/diag/x110_status.txt ]; then grep -q -E "^X110_(DONE|STAGE1_NO|FAIL_REPRO)" $B/diag/x110_status.txt && break; fail "110 ended with a technical failure: $(cat $B/diag/x110_status.txt)"; fi
  pgrep -f "[s]park_x110.sh" >/dev/null || fail "110 job not running and no status file"
  sleep 120
done
echo "== $(date +%T) start (111 training done, 110 evaluation done)"
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
$PY -I experiments/fpnet_seed/split_audit.py $R data/external/identity_folds/structures.parquet data/external/fold_safe_fpnet 1 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "split audit rc=$rc"
: > $MAN || fail "manifest"
for f in experiments/n111/train_n111.py experiments/n111/n111_model.py experiments/n111/n111_score.py experiments/n111/ck111_check.py $R/train_manifest.txt $B/gl_classify.py $B/gen_eval2fd_n111.py $B/x111_summary.py $B/gl_audit.py $B/rank_v8w7a/lambdarank.txt \
  $F1/fpnet_fold0.pt $F1/fp_bits.npy $R/work/split.parquet $B/c1bank_f1/c1dev/p2_molecules.csv spark/jobs/spark_n111.sh; do
  h=$(sha256sum $f | cut -c1-64); [ -n "$h" ] || fail "hash $f"; echo "$h $f" >> $MAN; done
for S in 2000 8000 20000; do
  T=n111_s$S
  $PY -X utf8 experiments/n111/ck111_check.py $R $T $S $H/$F1/fpnet_fold0.pt $R/work/split.parquet $R/train_manifest.txt >> $R/ck111_check.log 2>&1 || fail "checkpoint check $T"
  h=$(sha256sum $R/${T}_s$S.pt | cut -c1-64); [ -n "$h" ] || fail "hash ckpt $T"; echo "$h $R/${T}_s$S.pt" >> $MAN
done
BST=$B/run_c1bankdev_f1/c1bank_status.txt
while [ ! -s $BST ]; do pgrep -f "[s]park_c1bank_gl.sh" >/dev/null || fail "bank GLACIER job not running and no status file"; sleep 120; done
grep -q "^C1BANK_DONE" $BST || fail "bank: $(cat $BST)"
BK=$B/run_c1bankdev_f1; BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/c1bank_f1/c1dev/p2_molecules.csv').set.unique())))")
A=""; for S in $BSETS; do A="$A $BK/b1_runner_${S}_in.json $BK/work/gl_${S}.json"; done
$H/.venv-ice/bin/python -X utf8 $B/gl_audit.py $A > $BK/gl_audit_n111.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "bank GLACIER audit rc=$rc"
SC=$H/experiments/n111/scores; mkdir -p $SC
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
for S in 2000 8000 20000; do
  CKD=$SC/s$S; mkdir -p $CKD
  for T in f1dev np053f1dev c1bankdev; do
    case $T in f1dev) RUN=$B/run_f1dev; CSV=$B/eval_set_f1/p2_molecules.csv; SETS=$S5;; np053f1dev) RUN=$B/run_np053_f1dev; CSV=$B/np053_f1dev/p2_molecules.csv; SETS=$S3;;
      c1bankdev) RUN=$BK; CSV=$B/c1bank_f1/c1dev/p2_molecules.csv; SETS=$BSETS;; esac
    $PY experiments/n111/n111_score.py --model $R/n111_s${S}_s$S.pt --base $F1/fpnet_fold0.pt --code $H/data/external/v3_models/code --bits $F1/fp_bits.npy --store data/processed/spectra_store \
      --run $RUN --eval_csv $CSV --tag $T --sets $SETS --out $CKD --workers 8 > $CKD/score_$T.log 2>&1; rc=$?
    echo "== $(date +%T) score s$S $T rc=$rc"; [ $rc -eq 0 ] || fail "score s$S $T rc=$rc"
  done
done
cd $B || exit 1
ev() { local ck=$1 tag=$2; shift 2
  $PY -X utf8 gen_eval2fd_n111.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 "$@" --fold_safe data/external/fold_safe_fpnet --views c1,c2 --out diag/r111_${ck}_$tag --workers 2 > diag/r111_${ck}_$tag.log 2>&1; local rc=$?
  echo "== $(date +%T) eval $ck $tag rc=$rc"; return $rc; }
ev base c1bankdev --run run_c1bankdev_f1 --gen run_c1bankdev_f1/gen --sets $BSETS --eval_csv c1bank_f1/c1dev/p2_molecules.csv; rc=$?; [ $rc -eq 0 ] || fail "bank base evaluation"
for S in 2000 8000 20000; do
  PIDS=()
  ev s$S f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --nscore ../n111/scores/s$S --ntag f1dev & PIDS+=($!)
  ev s$S np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv --nscore ../n111/scores/s$S --ntag np053f1dev & PIDS+=($!)
  ev s$S c1bankdev --run run_c1bankdev_f1 --gen run_c1bankdev_f1/gen --sets $BSETS --eval_csv c1bank_f1/c1dev/p2_molecules.csv --nscore ../n111/scores/s$S --ntag c1bankdev & PIDS+=($!)
  FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || fail "evaluation s$S"
done
for f in diag/r111_*.csv; do h=$(sha256sum $f | cut -c1-64); echo "$h $f" >> diag/x111_manifest.txt; done
$PY -X utf8 x111_summary.py > diag/x111_summary.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "reader rc=$rc ($(tail -1 diag/x111_summary.log | cut -c1-200))"
echo "N111_DONE $(date '+%F %T')" | tee diag/x111_status.txt
