#!/bin/bash
# 107 confirmation (run ONCE, only after the development gate passed and the decision is recorded): v8w7a and cfall on np096_conf093 (NP_H/NP_N C2),
# np102_d0conf (D 286 C2) and c1cost098 (E, C1 view), one gen_eval2fd pass with both models per set; then x107c_summary.py.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
PY=~/CASMI2026/.venv/bin/python; FS=data/external/fold_safe_fpnet; MOD=rank_v8w7a/lambdarank.txt,rank_cfall/lambdarank.txt
{ echo "107 confirmation $(date '+%F %T')"; for f in gen_eval2fd.py x107c_summary.py rank_v8w7a/lambdarank.txt rank_cfall/lambdarank.txt np096_conf093/p2_molecules.csv np102_d0conf/p2_molecules.csv c1cost098/p2_molecules.csv; do echo "$(sha256sum $f | cut -c1-16) $f"; done; } > diag/cf107/c107_manifest.txt
ev() { T=$1; shift
  $PY -X utf8 gen_eval2fd.py --model $MOD --v7f --parents 0 "$@" --views c1,c2 --out diag/cf107/c107_v8w7a_$T,diag/cf107/c107_cfall_$T --workers 2 > diag/cf107/c107_$T.log 2>&1
  rc=$?; echo "== $(date +%T) conf107 $T exit $rc"; return $rc; }
PIDS=()
ev np096c --run run_np096_f0conf --gen run_np096_f0conf/gen --sets NP_H NP_N --eval_csv np096_conf093/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev np102d --run run_np102_d0conf --gen run_np102_d0conf/gen --sets D_np_single --eval_csv np102_d0conf/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
ev c1cost --run run_c1cost098 --gen run_c1cost098/gen --sets E_np_negonly --eval_csv c1cost098/p2_molecules.csv --fold_safe $FS & PIDS+=($!)
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for f in diag/cf107/c107_*.csv; do echo "$(sha256sum $f | cut -c1-16) $f" >> diag/cf107/c107_manifest.txt; done
[ $FAIL -eq 0 ] && $PY -X utf8 x107c_summary.py > diag/cf107/x107c_summary.log 2>&1; echo "C107_DONE fail=$FAIL $(date +%T)"
