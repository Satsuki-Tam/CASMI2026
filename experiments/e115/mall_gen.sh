#!/bin/bash
# 115 v2 (Codex 117 / 118): M_all generation as IDLE-TIME preparation on CPU (nice 19 = lowest priority; never on the GPU while the 110 / 111
# chain runs), started after the cat15k CPU generation ended. Two processes over the fixed plan's job list (make_simplan.py, experiments/e115/mall):
# cycle 1 = jobs[0:N], cycle 2 = jobs[N:2N] (N = catalog size). Each meta is rewritten after every 20,000-job chunk, so a run can be stopped and
# continued later (on CPU or GPU) with --start <meta stop> under a NEW prefix; the trainer accepts several prefixes and checks exact coverage.
# No performance is read; outputs are used only if the registered 115 main comparison runs. Hashes of all inputs in mall_sim/manifest.txt.
cd ~/CASMI2026 || exit 1
O=experiments/e115/mall_sim; P=experiments/e115/mall; mkdir -p $O; ST=$O/status.txt; rm -f $ST
while pgrep -f "[g]l_simulate.py data/external/glacier experiments/e115/cat15k/jobs.json" >/dev/null; do sleep 120; done
grep -q "^CAT15K_SIM_DONE" experiments/e115/cat15k_sim_cpu/status.txt || { echo "MALL_GEN_NOT_STARTED cat15k generation did not finish cleanly $(date "+%F %T")" > $ST; exit 1; }
N=$(.venv/bin/python -c "import json; print(json.load(open('$P/plan_manifest.json'))['catalog'])")
{ echo "M_all CPU generation $(date "+%F %T") N=$N"; for f in $P/catalog.parquet $P/jobs.json $P/jobs_pid.npy $P/plan.npy $P/plan_manifest.json data/external/glacier/ckpt/glacier.pt \
   data/external/glacier/gl_runner.py experiments/e115/gl_simulate.py experiments/e115/make_simplan.py experiments/e115/mall_gen.sh; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $O/manifest.txt
export OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3 CUDA_VISIBLE_DEVICES=""
nice -n 19 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $O/c1 --device cpu --chunk 20000 --start 0 --stop $N > $O/c1.log 2>&1 & P1=$!
nice -n 19 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $O/c2 --device cpu --chunk 20000 --start $N --stop $((2*N)) > $O/c2.log 2>&1 & P2=$!
wait $P1; r1=$?; wait $P2; r2=$?
echo "MALL_GEN_END c1 rc=$r1 c2 rc=$r2 $(date "+%F %T")" > $ST
