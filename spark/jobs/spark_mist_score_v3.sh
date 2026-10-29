#!/bin/bash
# 128 v3 (Codex 129: adapter float32 -> float16 rounding, --threads, ledger-checked empty windows): MIST (aug) per-candidate scores for the B1 development tables (label-free; experiments/mist/mist_score.py; read only after the stage-2/3 design
# is registered). CPU only, 4 threads, nice 10. Status: experiments/mist/scores/status.txt
set -u
cd ~/CASMI2026 || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=4 PYTHONUTF8=1
PY=.venv-mist/bin/python; CK=data/external/mist/zenodo_23303289/mist_msg_aug.ckpt; B=experiments/b1_baseline; O=experiments/mist/scores_v3; mkdir -p $O; ST=$O/status.txt; rm -f $ST
[ "$(sha256sum $CK | cut -c1-64)" = "9f251d772f68315ba6fe2dc75a3b2e1ec477d3f41ffbeaf5143749157b67b177" ] || { echo "MIST_SCORE_FAIL ckpt sha" > $ST; exit 1; }
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"
BSETS=$(.venv/bin/python -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('$B/c1bank_f1/c1dev/p2_molecules.csv').set.unique())))")
sc() { local T=$1 RUN=$2 CSV=$3; shift 3
  nice -n 10 $PY -X utf8 experiments/mist/mist_score.py --ckpt $CK --store data/processed/spectra_store --run $RUN --eval_csv $CSV --tag $T --sets "$@" --out $O --threads 4 > $O/mist_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) mist $T rc=$rc"; return $rc; }
sc f1dev $B/run_f1dev $B/eval_set_f1/p2_molecules.csv $S5 || { echo "MIST_SCORE_FAIL f1dev" > $ST; exit 1; }
sc np053f1dev $B/run_np053_f1dev $B/np053_f1dev/p2_molecules.csv $S3 || { echo "MIST_SCORE_FAIL np053f1dev" > $ST; exit 1; }
sc c1bankdev $B/run_c1bankdev_f1 $B/c1bank_f1/c1dev/p2_molecules.csv $BSETS || { echo "MIST_SCORE_FAIL c1bankdev" > $ST; exit 1; }
sc f2dev $B/run_f2dev $B/eval_set_f2/p2_molecules.csv $S5 || { echo "MIST_SCORE_FAIL f2dev" > $ST; exit 1; }
sc np053f2dev $B/run_np053_f2dev $B/np053_f2dev/p2_molecules.csv $S3 || { echo "MIST_SCORE_FAIL np053f2dev" > $ST; exit 1; }
echo "MIST_SCORE_DONE $(date '+%F %T')" | tee $ST
