#!/bin/bash
# 107 v2 (107_prereg_data.md section 4, after Codex 107): split v2 (protected identity groups excluded from every additional fit), analog
# features reused from v1 (same tables; coverage now checked strictly for the development runs), rankers cf0 / cfA / cfB / cfall retrained with the
# v2 trainer (ledger filter, fit rosters), gen_eval2fd with v8w7a + the four on the 6 tables. v1 outputs stay unread in diag/cf107_v1_unread.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUTF8=1
PY=~/CASMI2026/.venv/bin/python; C=diag/cf107
$PY -X utf8 cf107_split.py > diag/cf107_split_v2.log 2>&1 || { echo "CF107_FAIL split"; exit 1; }; cat diag/cf107_split_v2.log
[ -s $C/analog_tr_cf107.parquet ] || { echo "CF107_FAIL no merged analog parquet"; exit 1; }
cd ~/CASMI2026 || exit 1
B=experiments/b1_baseline; C=$B/diag/cf107
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
COMMON="--feats v2_noice_ana --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 run_f1dev=1 run_f2dev=1 run_np053_f1dev=1 run_np053_f2dev=1 --params_from $B/rank_params_v7a/rank_results.json --analog_parquet $C/analog_tr_cf107.parquet --filter_to_csv --analog_strict run_f1dev run_f2dev run_np053_f1dev run_np053_f2dev"
dev() { echo "$B/run_f1dev:$C/f1dev_$1_fit.csv:fit $B/run_f2dev:$C/f2dev_$1_fit.csv:fit $B/run_np053_f1dev:$C/np053f1dev_$1_fit.csv:fit $B/run_np053_f2dev:$C/np053f2dev_$1_fit.csv:fit"; }
tr() { M=$1; shift; rm -rf $B/rank_$M; $PY -X utf8 $B/b1_rank_train.py --runs "$@" $COMMON --out $B/rank_$M > $B/rank_${M}_train.log 2>&1; rc=$?; echo "== $(date +%T) train $M exit $rc $(sha256sum $B/rank_$M/lambdarank.txt 2>/dev/null | cut -c1-8) $(grep -a 'FIT-ROSTER' $B/rank_${M}_train.log | cut -c1-80)"; return $rc; }
PIDS=()
tr cf0 $RUNS0 $POOLS & PIDS+=($!)
tr cfA $RUNS0 $POOLS $(dev A) & PIDS+=($!)
tr cfB $RUNS0 $POOLS $(dev B) & PIDS+=($!)
tr cfall $RUNS0 $POOLS $(dev all) & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done; [ $FAIL -eq 0 ] || { echo "CF107_FAIL train"; exit 1; }
grep -a "ANALOG-COVER" $B/rank_cfall_train.log | head -20
{ echo "107 v2 $(date '+%F %T')"; for f in $B/b1_rank_train.py $B/gen_eval2fd.py $B/cf107_split.py $B/x107_summary.py $C/split.csv $C/*_fit.csv $C/analog_tr_cf107.parquet $B/rank_v8w7a/lambdarank.txt $B/rank_cf0/lambdarank.txt $B/rank_cfA/lambdarank.txt $B/rank_cfB/lambdarank.txt $B/rank_cfall/lambdarank.txt $B/rank_cf0/fit_roster.csv $B/rank_cfA/fit_roster.csv $B/rank_cfB/fit_roster.csv $B/rank_cfall/fit_roster.csv; do echo "$(sha256sum $f | cut -c1-16) $f"; done; } > $C/manifest_v2.txt
cd $B || exit 1
MS="rank_v8w7a rank_cf0 rank_cfA rank_cfB rank_cfall"
S5b="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  MOD=$(for M in $MS; do echo -n "$M/lambdarank.txt,"; done | sed 's/,$//'); OUT=$(for M in $MS; do echo -n "diag/cf107/r107_${M#rank_}_$T,"; done | sed 's/,$//')
  $PY -X utf8 gen_eval2fd.py --model $MOD --v7f --parents 0 "$@" --views c1,c2 --out $OUT --workers 2 > diag/cf107/r107_$T.log 2>&1
  rc=$?; echo "== $(date +%T) eval107 $T exit $rc"; return $rc; }
PIDS=()
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE & PIDS+=($!)
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5b --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5b --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5b --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for T in np053f1dev np053f2dev panel f1dev f2dev p2dev; do for M in $MS; do [ -s diag/cf107/r107_${M#rank_}_$T.csv ] || FAIL=1; done; done
for f in diag/cf107/r107_*.csv; do echo "$(sha256sum $f | cut -c1-16) $f" >> diag/cf107/manifest_v2.txt; done
echo "CF107_DONE fail=$FAIL $(date +%T)"
[ $FAIL -eq 0 ] || exit 1
