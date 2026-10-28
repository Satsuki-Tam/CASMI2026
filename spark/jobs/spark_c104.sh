#!/bin/bash
# 104 confirmation (run ONCE, only after the development gate passed and the decision is recorded): t1E on np096_conf093 (NP_H/NP_N C2),
# np102_d0conf (D 286 C2) and c1cost098 (E, C1 view), main = v8w7a, E = rank_e1r (102), keys v2. Then x104c_summary.py.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=~/CASMI2026/.venv/bin/python; FS=data/external/fold_safe_fpnet; EM=rank_e1b/lambdarank.txt,rank_e1r/lambdarank.txt
{ echo "104 confirmation $(date '+%F %T')"; for f in gen_eval2fd.py x104c_summary.py diag/e_window_keys_v2.parquet rank_e1r/lambdarank.txt rank_v8w7a/lambdarank.txt np096_conf093/p2_molecules.csv np102_d0conf/p2_molecules.csv c1cost098/p2_molecules.csv; do echo "$(sha256sum $f | cut -c1-16) $f"; done; } > diag/c104_manifest.txt
ev() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model rank_v8w7a/lambdarank.txt --v7f --parents 0 --emodel $EM --ekeys diag/e_window_keys_v2.parquet --rrf_k 10 "$@" --views c1,c2 --out diag/c104_$T --workers 2 > diag/c104_$T.log 2>&1
  rc=$?; echo "== $(date +%T) conf104 $T exit $rc"; return $rc; }
PIDS=()
ev np096c --run run_np096_f0conf --gen run_np096_f0conf/gen --sets NP_H NP_N --eval_csv np096_conf093/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev np102d --run run_np102_d0conf --gen run_np102_d0conf/gen --sets D_np_single --eval_csv np102_d0conf/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev c1cost --run run_c1cost098 --gen run_c1cost098/gen --sets E_np_negonly --eval_csv c1cost098/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for f in diag/c104_*.csv; do echo "$(sha256sum $f | cut -c1-16) $f" >> diag/c104_manifest.txt; done
[ $FAIL -eq 0 ] && $PY -X utf8 x104c_summary.py > diag/x104c_summary.log 2>&1; echo "C104_DONE fail=$FAIL $(date +%T)"
