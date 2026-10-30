#!/bin/bash
# v2 prep (156 decision): for each W135 world -> world E window (b1_ewin_world.py) -> invariants (w135_ewin_check.py) -> world E2 features
# (e2_feats_world.py) -> frozen E2 scores (e2_score_world.py). Outputs experiments/w135/v2/<world>/. Data only: no reach / truth number is
# printed (the builders' molecule tables keep labels for the registered d / c diagnostics; e-world label columns are never read).
# Usage: bash spark/jobs/spark_v2_world_e2.sh "dF1_p30 dR1_p30 ..."   (status lines in experiments/w135/v2/status.txt)
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1; L=experiments/w135/v2/status.txt; mkdir -p experiments/w135/v2
for w in $1; do
  b=${w%_p*}; O=experiments/w135/v2/$w; M=experiments/w135/worlds/$w/world_masks.json
  case $b in d*) FS=data/external/fpnet_fold1_as_fold0;; c*) FS=data/external/fpnet_fold2_as_fold0;; e*) FS=data/external/fold_safe_fpnet;; *) echo "V2_FAIL unknown batch $w" >> $L; continue;; esac
  [ -e $O/e2s_$b.parquet ] && { echo "skip $w (done)" >> $L; continue; }
  mkdir -p $O
  OMP_NUM_THREADS=1 nice -n 5 $PY -X utf8 experiments/e2/b1_ewin_world.py --eval_csv experiments/w135/batches/$b.csv --sets $b --fold_safe $FS --masks $M --out $O --workers 8 > $O/ewin.log 2>&1 || { echo "V2_FAIL ewin $w $(date '+%F %T')" >> $L; continue; }
  $PY -X utf8 experiments/e2/w135_ewin_check.py --ewin $O --masks $M --set $b > $O/check.log 2>&1 || { echo "V2_FAIL check $w $(date '+%F %T') $(head -1 $O/check.log)" >> $L; continue; }
  nice -n 5 $PY -X utf8 experiments/e2/e2_feats_world.py --ewin $O --eval_csv experiments/w135/batches/$b.csv --masks $M --sets $b --workers 8 > $O/feats.log 2>&1 || { echo "V2_FAIL feats $w $(date '+%F %T')" >> $L; continue; }
  $PY -X utf8 experiments/e2/e2_score_world.py --ewin $O --sets $b > $O/score.log 2>&1 || { echo "V2_FAIL score $w $(date '+%F %T')" >> $L; continue; }
  echo "V2_WORLD_DONE $w $(date '+%F %T') $(head -1 $O/check.log | cut -c1-60) $(sha256sum $O/e2s_$b.parquet | cut -c1-16)" >> $L
done
echo "V2_LIST_DONE $(date '+%F %T')" >> $L
