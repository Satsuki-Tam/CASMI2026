#!/bin/bash
# 111 TRAINING PHASE ONLY (Codex 113: concurrent with the 110 seed-1 FPNet training; evaluation phases run afterwards, serially).
# Three separate budgets (2,000 / 8,000 / 20,000 updates, each with its own cosine schedule), loader workers 6 (formal condition for all three;
# never changed when the 110 training ends). Records start / end times, the 110 trainer's step at each start / end, memory / swap / GPU every
# 10 minutes (spark/jobs/spark_n111_train.mon). A run is one inherently non-deterministic trial of a fixed recipe / data / update count (no claim
# of reproducing identical weights). Status line: experiments/n111/r1/train_status.txt (N111_TRAIN_DONE / N111_TRAIN_FAIL <reason>).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
H=$HOME/CASMI2026; PY=$H/.venv/bin/python; R=$H/experiments/n111/r1; F1=data/external/fpnet_fold1_as_fold0; ST=$R/train_status.txt; MON=spark/jobs/spark_n111_train.mon
rm -f $ST
fail() { echo "N111_TRAIN_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
s110() { grep -a " step " experiments/fpnet_seed/f1s1/train.log | tail -1 | awk '{print $3}'; }
for S in 2000 8000 20000; do [ -e $R/n111_s${S}_s$S.pt ] && fail "a checkpoint of budget $S already exists (no reuse)"; done
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
$PY -I experiments/fpnet_seed/split_audit.py $R data/external/identity_folds/structures.parquet data/external/fold_safe_fpnet 1 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "split audit rc=$rc"
{ echo "111 training phase $(date '+%F %T')"; for f in experiments/n111/train_n111.py experiments/n111/n111_model.py $F1/fpnet_fold0.pt $F1/fp_bits.npy $R/work/split.parquet spark/jobs/spark_n111_train.sh; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $R/train_manifest.txt
( while true; do echo "$(date '+%F %T') 110step $(s110) | $(free -g | awk '/Mem/{print "mem used "$3" avail "$7}') | $(free -g | awk '/Swap/{print "swap used "$3}') | gpu $(nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader | tr -d ' ')"; sleep 600; done ) >> $MON 2>&1 &
MONPID=$!
for S in 2000 8000 20000; do
  T=n111_s$S; echo "== $(date '+%F %T') start $T (110 trainer step $(s110))"
  $PY experiments/n111/train_n111.py --code $H/data/external/v3_models/code --run $R --init $H/$F1/fpnet_fold0.pt --folds $H/data/external/identity_folds/structures.parquet \
    --tag $T --steps $S --workers 6 > $R/$T.log 2>&1; rc=$?
  echo "== $(date '+%F %T') end $T rc=$rc (110 trainer step $(s110))"; [ $rc -eq 0 ] || { kill $MONPID; fail "train $T rc=$rc"; }
  $PY -c "import json,sys; r=json.load(open('$R/${T}_receipt.json')); sys.exit(0 if r['complete'] and r['step']==$S and r['args']['workers']==6 else 1)" || { kill $MONPID; fail "receipt $T"; }
  echo "$(sha256sum $R/${T}_s$S.pt | cut -c1-64) $R/${T}_s$S.pt" >> $R/train_manifest.txt
done
kill $MONPID
echo "N111_TRAIN_DONE $(date '+%F %T')" | tee $ST
