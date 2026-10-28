#!/bin/bash
# 115 v2 (Codex 117 / 118 / 119): M_all generation as IDLE-TIME preparation on CPU (nice 19; never on the GPU while the 110 / 111 chain runs),
# started after the cat15k CPU generation ended. Two processes x 2 threads (total 4 = the level measured at ~2-3.5% FPNet slowdown; Codex 119:
# nice does not remove memory / bandwidth contention) over the FIXED plan's job list (make_simplan.py -> experiments/e115/mall):
# cycle 1 = jobs[0:N], cycle 2 = jobs[N:2N] (N = catalog size). Each meta is rewritten (atomically) after every 20,000-job chunk, so a run can be
# stopped and continued later (CPU or GPU) with --start <meta stop> under a NEW prefix; the trainer accepts several prefixes and checks exact
# coverage. Before starting: the plan files still match plan_manifest.json and jobs == plan == 2N (no stale auto-start after a plan change).
# No performance is read; outputs are used only if the registered 115 main comparison runs. Exit status non-zero unless both ranges complete.
cd ~/CASMI2026 || exit 1
O=experiments/e115/mall_sim; P=experiments/e115/mall; mkdir -p $O; ST=$O/status.txt; rm -f $ST
fail() { echo "MALL_GEN_FAIL $* $(date "+%F %T")" > $ST; exit 1; }
while pgrep -f "[g]l_simulate.py data/external/glacier experiments/e115/cat15k/jobs.json" >/dev/null; do sleep 120; done
grep -q "^CAT15K_SIM_DONE" experiments/e115/cat15k_sim_cpu/status.txt || fail "cat15k generation did not finish cleanly"
.venv/bin/python -I - "$P" <<'PYEOF' || fail "plan files changed or inconsistent"
import hashlib, json, sys, numpy as np
P = sys.argv[1]; m = json.load(open(f"{P}/plan_manifest.json"))
def fsha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
bad = [f for f, h in m["outputs"].items() if fsha(f"{P}/{f}") != h]
n = m["catalog"]; plan = np.load(f"{P}/plan.npy", allow_pickle=False); jobs = json.load(open(f"{P}/jobs.json"))
ok = not bad and m["cycles"] == 2 and m["limit"] == 0 and len(jobs) == len(plan) == 2 * n
print("plan check", "OK" if ok else f"FAIL changed={bad} cycles={m['cycles']} limit={m['limit']} jobs={len(jobs)} plan={len(plan)} 2N={2 * n}")
sys.exit(0 if ok else 1)
PYEOF
N=$(.venv/bin/python -c "import json; print(json.load(open('$P/plan_manifest.json'))['catalog'])")
{ echo "M_all CPU generation $(date "+%F %T") N=$N"; for f in $P/catalog.parquet $P/jobs.json $P/jobs_pid.npy $P/plan.npy $P/plan_manifest.json $P/alias_audit.csv data/external/glacier/ckpt/glacier.pt \
   data/external/glacier/gl_runner.py experiments/e115/gl_simulate.py experiments/e115/make_simplan.py experiments/e115/mall_gen.sh; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $O/manifest.txt
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=""
nice -n 19 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $O/c1 --device cpu --chunk 20000 --start 0 --stop $N > $O/c1.log 2>&1 & P1=$!
nice -n 19 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $O/c2 --device cpu --chunk 20000 --start $N --stop $((2*N)) > $O/c2.log 2>&1 & P2=$!
trap 'kill $P1 $P2 2>/dev/null' TERM INT
wait $P1; r1=$?; wait $P2; r2=$?
c1=$(.venv/bin/python -c "import json; print(json.load(open('$O/c1_meta.json')).get('complete'))" 2>/dev/null); c2=$(.venv/bin/python -c "import json; print(json.load(open('$O/c2_meta.json')).get('complete'))" 2>/dev/null)
{ [ $r1 -eq 0 ] && [ $r2 -eq 0 ] && [ "$c1" = "True" ] && [ "$c2" = "True" ]; } || fail "c1 rc=$r1 complete=$c1, c2 rc=$r2 complete=$c2"
echo "MALL_GEN_DONE $(date "+%F %T")" > $ST
