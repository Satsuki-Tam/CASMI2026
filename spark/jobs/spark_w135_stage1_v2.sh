#!/bin/bash
# W135 stage 1 v2 (136_decision.md; Codex 136): full-mode generation of the six design worlds at pi3 = 0.3 with w135_gen_v2.py, then the
# registered reader w135_read_v2.py --decide. Before any generation: every world must be built by the v2 rebuild (status line), its manifest must
# verify, and the run manifest (code, arguments, world manifests) is written; after: output hashes and exit values.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1; PI=30; RM=experiments/w135/stage1_v2_run_manifest.txt
fail() { echo "W135_STAGE1_V2_FAIL $* $(date '+%F %T')" | tee -a $RM; exit 1; }
[ -e $RM ] && fail "run manifest exists (stage 1 v2 already started)"
for b in dF1 dF2 dF3 dR1 dR2 dR3; do
  W=experiments/w135/worlds/${b}_p$PI
  grep -q "W135_WORLD_DONE $b p$PI" experiments/w135/worlds/status.txt || fail "world $b p$PI not built"
  [ -e $W/gen_full_v2.parquet ] && fail "$b full table exists"
  while read -r h f; do [ "$(sha256sum $f | cut -c1-64)" = "$h" ] || fail "$f differs from the $b world manifest"; done < $W/manifest.txt
  $PY -c "import pandas as pd; F = pd.read_parquet('$W/P.parquet'); assert {'set', 'molecule', 'main', 'rP', 'top25', 'analogs'} <= set(F.columns)" || fail "$b P schema"
done
{ echo "stage1 v2 $(date '+%F %T') pi $PI budget 50 n_train 10 n_peer 10 workers 16 fold_safe data/external/fpnet_fold1_as_fold0"
  for f in experiments/w135/w135_gen_v2.py experiments/w135/w135_read_v2.py experiments/b1_baseline/b1_gen.py experiments/b1_baseline/b1_analog.py experiments/b1_baseline/b1_common.py \
    data/external/fpnet_fold1_as_fold0/fp_bits.npy experiments/w135/batches/d_manifest_v2.json; do echo "$(sha256sum $f | cut -c1-64) $f"; done
  for b in dF1 dF2 dF3 dR1 dR2 dR3; do echo "$(sha256sum experiments/w135/worlds/${b}_p$PI/manifest.txt | cut -c1-64) experiments/w135/worlds/${b}_p$PI/manifest.txt"; done; } > $RM
for b in dF1 dF2 dF3 dR1 dR2 dR3; do
  ( cd experiments/b1_baseline && $PY -X utf8 ../w135/w135_gen_v2.py --batch ../w135/batches/$b.csv --wclass_col wclass_p$PI --world ../w135/worlds/${b}_p$PI --set $b \
    --fold_safe data/external/fpnet_fold1_as_fold0 --out ../w135/worlds/${b}_p$PI/gen_full_v2 --workers 16 ) > experiments/w135/worlds/${b}_p$PI/gen_full_v2.log 2>&1; rc=$?
  echo "gen $b exit $rc $(sha256sum experiments/w135/worlds/${b}_p$PI/gen_full_v2.parquet 2>/dev/null | cut -c1-64)" >> $RM
  [ $rc -eq 0 ] || fail "gen $b (see the world's gen_full_v2.log)"
done
$PY -X utf8 experiments/w135/w135_read_v2.py --pi $PI --decide > experiments/w135/stage1_v2_p$PI.log 2>&1; rc=$?
echo "reader exit $rc" >> $RM
[ $rc -eq 0 ] || fail "reader"
echo "W135_STAGE1_V2_DONE $(date '+%F %T')" | tee -a $RM
