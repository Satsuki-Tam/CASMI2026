#!/bin/bash
# 115 v2 evaluation (115_plan.md "読み取りの固定", Codex 118 / 119; written before any R / A model exists). Started by hand once BOTH arms passed
# their completion checks and the GPU is otherwise idle (the gate below refuses otherwise):
#  1. slot dirs data/external/e115_slot_{r,a}: fpnet_fold0.pt -> the arm's final checkpoint, fp_bits.npy -> the public bits (P0 = the public fold-1
#     slot data/external/fpnet_fold1_as_fold0, sha 1739d568...); every slot checkpoint is loaded once with the evaluator's loader before any table;
#  2. the fold-1 dev tables three times with the same code on the same system: run_<tag>_{p0,r,a}e115 for tag f1dev / np053f1dev / c1bankdev, the
#     arguments of spark_x110.sh / spark_c1bank.sh with only --fold_safe differing; P0 vs the existing tables recorded (diag/x115_table_identity.txt);
#  3. stage 1 (x115_stage1.py, FP proxy, gate A - R > 0 AND A - P0 > 0); only on PASS:
#  4. GLACIER through ONE candidate-level cache per tag (gl_share.py: existing run -> P0 -> R -> A; only uncovered candidates are computed) with the
#     GLACIER audit (gl_audit.py) as a STOP gate; the v8w7a main (gen_eval2fd --v7f, as in 110) for the three arms -> diag/r115_<arm>_<tag>.csv;
#  5. stage 3 (x115_stage3.py; exit 2 = P0 does not reproduce the existing main -> X115_FAIL_REPRO, no difference computed).
# Final status line in diag/x115_status.txt: X115_DONE / X115_STAGE1_NO / X115_FAIL <reason> / X115_FAIL_REPRO. Exit statuses are captured right
# after each command (rc=$?), never after a $(...) substitution. Usage: nohup bash spark/jobs/spark_x115.sh > spark/jobs/spark_x115.out 2>&1 &
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
H=$HOME/CASMI2026; B=experiments/b1_baseline; E=experiments/e115; PY=$H/.venv/bin/python; PYI=$H/.venv-ice/bin/python
F1=data/external/fpnet_fold1_as_fold0; FS=data/external/fold_safe_fpnet; MAN=$H/$B/diag/x115_manifest.txt; ST=$H/$B/diag/x115_status.txt   # absolute: fail() is also called after cd $B
for p in "[s]park_x110" "[s]park_n111" "[t]rain_n111.py" "[t]rain_fivefold.py" "[s]park_fpnet_f2s1" "[s]park_c1bank" "[g]l_runner.py" "[g]en_eval2fd" "[t]rain_fpaug2.py" "[s]park_e115_train"; do
  if pgrep -f "$p" >/dev/null; then echo "refused: '$p' is running ($(date '+%F %T'))"; exit 1; fi; done
