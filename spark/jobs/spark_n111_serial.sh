#!/bin/bash
# 111 TRAINING, serial continuation (pre-set stop rule of 111_prereg_nscorer.md section 6: concurrent training stopped because the 110 FPNet ran at
# 1.14 it/s < 1.8 with two trainings, GPU-bound). Budget 2,000 finished concurrently (complete receipt, kept); budgets 8,000 and 20,000 are trained
# here, alone on the GPU, after the 110 seed-1 FPNet training has ended AND the 110 evaluation has a terminal status. Same recipe (loader 6).
# Writes experiments/n111/r1/train_status.txt = N111_TRAIN_DONE (all three budgets verified) / N111_TRAIN_FAIL <reason>.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
H=$HOME/CASMI2026; PY=$H/.venv/bin/python; R=$H/experiments/n111/r1; F1=data/external/fpnet_fold1_as_fold0; ST=$R/train_status.txt; B=experiments/b1_baseline
fail() { echo "N111_TRAIN_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
s110() { grep -a " step " experiments/fpnet_seed/f1s1/train.log | tail -1 | awk '{print $3}'; }
rm -f $ST
$PY -c "import json,sys; r=json.load(open('$R/n111_s2000_receipt.json')); sys.exit(0 if r['complete'] and r['step']==2000 and r['args']['workers']==6 else 1)" || fail "budget 2000 receipt"
for S in 8000 20000; do [ -e $R/n111_s${S}_s$S.pt ] && fail "a checkpoint of budget $S already exists (no reuse)"; done
while pgrep -f "[t]rain_fivefold.py.*--tag fpnet_f1s1" >/dev/null; do sleep 120; done
while [ ! -s $B/diag/x110_status.txt ]; do pgrep -f "[s]park_x110.sh" >/dev/null || break; sleep 120; done
echo "== $(date '+%F %T') serial 111 training start (110 status: $(cat $B/diag/x110_status.txt 2>/dev/null || echo missing))"
for S in 8000 20000; do
  T=n111_s$S; [ -e $R/$T.log ] && mv $R/$T.log $R/${T}_stopped_concurrent.log
  echo "== $(date '+%F %T') start $T (alone; 110 trainer step $(s110))"
  $PY experiments/n111/train_n111.py --code $H/data/external/v3_models/code --run $R --init $H/$F1/fpnet_fold0.pt --folds $H/data/external/identity_folds/structures.parquet \
    --tag $T --steps $S --workers 6 > $R/$T.log 2>&1; rc=$?
  echo "== $(date '+%F %T') end $T rc=$rc"; [ $rc -eq 0 ] || fail "train $T rc=$rc"
  $PY -c "import json,sys; r=json.load(open('$R/${T}_receipt.json')); sys.exit(0 if r['complete'] and r['step']==$S and r['args']['workers']==6 else 1)" || fail "receipt $T"
  echo "$(sha256sum $R/${T}_s$S.pt | cut -c1-64) $R/${T}_s$S.pt" >> $R/train_manifest.txt
done
echo "N111_TRAIN_DONE $(date '+%F %T') (2000 concurrent with the 110 training; 8000 / 20000 serial)" | tee $ST
