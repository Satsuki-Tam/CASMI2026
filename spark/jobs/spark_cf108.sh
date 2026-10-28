#!/bin/bash
# 108 (108_prereg_c1w.md): the 107 v2 fit lists / split / features / params unchanged; C1 nominal group-weight share restored to cf0's
# (q0 from the cf0 fit composition, --c1_share_target). Models cfAw / cfBw / cfallw; gen_eval2fd with v8w7a + the three on the 6 tables.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUTF8=1
PY=~/CASMI2026/.venv/bin/python; B=experiments/b1_baseline; C=$B/diag/cf107; O=$B/diag/cf108; mkdir -p $O
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
COMMON="--feats v2_noice_ana --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 run_f1dev=1 run_f2dev=1 run_np053_f1dev=1 run_np053_f2dev=1 --params_from $B/rank_params_v7a/rank_results.json --analog_parquet $C/analog_tr_cf107.parquet --filter_to_csv --analog_strict run_f1dev run_f2dev run_np053_f1dev run_np053_f2dev"
dev() { echo "$B/run_f1dev:$C/f1dev_$1_fit.csv:fit $B/run_f2dev:$C/f2dev_$1_fit.csv:fit $B/run_np053_f1dev:$C/np053f1dev_$1_fit.csv:fit $B/run_np053_f2dev:$C/np053f2dev_$1_fit.csv:fit"; }
rm -rf $B/rank_cf0c; $PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS $COMMON --out $B/rank_cf0c > $B/rank_cf0c_train.log 2>&1 || { echo "CF108_FAIL cf0"; exit 1; }
Q0=$($PY -c "import json; print(json.load(open('$B/rank_cf0c/fit_composition.json'))['c1_share'])"); echo "== $(date +%T) q0 $Q0 (cf0 model $(sha256sum $B/rank_cf0c/lambdarank.txt | cut -c1-8), 107 cf0 $(sha256sum $B/rank_cf0/lambdarank.txt | cut -c1-8))"
tr() { M=$1; shift; rm -rf $B/rank_$M; $PY -X utf8 $B/b1_rank_train.py --runs "$@" $COMMON --c1_share_target $Q0 --out $B/rank_$M > $B/rank_${M}_train.log 2>&1; rc=$?; echo "== $(date +%T) train $M exit $rc $(sha256sum $B/rank_$M/lambdarank.txt 2>/dev/null | cut -c1-8) $(grep -a 'C1-SHARE' $B/rank_${M}_train.log | cut -c1-100)"; return $rc; }
PIDS=()
tr cfAw $RUNS0 $POOLS $(dev A) & PIDS+=($!)
tr cfBw $RUNS0 $POOLS $(dev B) & PIDS+=($!)
tr cfallw $RUNS0 $POOLS $(dev all) & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || { echo "CF108_FAIL train"; exit 1; }
{ echo "108 $(date '+%F %T') q0 $Q0"; for f in $B/b1_rank_train.py $B/x108_summary.py $B/rank_cf0c/fit_composition.json $B/rank_cfAw/fit_composition.json $B/rank_cfBw/fit_composition.json $B/rank_cfallw/fit_composition.json $B/rank_cfAw/lambdarank.txt $B/rank_cfBw/lambdarank.txt $B/rank_cfallw/lambdarank.txt $B/rank_cfAw/fit_roster.csv $B/rank_cfBw/fit_roster.csv $B/rank_cfallw/fit_roster.csv; do echo "$(sha256sum $f | cut -c1-16) $f"; done; } > $O/manifest.txt
cd $B || exit 1
MS="rank_v8w7a rank_cfAw rank_cfBw rank_cfallw"
S5b="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  MOD=$(for M in $MS; do echo -n "$M/lambdarank.txt,"; done | sed 's/,$//'); OUT=$(for M in $MS; do echo -n "diag/cf108/r108_${M#rank_}_$T,"; done | sed 's/,$//')
  $PY -X utf8 gen_eval2fd.py --model $MOD --v7f --parents 0 "$@" --views c1,c2 --out $OUT --workers 2 > diag/cf108/r108_$T.log 2>&1
  rc=$?; echo "== $(date +%T) eval108 $T exit $rc"; return $rc; }
PIDS=()
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE & PIDS+=($!)
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5b --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5b --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5b --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for T in np053f1dev np053f2dev panel f1dev f2dev p2dev; do for M in $MS; do [ -s diag/cf108/r108_${M#rank_}_$T.csv ] || FAIL=1; done; done
for f in diag/cf108/r108_*.csv; do echo "$(sha256sum $f | cut -c1-16) $f" >> diag/cf108/manifest.txt; done
echo "CF108_DONE fail=$FAIL $(date +%T)"
[ $FAIL -eq 0 ] || exit 1
