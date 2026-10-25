#!/bin/bash
# Hand the finished full_rk checkpoint to the Spark (Codex 021/023): waits for ALL_DONE in the local training log (or an error / the 20:45 cutoff),
# then copies full_rk_final.pt to the Spark as data/external/fpnet_fullrk_as_fold0/fpnet_fold0.pt, checks the sha256 on both ends and writes READY
# (the Spark chain spark_fullrk_chain.sh waits for it). Local use only: no training, no GPU.
R=/c/kaggle/CASMI/experiments/fpnet_full/full_rk; SSH="ssh -i $HOME/.ssh/spark_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes"; H=svlg@spark-8fda.local
for i in $(seq 1 200); do
  grep -q "ALL_DONE" $R/train.log 2>/dev/null && break
  grep -q "Traceback" $R/train.err 2>/dev/null && { echo "HANDOFF ABORT: training error"; tail -n 3 $R/train.err; exit 1; }
  [ "$(date +%H%M)" -ge 2045 ] && { echo "HANDOFF ABORT: 20:45 cutoff without ALL_DONE"; exit 1; }
  sleep 60
done
[ -s $R/full_rk_final.pt ] || { echo "HANDOFF ABORT: full_rk_final.pt missing"; ls -la $R; exit 1; }
L=$(sha256sum $R/full_rk_final.pt | cut -c1-64); echo "== $(date +%T) full_rk_final.pt sha256 $L"
scp -q -i $HOME/.ssh/spark_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes $R/full_rk_final.pt $H:CASMI2026/data/external/fpnet_fullrk_as_fold0/fpnet_fold0.pt || { echo "HANDOFF ABORT: scp failed"; exit 1; }
for f in full_rk_history.json full_rk_progress.json train.log gocheck.json launch.json query_identity_exposure.csv dropped_train_rows.json; do [ -s $R/$f ] && scp -q -i $HOME/.ssh/spark_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes $R/$f $H:CASMI2026/experiments/fpnet_full/full_rk/; done
S=$($SSH $H "sha256sum CASMI2026/data/external/fpnet_fullrk_as_fold0/fpnet_fold0.pt | cut -c1-64")
[ "$L" = "$S" ] || { echo "HANDOFF ABORT: sha mismatch local $L spark $S"; exit 1; }
$SSH $H "echo 'full_rk_final.pt sha256 $L copied $(date +%FT%T)' > CASMI2026/data/external/fpnet_fullrk_as_fold0/READY"
echo "HANDOFF_DONE $(date +%T) sha $L"