rm -f $ST
fail() { echo "X115_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
grep -q "^E115_R_DONE" $E/runR/status.txt 2>/dev/null || fail "arm R has no E115_R_DONE"
grep -q "^E115_A_DONE" $E/runA/status.txt 2>/dev/null || fail "arm A has no E115_A_DONE"
$PY -c "import json, sys; sys.exit(0 if all(json.load(open(p)).get('passed') is True for p in sys.argv[1:]) else 1)" $E/runR/e115R_ck115.json $E/runA/e115A_ck115.json; rc=$?
[ $rc -eq 0 ] || fail "completion checks not passed"
[ "$(realpath $F1/fpnet_fold0.pt)" = "$(realpath $FS/fpnet_fold1.pt)" ] || fail "fold-1 slot does not point to the public fpnet_fold1"
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
[ "$(sha256sum $F1/fp_bits.npy | cut -c1-64)" = "c3869e86449d6fed6e79e9655f8a7d35bd55c3138ecddfc1dae5072627e78677" ] || fail "fp_bits sha"
for arm in r a; do
  if [ $arm = r ]; then CKP=$H/$E/runR/e115R_final.pt; else CKP=$H/$E/runA/e115A_final.pt; fi
  SL=data/external/e115_slot_$arm
  if [ -e $SL ]; then   # an existing slot must point exactly to this arm's final checkpoint and the public bits
    { [ "$(realpath $SL/fpnet_fold0.pt)" = "$(realpath $CKP)" ] && [ "$(realpath $SL/fp_bits.npy)" = "$(realpath $FS/fp_bits.npy)" ]; } || fail "slot $SL points elsewhere"
  else
    mkdir -p $SL && ln -s $CKP $SL/fpnet_fold0.pt && ln -s $H/$FS/fp_bits.npy $SL/fp_bits.npy || fail "slot $SL"
  fi
done
$PY -X utf8 -c "import sys; sys.path.insert(0, sys.argv[1]); from casmi import fpnet; [fpnet.load_model(p, 'cpu') for p in sys.argv[2:]]; print('slot checkpoints load:', len(sys.argv) - 2)" \
  $H/data/external/v3_models/code $F1/fpnet_fold0.pt data/external/e115_slot_r/fpnet_fold0.pt data/external/e115_slot_a/fpnet_fold0.pt; rc=$?
[ $rc -eq 0 ] || fail "slot checkpoints do not load with the evaluator's loader"
: > $MAN || fail "manifest"
for f in $E/runR/e115R_final.pt $E/runA/e115A_final.pt $E/runR/e115R_ck115.json $E/runA/e115A_ck115.json $F1/fpnet_fold0.pt $F1/fp_bits.npy $B/b1_features.py $B/gen_eval2fd.py \
  $B/x115_stage1.py $B/x115_stage3.py $B/gl_share.py $B/gl_audit.py data/external/glacier/gl_runner.py data/external/glacier/ckpt/glacier.pt $B/rank_v8w7a/lambdarank.txt \
  $B/eval_set_f1/p2_molecules.csv $B/np053_f1dev/p2_molecules.csv $B/c1bank_f1/c1dev/p2_molecules.csv $E/mall/jobs_pid.npy $E/runA/e115A_consumed_jobs.npy spark/jobs/spark_x115.sh; do
  h=$(sha256sum $f | cut -c1-64); [ -n "$h" ] || fail "hash $f"; echo "$h $f" >> $MAN; done
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
BCSV=$B/c1bank_f1/c1dev/p2_molecules.csv; BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$BCSV').set.unique())))")
[ -n "$BSETS" ] || fail "no bank sets"
COMMON="--store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --v3 data/external/v3_models/code --k 100 --workers 6 --k_fpp 200 --k_pop 50"
feat() { local tag=$1 arm=$2 csv sets slot run=$B/run_$1_$2e115
  case "$tag" in f1dev) csv=$B/eval_set_f1/p2_molecules.csv; sets=$S5;; np053f1dev) csv=$B/np053_f1dev/p2_molecules.csv; sets=$S3;; c1bankdev) csv=$BCSV; sets=$BSETS;; *) return 1;; esac
  case "$arm" in p0) slot=$F1;; r) slot=data/external/e115_slot_r;; a) slot=data/external/e115_slot_a;; *) return 1;; esac
  rm -rf "$run"; mkdir -p $run/work
  $PY -X utf8 $B/b1_features.py --eval_csv $csv $COMMON --fold_safe $slot --out $run --dump_gen $run/gen --sets $sets > $run/features.log 2>&1; local rc=$?
  echo "== $(date +%T) features $tag $arm rc=$rc"; [ $rc -eq 0 ] || return 1
  for S in $sets; do { [ -s $run/b1_molecules_$S.csv ] && [ -s $run/b1_features_$S.parquet ] && [ -s $run/b1_runner_${S}_in.json ]; } || return 1; done; [ -s $run/b1_features_manifest.json ]; }
for T in f1dev np053f1dev c1bankdev; do
  feat $T p0 & P0=$!; feat $T r & P1=$!; feat $T a & P2=$!
  wait $P0; r0=$?; wait $P1; r1=$?; wait $P2; r2=$?; { [ $r0 -eq 0 ] && [ $r1 -eq 0 ] && [ $r2 -eq 0 ]; } || fail "features $T ($r0 / $r1 / $r2)"
