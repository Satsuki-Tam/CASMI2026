#!/bin/bash
# 110 (110_prereg_fpseed.md section 3-4, after Codex 110 / 112): waits for the seed-1 fold-1 FPNet job to end, then
#  1. completion check (ckpt_check.py) + split audit (split_audit.py) + fold-1 slot / bits asserts; any failure stops;
#  2. builds the fold-1 dev tables twice with the same code on the same system: control = seed 0 alone (run_*_s0rep), FPavg = + --extra_ckpts
#     <seed-1 final> (run_*_fpavg); same arguments as spark_fold1_sets.sh / spark_np053_sets.sh; table identity vs the existing tables recorded;
#  3. stage-1 reading (x110_stage1.py); only on PASS: GLACIER through ONE candidate-level cache (gl_share.py: existing run -> control ->
#     FPavg; only uncovered candidates are computed), the GLACIER audit (gl_audit.py) as a STOP gate, the v8w7a main (gen_eval2fd --v7f, as in
#     102/104) for both arms, and the stage-3 reading (x110_stage3.py).
# Final status line in diag/x110_status.txt: X110_DONE / X110_STAGE1_NO / X110_FAIL <reason>; the job exits non-zero on any technical failure.
# Exit statuses are captured right after each command (rc=$?), never after a $(...) substitution.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; R=experiments/fpnet_seed/f1s1; CK=$R/fpnet_f1s1_final.pt
F1=data/external/fpnet_fold1_as_fold0; FS=data/external/fold_safe_fpnet; MAN=$B/diag/x110_manifest.txt; ST=$B/diag/x110_status.txt
rm -f $ST
fail() { echo "X110_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
while pgrep -f "[s]park_fpnet_f1s1.sh" >/dev/null || pgrep -f "[t]rain_fivefold.py.*--tag fpnet_f1s1" >/dev/null; do sleep 300; done
echo "== $(date +%T) training job ended"
while pgrep -f "[s]park_n111_train.sh" >/dev/null; do sleep 120; done   # Codex 113: evaluations run after BOTH training series
echo "== $(date +%T) 111 training phase not running"
$PY -I experiments/fpnet_seed/ckpt_check.py $R fpnet_f1s1 82855 1 > $R/ckpt_check.log 2>&1; rc=$?; grep -a -E "^(PASS|FAIL)" $R/ckpt_check.log; [ $rc -eq 0 ] || fail "completion check rc=$rc"
$PY -I experiments/fpnet_seed/split_audit.py $R data/external/identity_folds/structures.parquet $FS 1 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "split audit rc=$rc"
[ "$(realpath $F1/fpnet_fold0.pt)" = "$(realpath $FS/fpnet_fold1.pt)" ] || fail "fold-1 slot does not point to the public fpnet_fold1"
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
[ "$(sha256sum $F1/fp_bits.npy | cut -c1-64)" = "c3869e86449d6fed6e79e9655f8a7d35bd55c3138ecddfc1dae5072627e78677" ] || fail "fp_bits sha"
: > $MAN || fail "manifest"
for f in $CK $F1/fpnet_fold0.pt $F1/fp_bits.npy $B/b1_features.py $B/gen_eval2fd.py $B/x110_stage1.py $B/x110_stage3.py $B/gl_share.py $B/gl_audit.py $B/rank_v8w7a/lambdarank.txt \
  $B/eval_set_f1/p2_molecules.csv $B/np053_f1dev/p2_molecules.csv experiments/fpnet_seed/ckpt_check.py experiments/fpnet_seed/split_audit.py spark/jobs/spark_x110.sh; do
  h=$(sha256sum $f | cut -c1-64); [ -n "$h" ] || fail "hash $f"; echo "$h $f" >> $MAN; done
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
COMMON="--store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --k 100 --workers 8 --k_fpp 200 --k_pop 50"
feat() { local name=$1 csv=$2 sets=$3; shift 3
  case "$name" in run_f1dev_s0rep|run_f1dev_fpavg|run_np053f1dev_s0rep|run_np053f1dev_fpavg) ;; *) echo "bad run name '$name'"; return 1;; esac
  local run=$B/$name; rm -rf "$run"; mkdir -p $run/work
  $PY -X utf8 $B/b1_features.py --eval_csv $csv $COMMON --out $run --dump_gen $run/gen --sets $sets "$@" > $run/features.log 2>&1; local rc=$?
  echo "== $(date +%T) features $name rc=$rc"; [ $rc -eq 0 ] || return 1
  for S in $sets; do { [ -s $run/b1_molecules_$S.csv ] && [ -s $run/b1_features_$S.parquet ] && [ -s $run/b1_runner_${S}_in.json ]; } || return 1; done; [ -s $run/b1_features_manifest.json ]; }
for T in f1dev np053f1dev; do
  if [ $T = f1dev ]; then CSV=$B/eval_set_f1/p2_molecules.csv; SETS=$S5; else CSV=$B/np053_f1dev/p2_molecules.csv; SETS=$S3; fi
  feat run_${T}_s0rep $CSV "$SETS" & P0=$!
  feat run_${T}_fpavg $CSV "$SETS" --extra_ckpts $CK & P1=$!
  wait $P0; r0=$?; wait $P1; r1=$?; { [ $r0 -eq 0 ] && [ $r1 -eq 0 ]; } || fail "features $T ($r0 / $r1)"
