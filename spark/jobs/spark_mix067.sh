#!/bin/bash
# 067: production FPNet choice on the unopened locked2 v2 (fold 0; unseen by full_eval and by public fold0): A = full_eval, B = public
# fold0, C = equal logit mean of both; plus the panel under C (class-1 regime check vs the existing full_eval panel run). rank_v4b fixed.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=$HOME/CASMI2026/.venv/bin/python; FE=data/external/fpnet_fulleval_as_fold0; F0=data/external/fold_safe_fpnet
S5="C_np_crosslib D_np_single E_np_negonly F_np_uncovered G_tims_crosslib"
feat() {  # $1 run dir, $2 eval csv, $3 fold_safe dir, $4 extra args, $5 sets
  mkdir -p $1/work
  nice -n 5 $PY -X utf8 $B/b1_features.py --eval_csv $2 --store data/processed/spectra_store --tier data/external/pubchem_tier --pop data/external/pubchem_popularity \
    --pool data/external/v2_pool/pool_meta.parquet --coco data/external/coconut --fold_safe $3 --v3 data/external/v3_models/code --out $1 --k 100 --workers 8 --k_fpp 200 --k_pop 50 \
    --dump_gen $1/gen --sets $5 $4 > $1/features.log 2>&1
  echo "== $(date +%T) $(basename $1) features exit $? $(grep -a 'FPNet ensemble\|^saved' $1/features.log | tr '\n' ' ' | cut -c1-200)"
  for S in $5; do
    .venv-ice/bin/python spark/jobs/ice_resume.py --python .venv-ice/bin/python data/external/glacier/gl_runner.py data/external/glacier $1/b1_runner_${S}_in.json $1/work/gl_${S}.json -- --device cuda --site none --budget 3600 > $1/work/gl_${S}_resume.log 2>&1
  done
  echo "== $(date +%T) $(basename $1) gl done"
}
feat $B/run_l2_A $B/locked_eval2/v2/p2_molecules.csv $FE "" "$S5"
feat $B/run_l2_B $B/locked_eval2/v2/p2_molecules.csv $F0 "" "$S5"
feat $B/run_l2_C $B/locked_eval2/v2/p2_molecules.csv $FE "--extra_ckpts $F0/fpnet_fold0.pt" "$S5"
feat $B/run_panel_C $B/panel_np250/p1_molecules.csv $FE "--extra_ckpts $F0/fpnet_fold0.pt" "P_np250"
export NUMBA_NUM_THREADS=6
cd $B
for X in A:$FE B:$F0 C:$FE; do
  N=${X%%:*}; FS=${X#*:}
  nice -n 5 $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run run_l2_$N --gen run_l2_$N/gen --sets $S5 --eval_csv locked_eval2/v2/p2_molecules.csv --fold_safe $HOME/CASMI2026/$FS --views c1,c2 --out diag/m067_l2_$N --workers 6 > diag/m067_l2_$N.log 2>&1
  echo "== $(date +%T) eval l2 $N exit $?"
done
nice -n 5 $PY -X utf8 gen_eval2.py --model rank_v4b/lambdarank.txt --parents 0 --run run_panel_C --gen run_panel_C/gen --sets P_np250 --eval_csv panel_np250/p1_molecules.csv --fold_safe $HOME/CASMI2026/$FE --views c1,c2 --out diag/m067_panel_C --workers 6 > diag/m067_panel_C.log 2>&1
echo "== $(date +%T) eval panel C exit $?"
echo "MIX067_DONE $(date +%T)"