done
$PY -X utf8 - "$BSETS" > $B/diag/x115_table_identity.txt 2>&1 <<'EOF'
import sys
import pandas as pd
B = "experiments/b1_baseline"
for new, old, sets in (("run_f1dev_p0e115", "run_f1dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
                       ("run_np053f1dev_p0e115", "run_np053_f1dev", ["NP_H", "NP_X", "NP_N"]), ("run_c1bankdev_p0e115", "run_c1bankdev_f1", sys.argv[1].split())):
    for s in sets:
        a = pd.read_parquet(f"{B}/{new}/b1_features_{s}.parquet"); b = pd.read_parquet(f"{B}/{old}/b1_features_{s}.parquet")
        same_cols = list(a.columns) == list(b.columns); same = same_cols and len(a) == len(b) and a.reset_index(drop=True).equals(b.reset_index(drop=True))
        print(f"{new} vs {old} {s}: rows {len(a)} / {len(b)}, identical={same}")
EOF
( cd $B && $PY -X utf8 x115_stage1.py > diag/x115_stage1.log 2>&1 ); rc=$?; [ $rc -eq 0 ] || fail "stage-1 reader rc=$rc ($(tail -1 $B/diag/x115_stage1.log | cut -c1-200))"
grep -q "gate PASS" $B/diag/x115_stage1.md || { echo "X115_STAGE1_NO $(date '+%F %T')" | tee $ST; exit 0; }
echo "== $(date +%T) stage 1 PASS -> GLACIER (one cache per tag) + audit + main for the three arms"
gl() { local arm=$1 tag=$2 S=$3; shift 3   # remaining args: cache IN:OUT pairs
  local run=$B/run_${tag}_${arm}e115 w=$B/run_${tag}_${arm}e115/work
  $PYI -X utf8 $B/gl_share.py prepare --inp $run/b1_runner_${S}_in.json --cache "$@" --todo $w/gl_${S}_todo_in.json --plan $w/gl_${S}_plan.json > $w/gl_${S}_share.log 2>&1 || return 1
  if [ "$($PY -c "import json; print(len(json.load(open('$w/gl_${S}_todo_in.json'))))")" != "0" ]; then
    $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $w/gl_${S}_todo_in.json $w/gl_${S}_todo_out.json -- --device cuda --site none --budget 7200 > $w/gl_${S}_resume.log 2>&1 || return 1
  fi
  $PYI -X utf8 $B/gl_share.py merge --inp $run/b1_runner_${S}_in.json --plan $w/gl_${S}_plan.json --todo_out $w/gl_${S}_todo_out.json --out $w/gl_${S}.json >> $w/gl_${S}_share.log 2>&1 || return 1
  $PYI -X utf8 $B/gl_audit.py $run/b1_runner_${S}_in.json $w/gl_${S}.json >> $w/gl_${S}_share.log 2>&1; }
for T in f1dev np053f1dev c1bankdev; do
  case $T in f1dev) SETS=$S5; OLD=$B/run_f1dev;; np053f1dev) SETS=$S3; OLD=$B/run_np053_f1dev;; c1bankdev) SETS=$BSETS; OLD=$B/run_c1bankdev_f1;; esac
  for S in $SETS; do
    C=("$OLD/b1_runner_${S}_in.json:$OLD/work/gl_${S}.json")
    for A in p0 r a; do
      gl $A $T $S "${C[@]}"; rc=$?; echo "== $(date +%T) gl $A $T $S rc=$rc $(tail -1 $B/run_${T}_${A}e115/work/gl_${S}_share.log | cut -c1-150)"; [ $rc -eq 0 ] || fail "GL $A $T $S"
      C+=("$B/run_${T}_${A}e115/b1_runner_${S}_in.json:$B/run_${T}_${A}e115/work/gl_${S}.json")
    done
  done
done
cd $B || exit 1
ev() { local arm=$1 tag=$2; shift 2
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --run run_${tag}_${arm}e115 --gen run_${tag}_${arm}e115/gen "$@" --fold_safe $FS --views c1,c2 --out diag/r115_${arm}_$tag --workers 2 > diag/r115_${arm}_$tag.log 2>&1; local rc=$?
  echo "== $(date +%T) main $arm $tag rc=$rc"; return $rc; }
PIDS=()
for A in p0 r a; do
  ev $A f1dev --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv & PIDS+=($!)
  ev $A np053f1dev --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv & PIDS+=($!)
  ev $A c1bankdev --sets $BSETS --eval_csv c1bank_f1/c1dev/p2_molecules.csv & PIDS+=($!)
done
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || fail "main evaluation"
for f in diag/r115_*.csv; do echo "$(sha256sum $f | cut -c1-64) $f" >> $MAN; done
$PY -X utf8 x115_stage3.py > diag/x115_stage3.log 2>&1; rc=$?
if [ $rc -eq 2 ]; then echo "X115_FAIL_REPRO P0 does not reproduce the existing main; diag/x115_stage3_repro.md $(date '+%F %T')" | tee $ST; exit 1; fi
[ $rc -eq 0 ] || fail "stage-3 reader rc=$rc ($(tail -1 diag/x115_stage3.log | cut -c1-200))"
echo "X115_DONE $(date '+%F %T')" | tee $ST
