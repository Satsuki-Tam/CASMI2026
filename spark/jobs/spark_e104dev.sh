#!/bin/bash
# 104 dev evaluation (t1E = main rank-1 fixed + E slots re-ordered; models of 102 reused; results unread until the 104 registration is reviewed). Based on 102 v2 (after Codex 102): E keys v2 (official keys recomputed from SMILES), E-lite training (e1b pointwise binary, e1r lambdarank control; same runs as
# v8w7a, features e1, E subset of the view lists) and one gen_eval2fd --v7f --emodel pass per development table (main = rank_v8w7a).
# Every step's exit status is checked; outputs are created fresh; hashes go to diag/r102_manifest.txt. Results are not read here.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=~/CASMI2026/.venv/bin/python; KEYS=$B/diag/e_window_keys_v2.parquet; MAN=$B/diag/r104_manifest.txt
[ -s $KEYS ] || { echo "E104_FAIL no keys"; exit 1; }
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
COMMON="--runs $RUNS0 $POOLS --feats e1 --restrict E --ekeys $KEYS --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 --analog_parquet $B/diag/analog_tr_v8w.parquet"
{ echo "104 dev (t1E; models of 102 reused) $(date '+%F %T')"; for f in $B/gen_eval2fd.py $KEYS $B/rank_e1b/lambdarank.txt $B/rank_e1r/lambdarank.txt $B/rank_v8w7a/lambdarank.txt; do echo "$(sha256sum $f | cut -c1-16) $f"; done; } > $MAN
cd $B || exit 1
rm -f diag/r104_*.csv diag/r104_*.md diag/r104_*.log
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
EM=rank_e1b/lambdarank.txt,rank_e1r/lambdarank.txt
ev() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --emodel $EM --ekeys diag/e_window_keys_v2.parquet --rrf_k 10 "$@" --views c1,c2 --out diag/r104_$T --workers 2 > diag/r104_$T.log 2>&1
  rc=$?; echo "== $(date +%T) eval102 $T exit $rc"; return $rc; }
PIDS=()
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE & PIDS+=($!)
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for T in np053f1dev np053f2dev panel f1dev f2dev p2dev; do [ -s diag/r104_$T.csv ] || FAIL=1; done
for f in diag/r104_*.csv; do echo "$(sha256sum $f | cut -c1-16) $f" >> r104_manifest_csv.txt; done
echo "E104_DONE fail=$FAIL $(date +%T)"
