#!/bin/bash
# 110 (110_prereg_fpseed.md section 3, after Codex 110): waits for the seed-1 fold-1 FPNet job to end, then
#  1. completion check (experiments/fpnet_seed/ckpt_check.py) + split audit (split_audit.py) + fold-1 slot / bits asserts; any failure stops;
#  2. builds the fold-1 dev tables twice with the same code on the same system: control = seed 0 alone (run_*_s0rep), FPavg = + --extra_ckpts
#     <seed-1 final> (run_*_fpavg); same arguments as spark_fold1_sets.sh / spark_np053_sets.sh;
#  3. stage-1 reading (x110_stage1.py, registered); only on PASS: GLACIER for both arms, the v8w7a main (gen_eval2fd --v7f, as in 102/104)
#     for both arms, and the stage-3 reading (x110_stage3.py, registered; it stops itself if the control does not reproduce the existing main).
# Exit statuses are captured right after each command (rc=$?), never after a $(...) substitution.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; R=experiments/fpnet_seed/f1s1; CK=$R/fpnet_f1s1_final.pt
F1=data/external/fpnet_fold1_as_fold0; FS=data/external/fold_safe_fpnet; MAN=$B/diag/x110_manifest.txt
fail() { echo "X110_FAIL $* $(date +%T)"; exit 1; }
while pgrep -f "[s]park_fpnet_f1s1.sh" >/dev/null || pgrep -f "[t]rain_fivefold.py.*--tag fpnet_f1s1" >/dev/null; do sleep 300; done
echo "== $(date +%T) training job ended"
$PY -I experiments/fpnet_seed/ckpt_check.py $R fpnet_f1s1 82855 1 > $R/ckpt_check.log 2>&1; rc=$?; grep -a -E "^(PASS|FAIL)" $R/ckpt_check.log; [ $rc -eq 0 ] || fail "completion check rc=$rc"
$PY -I experiments/fpnet_seed/split_audit.py $R data/external/identity_folds/structures.parquet $FS 1 > $R/split_audit.log 2>&1; rc=$?; [ $rc -eq 0 ] || fail "split audit rc=$rc"
[ "$(realpath $F1/fpnet_fold0.pt)" = "$(realpath $FS/fpnet_fold1.pt)" ] || fail "fold-1 slot does not point to the public fpnet_fold1"
[ "$(sha256sum $F1/fpnet_fold0.pt | cut -c1-64)" = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4" ] || fail "fold-1 slot sha"
[ "$(sha256sum $F1/fp_bits.npy | cut -c1-64)" = "c3869e86449d6fed6e79e9655f8a7d35bd55c3138ecddfc1dae5072627e78677" ] || fail "fp_bits sha"
{ echo "110 $(date '+%F %T')"; for f in $CK $F1/fpnet_fold0.pt $F1/fp_bits.npy $B/b1_features.py $B/gen_eval2fd.py $B/x110_stage1.py $B/x110_stage3.py $B/rank_v8w7a/lambdarank.txt \
  $B/eval_set_f1/p2_molecules.csv $B/np053_f1dev/p2_molecules.csv experiments/fpnet_seed/ckpt_check.py experiments/fpnet_seed/split_audit.py; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $MAN
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
COMMON="--store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $F1 --v3 data/external/v3_models/code --k 100 --workers 8 --k_fpp 200 --k_pop 50"
feat() { case "$1" in run_f1dev_s0rep|run_f1dev_fpavg|run_np053f1dev_s0rep|run_np053f1dev_fpavg) ;; *) echo "bad run name '$1'"; return 1;; esac
  RUN=$B/$1; CSV=$2; SETS=$3; shift 3; rm -rf "$RUN"; mkdir -p $RUN/work
  $PY -X utf8 $B/b1_features.py --eval_csv $CSV $COMMON --out $RUN --dump_gen $RUN/gen --sets $SETS "$@" > $RUN/features.log 2>&1; rc=$?
  echo "== $(date +%T) features $1 rc=$rc"; [ $rc -eq 0 ] || return 1
  for S in $SETS; do { [ -s $RUN/b1_molecules_$S.csv ] && [ -s $RUN/b1_features_$S.parquet ]; } || return 1; done; [ -s $RUN/b1_features_manifest.json ]; }
for T in f1dev np053f1dev; do
  if [ $T = f1dev ]; then CSV=$B/eval_set_f1/p2_molecules.csv; SETS=$S5; else CSV=$B/np053_f1dev/p2_molecules.csv; SETS=$S3; fi
  feat run_${T}_s0rep $CSV "$SETS" & P0=$!
  feat run_${T}_fpavg $CSV "$SETS" --extra_ckpts $CK & P1=$!
  wait $P0; r0=$?; wait $P1; r1=$?; { [ $r0 -eq 0 ] && [ $r1 -eq 0 ]; } || fail "features $T ($r0 / $r1)"
done
( cd $B && $PY -X utf8 x110_stage1.py > diag/x110_stage1.log 2>&1 ); rc=$?; [ $rc -eq 0 ] || fail "stage-1 reader rc=$rc ($(tail -1 $B/diag/x110_stage1.log))"
grep -q "gate PASS" $B/diag/x110_stage1.md || { echo "X110_STAGE1_NO $(date +%T)"; exit 0; }
echo "== $(date +%T) stage 1 PASS -> GLACIER + main for both arms"
for A in s0rep fpavg; do for T in f1dev np053f1dev; do
  if [ $T = f1dev ]; then SETS=$S5; else SETS=$S3; fi; RUN=$B/run_${T}_$A
  for S in $SETS; do
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $RUN/b1_runner_${S}_in.json $RUN/work/gl_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/gl_${S}_resume.log 2>&1
    echo "== $(date +%T) gl $A $T $S $(grep -a '\[resume\] done' $RUN/work/gl_${S}_resume.log | cut -c1-100)"
  done
done; done
cd $B || exit 1
ev() { A=$1; T=$2; shift 2
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --run run_${T}_$A --gen run_${T}_$A/gen "$@" --fold_safe $FS --views c1,c2 --out diag/r110_${A}_$T --workers 2 > diag/r110_${A}_$T.log 2>&1; rc=$?
  echo "== $(date +%T) main $A $T rc=$rc"; return $rc; }
PIDS=()
for A in s0rep fpavg; do
  ev $A f1dev --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv & PIDS+=($!)
  ev $A np053f1dev --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv & PIDS+=($!)
done
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || fail "main evaluation"
for f in diag/r110_*.csv; do echo "$(sha256sum $f | cut -c1-64) $f" >> diag/x110_manifest.txt; done
$PY -X utf8 x110_stage3.py > diag/x110_stage3.log 2>&1; rc=$?
echo "X110_DONE stage3 rc=$rc $(date +%T)"
