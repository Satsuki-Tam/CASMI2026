#!/bin/bash
# 133 (MIST-feature ranker pair, 133_prereg_mist_ranker.md): the v8w7a recipe (pc_lc127.sh) twice on the same rows -- control (v2_noice_ana) and M
# (v2_noice_ana_mist with the MIST v4 tables of the five training runs, strict coverage). CPU only. The control must reproduce rank_v8w7a
# (fe61dc42) byte for byte (else recorded, and the retrained control is the comparison's P). No evaluation here; the training logs' tune / eval
# metrics are not read before the registration is final.
set -u
cd /c/kaggle/CASMI || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; P7=$B/rank_params_v7a/rank_results.json
RUNS0="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
POOLS="$B/run_tp_f3a:$B/train_pool_f3a/p2_molecules.csv:fit $B/run_tp_f4a:$B/train_pool_f4a/p2_molecules.csv:fit"
TAGS="run_v3_p1=tr_v3p1 run_v3_eval=tr_v3eval run_v3_c1=tr_v3c1 run_tp_f3a=tr_f3a run_tp_f4a=tr_f4a"
for d in $B/rank_m133_ctrl $B/rank_m133; do [ -e $d ] && { echo "refused: $d exists"; exit 1; }; done
echo "== $(date '+%F %T') trainer $(sha256sum $B/b1_rank_train.py | cut -c1-12) rankfeats $(sha256sum $B/b1_rankfeats.py | cut -c1-12) mist tables $(cat experiments/mist/scores_v4/mist_tr_*.parquet | sha256sum | cut -c1-12)"
trn() { local OUT=$1; shift
  $PY -X utf8 $B/b1_rank_train.py --runs $RUNS0 $POOLS --out $OUT --drop lib_nref in_train --c1_repeat 3 --c1_repeat_run run_tp_f3a=1 run_tp_f4a=1 \
    --params_from $P7 --analog_parquet $B/diag/analog_tr_v8w.parquet "$@" > $OUT.log 2>&1; local rc=$?
  echo "== $(date +%T) $OUT rc=$rc $(grep -a -E 'fit groups after|MIST-COVER|133 MIST tables' $OUT.log | tr '\n' ' ' | cut -c1-400) sha $(sha256sum $OUT/lambdarank.txt 2>/dev/null | cut -c1-16)"; return $rc; }
trn $B/rank_m133_ctrl --feats v2_noice_ana & P1=$!
trn $B/rank_m133 --feats v2_noice_ana_mist --mist_dir experiments/mist/scores_v4 --mist_tags $TAGS & P2=$!
wait $P1; R1=$?; wait $P2; R2=$?
[ $R1 -eq 0 ] && [ $R2 -eq 0 ] || { echo "M133_TRAIN_FAIL rc $R1 $R2"; exit 1; }
if [ "$(sha256sum $B/rank_m133_ctrl/lambdarank.txt | cut -c1-64)" = "$(sha256sum $B/rank_v8w7a/lambdarank.txt | cut -c1-64)" ]; then echo "control reproduces rank_v8w7a (fe61dc42) byte for byte"; else echo "control DIFFERS from rank_v8w7a"; fi
echo "M133_TRAIN_DONE $(date '+%F %T')"