done
$PY -X utf8 - > $B/diag/x110_table_identity.txt 2>&1 <<'EOF'
import pandas as pd
B = "experiments/b1_baseline"
for new, old, sets in (("run_f1dev_s0rep", "run_f1dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]), ("run_np053f1dev_s0rep", "run_np053_f1dev", ["NP_H", "NP_X", "NP_N"])):
    for s in sets:
        a = pd.read_parquet(f"{B}/{new}/b1_features_{s}.parquet"); b = pd.read_parquet(f"{B}/{old}/b1_features_{s}.parquet")
        same_cols = list(a.columns) == list(b.columns); same = same_cols and len(a) == len(b) and a.reset_index(drop=True).equals(b.reset_index(drop=True))
        print(f"{new} vs {old} {s}: rows {len(a)} / {len(b)}, identical={same}")
EOF
( cd $B && $PY -X utf8 x110_stage1.py > diag/x110_stage1.log 2>&1 ); rc=$?; [ $rc -eq 0 ] || fail "stage-1 reader rc=$rc"
grep -q "gate PASS" $B/diag/x110_stage1.md || { echo "X110_STAGE1_NO $(date '+%F %T')" | tee $ST; exit 0; }
echo "== $(date +%T) stage 1 PASS -> GLACIER (shared cache) + audit + main for both arms"
gl() { local arm=$1 tag=$2 S=$3; shift 3   # remaining args: cache IN:OUT pairs
  local run=$B/run_${tag}_$arm w=$B/run_${tag}_$arm/work
  $PY -X utf8 $B/gl_share.py prepare --inp $run/b1_runner_${S}_in.json --cache "$@" --todo $w/gl_${S}_todo_in.json --plan $w/gl_${S}_plan.json > $w/gl_${S}_share.log 2>&1 || return 1
  if [ "$($PY -c "import json; print(len(json.load(open('$w/gl_${S}_todo_in.json'))))")" != "0" ]; then
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $w/gl_${S}_todo_in.json $w/gl_${S}_todo_out.json -- --device cuda --site none --budget 7200 > $w/gl_${S}_resume.log 2>&1 || return 1
  fi
  $PY -X utf8 $B/gl_share.py merge --inp $run/b1_runner_${S}_in.json --plan $w/gl_${S}_plan.json --todo_out $w/gl_${S}_todo_out.json --out $w/gl_${S}.json >> $w/gl_${S}_share.log 2>&1 || return 1
  $PY -X utf8 $B/gl_audit.py $run/b1_runner_${S}_in.json $w/gl_${S}.json >> $w/gl_${S}_share.log 2>&1; }
for T in f1dev np053f1dev; do
  if [ $T = f1dev ]; then SETS=$S5; OLD=$B/run_f1dev; else SETS=$S3; OLD=$B/run_np053_f1dev; fi
  for S in $SETS; do
    gl s0rep $T $S $OLD/b1_runner_${S}_in.json:$OLD/work/gl_${S}.json; rc=$?; echo "== $(date +%T) gl s0rep $T $S rc=$rc $(tail -1 $B/run_${T}_s0rep/work/gl_${S}_share.log | cut -c1-150)"; [ $rc -eq 0 ] || fail "GL control $T $S"
    C0=$B/run_${T}_s0rep
    gl fpavg $T $S $OLD/b1_runner_${S}_in.json:$OLD/work/gl_${S}.json $C0/b1_runner_${S}_in.json:$C0/work/gl_${S}.json; rc=$?; echo "== $(date +%T) gl fpavg $T $S rc=$rc $(tail -1 $B/run_${T}_fpavg/work/gl_${S}_share.log | cut -c1-150)"; [ $rc -eq 0 ] || fail "GL FPavg $T $S"
  done
done
cd $B || exit 1
ev() { local arm=$1 tag=$2; shift 2
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --run run_${tag}_$arm --gen run_${tag}_$arm/gen "$@" --fold_safe $FS --views c1,c2 --out diag/r110_${arm}_$tag --workers 2 > diag/r110_${arm}_$tag.log 2>&1; local rc=$?
  echo "== $(date +%T) main $arm $tag rc=$rc"; return $rc; }
PIDS=()
for A in s0rep fpavg; do
  ev $A f1dev --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv & PIDS+=($!)
  ev $A np053f1dev --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv & PIDS+=($!)
done
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || fail "main evaluation"
for f in diag/r110_*.csv; do echo "$(sha256sum $f | cut -c1-64) $f" >> diag/x110_manifest.txt; done
$PY -X utf8 x110_stage3.py > diag/x110_stage3.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "stage-3 reader rc=$rc ($(tail -1 diag/x110_stage3.log | cut -c1-200))"
echo "X110_DONE $(date '+%F %T')" | tee diag/x110_status.txt
