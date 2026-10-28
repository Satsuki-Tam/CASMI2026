#!/bin/bash
# 115 cat15k generation on CPU ONLY (Codex 117 additional answer): preparation for a conditional use, not a performance step; started only after
# the 150-molecule stage-1 run finished technically. One process, explicit --device cpu, thread caps, nice; chunks of 5,000 jobs. Completion = the
# meta file (gl_simulate.py writes it at the end); chunk files without the meta are not a finished product. Hashes of every input in manifest.txt.
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6 OPENBLAS_NUM_THREADS=6 CUDA_VISIBLE_DEVICES=""
O=experiments/e115/cat15k_sim_cpu; C=experiments/e115/cat15k
grep -q "^STAGE1_CPU rc=0" experiments/e115/stage1_cpu/status.txt || { echo "stage 1 not finished technically" > $O/status.txt; exit 1; }
.venv/bin/python -c "import json,sys; r=json.load(open(\"experiments/e115/stage1_cpu/simtest/simtest_result.json\")); sys.exit(0 if r[\"passed\"] and r[\"molecules\"]==150 else 1)" || { echo "stage 1 result not passed / not 150 molecules" > $O/status.txt; exit 1; }
{ echo "cat15k CPU generation $(date "+%F %T")"; for f in $C/catalog.parquet $C/jobs.json $C/stage2_check.json data/external/v2_pool/pool_meta.parquet data/external/fold_safe_fpnet/fp_bits.npy \
   data/external/glacier/ckpt/glacier.pt data/external/glacier/gl_runner.py experiments/e115/gl_simulate.py experiments/e115/sim_jobs.py $O/run.sh; do echo "$(sha256sum $f | cut -c1-64) $f"; done
  .venv-ice/bin/python -c "import torch, rdkit, numpy; print(\"torch\", torch.__version__, \"rdkit\", rdkit.__version__, \"numpy\", numpy.__version__, \"threads\", torch.get_num_threads())"; uname -a; } > $O/manifest.txt 2>&1
nice -n 15 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $C/jobs.json $O/sim --device cpu --chunk 5000 > $O/simulate.log 2>&1; rc=$?
[ $rc -eq 0 ] && [ -s $O/sim_meta.json ] && echo "CAT15K_SIM_DONE $(date "+%F %T")" > $O/status.txt || echo "CAT15K_SIM_FAIL rc=$rc $(date "+%F %T")" > $O/status.txt
