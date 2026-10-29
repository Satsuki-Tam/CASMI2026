#!/bin/bash
# 105 stage 1: ms-pred preprocessing of a GLACIER adaptation dataset (make_glt_data.py output): MAGMa -> subformulae -> MAGMa trees with
# intensities, inside .venv-glt through experiments/glt/run_mspred.py (shims for dgl / torch_scatter, real LinSATNet). CPU only.
set -u
cd ~/CASMI2026 || exit 1
D=$HOME/CASMI2026/${1:?dataset dir under the repo, e.g. data/glt/tims_s1}; W=${2:-8}
export PYTHONPATH=$HOME/CASMI2026/data/glt/shim_train:$HOME/CASMI2026/data/external/ms-pred-train/ms-pred/src CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=1
PY=".venv-glt/bin/python -X utf8 experiments/glt/run_mspred.py"
[ -e $D/magma_outputs ] && { echo "refused: $D/magma_outputs exists"; exit 1; }
nice -n 10 $PY src/ms_pred/magma/run_magma.py --spectra-dir $D/spec_files.hdf5 --spec-labels $D/labels.tsv --output-dir $D/magma_outputs --max-peaks 50 --ppm-diff 20 --workers $W > $D/magma.log 2>&1 || { echo "GLT_PREP_FAIL magma"; exit 1; }
echo "== $(date +%T) magma done"
mkdir -p $D/subformulae
nice -n 10 $PY data_scripts/forms/01_assign_subformulae.py --data-dir $D --labels-file $D/labels.tsv --use-all --output-dir-name no_subform.hdf5 --num-workers $W > $D/subform.log 2>&1 || { echo "GLT_PREP_FAIL subform"; exit 1; }
echo "== $(date +%T) subformulae done"
nice -n 10 $PY data_scripts/dag/add_dag_intens.py --pred-dag-path $D/magma_outputs/magma_tree.hdf5 --true-dag-path $D/subformulae/no_subform.hdf5 --out-dag-path $D/magma_outputs/magma_tree_with_inten.hdf5 --num-workers $W --magma-output > $D/addinten.log 2>&1 || { echo "GLT_PREP_FAIL addinten"; exit 1; }
for f in $D/magma_outputs/magma_tree.hdf5 $D/subformulae/no_subform.hdf5 $D/magma_outputs/magma_tree_with_inten.hdf5; do echo "$(sha256sum $f | cut -c1-64) $f"; done > $D/prep_manifest.txt
echo "GLT_PREP_DONE $(date '+%F %T')"
