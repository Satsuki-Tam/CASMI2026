#!/bin/bash
# 111 (111_prereg_nscorer.md): own spectrum-molecule scorer N, three separate training budgets (2,000 / 8,000 / 20,000 updates, each with its own
# cosine schedule), then per budget: n111_score.py on the fold-1 dev tables (N with the budget's final checkpoint, Fs with the base fold-1 FPNet),
# gen_eval2fd --nscore (main = rank_v8w7a on the existing tables, as in 102/104), and the registered reading x111_summary.py.
# Starts after the seed-1 FPNet training has ended AND the 110 tables are built (110 stage-1 output or the 110 job no longer running), so the
# GPU / CPU are not shared with the FPNet training. Exit statuses are captured right after each command.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
H=$HOME/CASMI2026; B=experiments/b1_baseline; PY=$H/.venv/bin/python; R=$H/experiments/n111/r1; F1=data/external/fpnet_fold1_as_fold0; MAN=$B/diag/x111_manifest.txt
fail() { echo "N111_FAIL $* $(date +%T)"; exit 1; }
while pgrep -f "[t]rain_fivefold.py.*--tag fpnet_f1s1" >/dev/null; do sleep 300; done
while pgrep -f "[s]park_x110.sh" >/dev/null && [ ! -s $B/diag/x110_stage1.md ]; do sleep 120; done
echo "== $(date +%T) start (FPNet training ended; 110 tables built or 110 job ended)"
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
$PY -I experiments/fpnet_seed/split_audit.py $R data/external/identity_folds/structures.parquet data/external/fold_safe_fpnet 1 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "split audit rc=$rc"
{ echo "111 $(date '+%F %T')"; for f in experiments/n111/train_n111.py experiments/n111/n111_model.py experiments/n111/n111_score.py $B/gen_eval2fd_n111.py $B/x111_summary.py $B/rank_v8w7a/lambdarank.txt \
  $F1/fpnet_fold0.pt $F1/fp_bits.npy $R/work/split.parquet; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $MAN
for S in 2000 8000 20000; do
  T=n111_s$S
  if [ ! -s $R/${T}_s$S.pt ]; then
    $PY experiments/n111/train_n111.py --code $H/data/external/v3_models/code --run $R --init $H/$F1/fpnet_fold0.pt --folds $H/data/external/identity_folds/structures.parquet \
      --tag $T --steps $S --workers 12 > $R/$T.log 2>&1; rc=$?
    echo "== $(date +%T) train $T rc=$rc"; [ $rc -eq 0 ] || fail "train $T rc=$rc"
  fi
  $PY -c "import json,sys; r=json.load(open('$R/${T}_receipt.json')); sys.exit(0 if r['complete'] and r['step']==$S else 1)" || fail "receipt $T"
  echo "$(sha256sum $R/${T}_s$S.pt | cut -c1-64) $R/${T}_s$S.pt" >> $MAN
done
SC=$H/experiments/n111/scores; mkdir -p $SC
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
for S in 2000 8000 20000; do
  CKD=$SC/s$S; mkdir -p $CKD
  for T in f1dev np053f1dev; do
    if [ $T = f1dev ]; then RUN=$B/run_f1dev; CSV=$B/eval_set_f1/p2_molecules.csv; SETS=$S5; else RUN=$B/run_np053_f1dev; CSV=$B/np053_f1dev/p2_molecules.csv; SETS=$S3; fi
    $PY experiments/n111/n111_score.py --model $R/n111_s${S}_s$S.pt --base $F1/fpnet_fold0.pt --code $H/data/external/v3_models/code --bits $F1/fp_bits.npy --store data/processed/spectra_store \
      --run $RUN --eval_csv $CSV --tag $T --sets $SETS --out $CKD --workers 8 > $CKD/score_$T.log 2>&1; rc=$?
    echo "== $(date +%T) score s$S $T rc=$rc"; [ $rc -eq 0 ] || fail "score s$S $T rc=$rc"
  done
done
cd $B || exit 1
ev() { S=$1; T=$2; shift 2
  $PY -X utf8 gen_eval2fd_n111.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 "$@" --fold_safe data/external/fold_safe_fpnet --views c1,c2 \
    --nscore ../n111/scores/s$S --ntag $T --out diag/r111_s${S}_$T --workers 2 > diag/r111_s${S}_$T.log 2>&1; rc=$?
  echo "== $(date +%T) main+N s$S $T rc=$rc"; return $rc; }
PIDS=()
for S in 2000 8000 20000; do
  ev $S f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv & PIDS+=($!)
  ev $S np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv & PIDS+=($!)
done
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || fail "evaluation"
rm -f diag/r111_*.md
for f in diag/r111_*.csv; do echo "$(sha256sum $f | cut -c1-64) $f" >> diag/x111_manifest.txt; done
$PY -X utf8 x111_summary.py > diag/x111_summary.log 2>&1; rc=$?
echo "N111_DONE reader rc=$rc $(date +%T)"
