#!/bin/bash
# 071 (+ Codex 070 amendment) with the multi-model evaluator gen_eval2m (analogs shared): models rank_v4b, rank_v8w (Spark), rank_v8w_pc,
# rank_v9h, rank_v9a, rank_v9b on every development table. Check first: v4b / v8w outputs must equal the Spark CSVs (r047 / r056) on f1dev
# (implementation + environment check); stop if not. CPU only.
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=6 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P0=$B/rank_v4b/rank_results.json
if [ ! -f $B/rank_v9h/lambdarank.txt ]; then
  RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
  POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
  $PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS $B/run_tp_f3b:$B/train_pool_f3b/p2_molecules.csv:fit --out $B/rank_v9h --feats v2_noice --drop lib_nref in_train --c1_repeat 3 \
    --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 run_tp_f3b=1 --params_from $P0 > $B/rank_v9h_train.log 2>&1
  echo "== $(date +%T) v9h exit $? $(grep -a 'c1 share' $B/rank_v9h_train.log) sha $(sha256sum $B/rank_v9h/lambdarank.txt | cut -c1-8)"
fi
cd $B
MS="rank_v4b rank_v8w rank_v8w_pc rank_v9h rank_v9a rank_v9b"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  MOD=$(for M in $MS; do echo -n "$M/lambdarank.txt,"; done | sed 's/,$//'); OUT=$(for M in $MS; do echo -n "diag/r071m_${M}_$T,"; done | sed 's/,$//')
  $PY -X utf8 gen_eval2m.py --model $MOD --parents 0 "$@" --views c1,c2 --out $OUT --workers 6 > diag/r071m_$T.log 2>&1
  echo "== $(date +%T) eval $T exit $?"; }
chk() { T=$1
  $PY -X utf8 -c "
import pandas as pd, sys
bad = 0
for m, ref in (('rank_v4b', 'r047_rank_v4b'), ('rank_v8w', 'r056_rank_v8w')):
    a = pd.read_csv(f'diag/{ref}_$T.csv'); b = pd.read_csv(f'diag/r071m_{m}_$T.csv')
    x = a.merge(b, on=['set', 'view', 'molecule'], suffixes=('_s', '_p')); d = (x.main_s - x.main_p).abs()
    ok = len(x) == len(a) == len(b) and float(d.max()) < 1e-9; bad += not ok
    print('CHECK $T', m, 'rows', len(a), len(b), len(x), 'equal', int((d < 1e-9).sum()), 'max', float(d.max()), 'OK' if ok else 'MISMATCH')
sys.exit(1 if bad else 0)"; }
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS
chk f1dev || { echo "ENVCHECK FAILED -> stop"; exit 3; }
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS; chk f2dev
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE; chk panel
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE; chk p2dev
echo "P1SCALE071M_DONE $(date +%T)"
