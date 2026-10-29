#!/bin/bash
# pop0 LOCAL COST (116 / 124 / 125; descriptive, not a gate): the reviewed evaluator (gen_eval2fd_n111.py = PC gen_eval2fd.py, sha 1ccf5e35)
# --v7f --parents 0 --pop_ws 0.5,0 with rank_v8w7a on the existing development tables (stored GLACIER), CPU only, AFTER the 111 evaluation
# has written its status. pw0.5 must equal main on every row (variant path = P); pw0 = the fixed-rule prior coefficient 0 on both paths (the
# pop0 kernel's change). Reader: x_pop0_local.py -> diag/x_pop0_local.md. Status: diag/xpop0_status.txt.
set -u
cd ~/CASMI2026/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
PY=$HOME/CASMI2026/.venv/bin/python; ST=diag/xpop0_status.txt
rm -f $ST
fail() { echo "POP0_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ "$(sha256sum gen_eval2fd_n111.py | cut -c1-64)" = "1ccf5e356129d4653e1dfd9e1f988e010bdca8ccb1b45e83bd37a9e70299febd" ] || fail "evaluator sha"
while [ ! -s diag/x111_status.txt ]; do pgrep -f "[s]park_n111.sh" >/dev/null || break; sleep 120; done
echo "== $(date +%T) start (111 status: $(cat diag/x111_status.txt 2>/dev/null | cut -c1-80))"
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"; S3="NP_H NP_X NP_N"; FS=data/external/fold_safe_fpnet; FE=data/external/fpnet_fulleval_as_fold0
BSETS=$($PY -c "import pandas as pd; print(' '.join(sorted(pd.read_csv('c1bank_f1/c1dev/p2_molecules.csv').set.unique())))")
ev() { local T=$1; shift
  $PY -X utf8 gen_eval2fd_n111.py --model rank_v8w7a/lambdarank.txt --v7f --pop_ws 0.5,0 --parents 0 "$@" --views c1,c2 --out diag/rpop0_$T --workers 4 > diag/rpop0_$T.log 2>&1; local rc=$?
  echo "== $(date +%T) pop0 $T rc=$rc"; return $rc; }
ev f1dev --run run_f1dev --gen run_f1dev/gen --sets $S5 --eval_csv eval_set_f1/p2_molecules.csv --fold_safe $FS || fail "f1dev"
ev np053f1dev --run run_np053_f1dev --gen run_np053_f1dev/gen --sets $S3 --eval_csv np053_f1dev/p2_molecules.csv --fold_safe $FS || fail "np053f1dev"
ev c1bankdev --run run_c1bankdev_f1 --gen run_c1bankdev_f1/gen --sets $BSETS --eval_csv c1bank_f1/c1dev/p2_molecules.csv --fold_safe $FS || fail "c1bankdev"
ev f2dev --run run_f2dev --gen run_f2dev/gen --sets $S5 --eval_csv eval_set_f2/p2_molecules.csv --fold_safe $FS || fail "f2dev"
ev np053f2dev --run run_np053_f2dev --gen run_np053_f2dev/gen --sets $S3 --eval_csv np053_f2dev/p2_molecules.csv --fold_safe $FS || fail "np053f2dev"
ev panel --run run_panel_fe --gen run_panel_fe_g/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE || fail "panel"
$PY -X utf8 x_pop0_local.py > diag/x_pop0_local.log 2>&1; rc=$?
[ $rc -eq 0 ] || fail "reader rc=$rc ($(tail -1 diag/x_pop0_local.log | cut -c1-200))"
echo "POP0_LOCAL_DONE $(date '+%F %T')" | tee $ST
