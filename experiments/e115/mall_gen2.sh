#!/bin/bash
# 115 v2: continuation of the M_all CPU generation with more processes. mall_gen.sh ran 2 processes x 2 threads, a cap chosen for the speed of the
# 110 FPNet training; that training has ended, and the CPU is mostly idle while the GPU chain runs. This job waits until the 110 table rebuild is
# over (x110 stage-1 file or a terminal x110 status), then stops mall_gen.sh's two generators BY PID (each keeps a valid partial part: its meta
# covers the chunks written so far; an unfinished chunk exists only as <prefix>_NNNN.npz.tmp, moved aside), and covers the rest of each range with
# K contiguous sub-ranges under NEW prefixes (gl_simulate refuses existing ones). Same plan files, job list, code and settings (CPU, nice 19,
# 2 threads per process, chunk 20,000). The A trainer takes all prefixes and checks exact coverage, hashes and recorded failures itself.
# Status line in mall_sim/status2.txt: MALL_GEN2_DONE <prefix list> / MALL_GEN2_FAIL <reason>. Usage: nohup bash experiments/e115/mall_gen2.sh <pid_c1> <pid_c2> [K] &
cd ~/CASMI2026 || exit 1
P1=${1:?pid of the c1 generator}; P2=${2:?pid of the c2 generator}; K=${3:-3}
O=experiments/e115/mall_sim; P=experiments/e115/mall; ST=$O/status2.txt; rm -f $ST
fail() { echo "MALL_GEN2_FAIL $* $(date "+%F %T")" > $ST; exit 1; }
for p in $P1 $P2; do ps -o args= -p $p | grep -q "gl_simulate.py data/external/glacier $P/jobs.json $O/c[12] --device cpu" || fail "pid $p is not an M_all c1/c2 generator"; done
B=experiments/b1_baseline
while [ ! -s $B/diag/x110_stage1.md ] && ! grep -q "^X110_" $B/diag/x110_status.txt 2>/dev/null; do sleep 60; done
echo "== $(date "+%F %T") x110 tables done; stopping c1 / c2 (pids $P1 $P2)" > $O/gen2.log
kill $P1 $P2; for i in $(seq 60); do kill -0 $P1 2>/dev/null || kill -0 $P2 2>/dev/null || break; sleep 2; done
{ kill -0 $P1 2>/dev/null || kill -0 $P2 2>/dev/null; } && fail "c1 / c2 did not stop"
mkdir -p $O/killed_tmp; mv $O/c1_*.npz.tmp $O/c2_*.npz.tmp $O/killed_tmp/ 2>/dev/null
N=$(.venv/bin/python -c "import json; print(json.load(open('$P/plan_manifest.json'))['catalog'])")
RANGES=$(.venv/bin/python -I - "$O" "$N" "$K" <<'PYEOF'
import glob, json, os, sys
O, N, K = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); out = []
for pf, lo, hi in ((f"{O}/c1", 0, N), (f"{O}/c2", N, 2 * N)):
    m = json.load(open(pf + "_meta.json")) if os.path.exists(pf + "_meta.json") else None
    if m is None:
        if glob.glob(pf + "_[0-9]*.npz"): sys.exit(f"{pf}: shards without a meta")
        s = lo
    else:
        if int(m["start"]) != lo or int(m["requested_stop"]) != hi or m.get("complete"): sys.exit(f"{pf}: unexpected meta {m['start']} {m['requested_stop']} {m.get('complete')}")
        s = int(m["stop"]); shards = sorted(glob.glob(pf + "_[0-9]*.npz"))
        if len(shards) != int(m["chunks"]) or int(m["n_ok"]) + int(m["n_fail"]) + sum(m.get("rejected", {}).values()) != s - lo: sys.exit(f"{pf}: meta / shards inconsistent")
    step = -(-(hi - s) // K)
    for k in range(K):
        a, b = s + k * step, min(hi, s + (k + 1) * step)
        if a < b: out.append(f"{pf}{'abc'[k]}:{a}:{b}")
print(" ".join(out))
PYEOF
) || fail "partial parts inconsistent"
echo "== $(date "+%F %T") ranges $RANGES" >> $O/gen2.log
{ echo "M_all CPU generation, continuation $(date "+%F %T") N=$N K=$K ranges $RANGES"; for f in $P/catalog.parquet $P/jobs.json $P/jobs_pid.npy $P/plan.npy $P/plan_manifest.json \
   $P/alias_audit.csv data/external/glacier/ckpt/glacier.pt data/external/glacier/gl_runner.py experiments/e115/gl_simulate.py experiments/e115/make_simplan.py experiments/e115/mall_gen2.sh; do
   echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $O/manifest2.txt
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=""
PIDS=(); PREF=()
for r in $RANGES; do pf=${r%%:*}; rest=${r#*:}; a=${rest%%:*}; b=${rest#*:}
  nice -n 19 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $pf --device cpu --chunk 20000 --start $a --stop $b > $pf.log 2>&1 & PIDS+=($!); PREF+=($pf)
done
trap 'kill ${PIDS[*]} 2>/dev/null' TERM INT
echo "== $(date "+%F %T") started ${#PIDS[@]} generators: ${PIDS[*]}" >> $O/gen2.log
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
for pf in "${PREF[@]}"; do c=$(.venv/bin/python -c "import json; print(json.load(open('$pf' + '_meta.json')).get('complete'))" 2>/dev/null); [ "$c" = "True" ] || FAIL=1; done
[ $FAIL -eq 0 ] || fail "a continuation part did not complete"
ALL=$(for pf in $O/c1 $O/c2 "${PREF[@]}"; do [ -s ${pf}_meta.json ] && echo -n "$(realpath $pf),"; done)
echo "MALL_GEN2_DONE ${ALL%,} $(date "+%F %T")" > $ST
