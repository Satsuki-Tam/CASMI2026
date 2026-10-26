#!/bin/bash
# 067 on the LOCAL PC (the Spark is needed by the user since 08:37): finish run_l2_C (GLACIER for D/E/F/G; C_np_crosslib was scored on the
# Spark before the stop), panel under C (features + GLACIER), then gen_eval2 (rank_v4b fixed) for locked2 A / B / C and panel C.
# One CUDA job at a time (the RTX 5070 Ti also drives the display).
set -u
cd /c/kaggle/CASMI || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONUTF8=1
B=experiments/b1_baseline; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; IPY=/c/kaggle/CASMI/.venv-ice/Scripts/python.exe
FE=data/external/fpnet_fulleval_as_fold0; F0=data/external/fold_safe_fpnet
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
gl() {  # $1 run dir, $2 set
  $IPY spark/jobs/ice_resume.py --python $IPY data/external/glacier/gl_runner.py data/external/glacier $1/b1_runner_$2_in.json $1/work/gl_$2.json -- --device cuda --site none --budget 3600 > $1/work/gl_$2_resume.log 2>&1
  echo "== $(date +%T) gl $(basename $1) $2 $(grep -a '\[resume\] done' $1/work/gl_$2_resume.log | cut -c1-90)"
}
for S in D_np_single E_np_negonly F_np_uncovered G_tims_crosslib; do gl $B/run_l2_C $S; done
R=$B/run_panel_C; mkdir -p $R/work
$PY -X utf8 $B/b1_features.py --eval_csv $B/panel_np250/p1_molecules.csv --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
  --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $FE --v3 data/external/v3_models/code --out $R --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
  --dump_gen $R/gen --sets P_np250 --extra_ckpts $F0/fpnet_fold0.pt > $R/features.log 2>&1
echo "== $(date +%T) panel_C features exit $? $(grep -a 'FPNet ensemble\|^saved' $R/features.log | tr '\n' ' ' | cut -c1-200)"
gl $R P_np250
export NUMBA_NUM_THREADS=6
cd $B
for X in A:$FE B:$F0 C:$FE; do
  N=${X%%:*}; FS=${X#*:}
  $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run run_l2_$N --gen run_l2_$N/gen --sets $S5 --eval_csv locked_eval2/v2/p2_molecules.csv --fold_safe $FS --views c1,c2 --out diag/m067_l2_$N --workers 6 > diag/m067_l2_$N.log 2>&1
  echo "== $(date +%T) eval l2 $N exit $?"
done
$PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run run_panel_C --gen run_panel_C/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $FE --views c1,c2 --out diag/m067_panel_C --workers 6 > diag/m067_panel_C.log 2>&1
echo "== $(date +%T) eval panel C exit $?"
echo "MIX067_PC_DONE $(date +%T)"
