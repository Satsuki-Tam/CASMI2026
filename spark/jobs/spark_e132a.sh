#!/bin/bash
# 132 parity (A) (132_prereg_elite_public.md): the submission pipeline's shared E-lite function (experiments/b1_elite/elite.py) asserted inside a
# copy of the 102 evaluator (gen_eval2fd_e132.py, made by make_ge132.py from gen_eval2fd.py 5f3cded6; the original is not touched) on the six
# 102 tables, both views, model rank_e1r only; then x132a_compare.py compares every main / E-lite column with the stored diag/r102_<T>.csv.
# CPU only, nice 15 (x115 holds the GPU); outputs are new files (diag/r132A_*); hashes in diag/r132A_manifest.txt.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=2 PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=-1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; MAN=$B/diag/r132A_manifest.txt
ls $B/diag/r132A_* >/dev/null 2>&1 && { echo "E132A_FAIL outputs exist"; exit 1; }
$PY -X utf8 experiments/b1_elite/make_ge132.py $B/gen_eval2fd.py $B/gen_eval2fd_e132.py || { echo "E132A_FAIL make"; exit 1; }
{ echo "132A $(date '+%F %T')"; for f in $B/gen_eval2fd.py $B/gen_eval2fd_e132.py experiments/b1_elite/elite.py experiments/b1_elite/make_ge132.py experiments/b1_elite/x132a_compare.py $B/b1_rankfeats.py $B/diag/e_window_keys_v2.parquet $B/rank_e1r/lambdarank.txt $B/rank_v8w7a/lambdarank.txt $B/diag/r102_*.csv; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $MAN
cd $B || exit 1
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
ev() { T=$1; shift
  nice -n 15 $PY -X utf8 gen_eval2fd_e132.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --emodel rank_e1r/lambdarank.txt --ekeys diag/e_window_keys_v2.parquet --rrf_k 10 "$@" --views c1,c2 --out diag/r132A_$T --workers 2 > diag/r132A_$T.log 2>&1
  rc=$?; echo "== $(date +%T) e132A $T exit $rc"; return $rc; }
PIDS=()
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets NP_H NP_X NP_N --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE & PIDS+=($!)
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev p2dev --run run_p2dev_fe --gen run_p2dev_fe_g/gen --sets $S5 --eval_csv eval_set2/v2/p2_molecules.csv --fold_safe $FE & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for f in diag/r132A_*.csv diag/r132A_*_e132check.json; do echo "$(sha256sum $f | cut -c1-64) $f" >> ../../$MAN; done
[ $FAIL -eq 0 ] || { echo "E132A_FAIL evaluation (see diag/r132A_<T>.log) $(date +%T)"; exit 1; }
$PY -X utf8 ../b1_elite/x132a_compare.py > diag/x132a_compare.log 2>&1; rc=$?
if [ $rc -eq 0 ]; then echo "E132A_DONE PASS $(tail -1 diag/x132a_compare.log | cut -c1-200) $(date +%T)"; exit 0; fi   # Codex 132: a FAIL must end the job with a non-zero status
echo "E132A_DONE FAIL compare_rc=$rc $(tail -1 diag/x132a_compare.log | cut -c1-200) $(date +%T)"; exit 1
