#!/bin/bash
# 115 v2: re-split of the M_all CPU generation into more processes (v2 after Codex 122). mall_gen.sh ran 2 processes x 2 threads, a cap chosen for
# the speed of the 110 FPNet training; that training has ended. Generic: given generator PIDs and their prefixes, it
#  (0) takes the switch lock (mall_sim/gen2.lock; separate from the GPU lock), checks K (1..3), the plan files against plan_manifest.json, and that
#      every given PID is alive with EXACTLY the expected command line (prefix, --device cpu, chunk, --start/--stop of its meta) and records its
#      start time; the new prefixes must be unused;
#  (1) waits until the 110 table rebuild of the CURRENT run is over: diag/x110_manifest.txt exists, no b1_features.py process is left, and
#      diag/x110_stage1.md or diag/x110_status.txt is newer than that manifest;
#  (2) records every generator's meta state at that moment, then stops each one right after its NEXT chunk (its meta changed), after re-checking
#      PID start time and command line (a generator that ended meanwhile is not stopped; a PID that changed identity STOPs the job);
#  (3) validates every old part: start = lo, requested_stop = hi, lo <= stop <= hi, n_jobs = stop - lo, ok + failed + rejected = stop - lo, meta
#      hashes (jobs, GLACIER checkpoint, runner, generator) = the current files, shards 0..chunks-1 present; shards beyond the meta's chunks and
#      .tmp files are moved to mall_sim/quarantine (never read); a part already complete keeps its range and gets no new part;
#  (4) covers the rest of each range [stop, hi) with K contiguous sub-ranges under NEW prefixes <prefix>s<k>, CPU, nice 19, 2 threads each,
#      the same chunk size, the children's trap set before they start;
#  (5) at the end checks that ALL parts of the directory cover [0, 2N) exactly once (contiguous) and writes the prefix list and meta hashes.
# Status line in mall_sim/status2.txt: MALL_GEN2_DONE <prefix,list> / MALL_GEN2_FAIL <reason>. O / P / B / CHUNK / X110_WAIT=0: test overrides only.
# Usage: nohup bash experiments/e115/mall_gen2.sh K <pid>:<prefix> [<pid>:<prefix> ...] &     e.g. 2 2828471:experiments/e115/mall_sim/c1 ...
cd ~/CASMI2026 || exit 1
K=${1:-}; shift
O=${O:-experiments/e115/mall_sim}; P=${P:-experiments/e115/mall}; B=${B:-experiments/b1_baseline}; CHUNK=${CHUNK:-20000}; ST=$O/status2.txt; LOG=$O/gen2.log
case "$K" in 1|2|3) ;; *) echo "K must be 1, 2 or 3"; exit 1;; esac
[ $# -ge 1 ] || { echo "usage: $0 K pid:prefix [pid:prefix ...]"; exit 1; }
exec 8>$O/gen2.lock; flock -n 8 || { echo "another mall_gen2 holds $O/gen2.lock"; exit 1; }
rm -f $ST
fail() { echo "MALL_GEN2_FAIL $* $(date "+%F %T")" | tee -a $LOG > $ST; exit 1; }
echo "== $(date "+%F %T") mall_gen2 v2 K=$K $*" >> $LOG
.venv/bin/python -I - "$P" <<'PYEOF' || fail "plan files changed"
import hashlib, json, sys
P = sys.argv[1]; m = json.load(open(f"{P}/plan_manifest.json"))
bad = [f for f, h in m["outputs"].items() if hashlib.sha256(open(f"{P}/{f}", "rb").read()).hexdigest() != h]
print("plan check", "OK" if not bad else f"FAIL {bad}"); sys.exit(1 if bad else 0)
PYEOF
N=$(.venv/bin/python -c "import json; print(json.load(open('$P/plan_manifest.json'))['catalog'])")
declare -A PFX ST0 CMD LO HI M0 DONE_
for a in "$@"; do pid=${a%%:*}; pf=${a#*:}
  [ -n "${PFX[$pid]:-}" ] && fail "PID $pid given twice"
  for q in "${PFX[@]}"; do [ "$q" = "$pf" ] && fail "prefix $pf given twice"; done
  m=$(.venv/bin/python -I -c "import json,sys; m=json.load(open(sys.argv[1]+'_meta.json')); print(m['start'], m['requested_stop'])" "$pf" 2>/dev/null) || fail "$pf has no meta"
  LO[$pid]=${m% *}; HI[$pid]=${m#* }
  want="experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $pf --device cpu --chunk $CHUNK --start ${LO[$pid]} --stop ${HI[$pid]}"
  cmd=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null) || fail "PID $pid not alive"
  [[ "$cmd" == *"$want"* ]] || fail "PID $pid is not the generator of $pf ($cmd)"
  PFX[$pid]=$pf; CMD[$pid]=$cmd; ST0[$pid]=$(awk '{print $22}' /proc/$pid/stat)
  for k in 1 2 3; do ls ${pf}s${k}_* >/dev/null 2>&1 && fail "new prefix ${pf}s${k} already used"; done
done
while [ "${X110_WAIT:-1}" = "1" ]; do   # (1) the 110 table rebuild of the current run is over
  if [ -s $B/diag/x110_manifest.txt ] && ! pgrep -f "[b]1_features.py" >/dev/null; then
    for f in $B/diag/x110_stage1.md $B/diag/x110_status.txt; do [ -s $f ] && [ $f -nt $B/diag/x110_manifest.txt ] && break 2; done
  fi
  sleep 60
done
echo "== $(date "+%F %T") trigger reached; stopping each generator right after its next chunk" >> $LOG
for pid in "${!PFX[@]}"; do M0[$pid]=$(stat -c %y ${PFX[$pid]}_meta.json); done   # meta state of ALL generators at the trigger
while [ ${#DONE_[@]} -lt ${#PFX[@]} ]; do
  for pid in "${!PFX[@]}"; do
    [ -n "${DONE_[$pid]:-}" ] && continue
    pf=${PFX[$pid]}
    if ! kill -0 $pid 2>/dev/null; then echo "== $(date "+%F %T") $pid ($pf) had already ended" >> $LOG; DONE_[$pid]=1; continue; fi
    [ "$(stat -c %y ${pf}_meta.json)" = "${M0[$pid]}" ] && continue
    [ "$(awk '{print $22}' /proc/$pid/stat 2>/dev/null)" = "${ST0[$pid]}" ] || fail "PID $pid changed identity (start time)"
    [ "$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)" = "${CMD[$pid]}" ] || fail "PID $pid changed identity (command line)"
    kill $pid; for i in $(seq 60); do kill -0 $pid 2>/dev/null || break; sleep 1; done
    kill -0 $pid 2>/dev/null && fail "PID $pid did not stop"
    echo "== $(date "+%F %T") stopped $pid ($pf) right after a chunk" >> $LOG; DONE_[$pid]=1
  done
  sleep 2
done
mkdir -p $O/quarantine
ARGS=(); for pid in "${!PFX[@]}"; do ARGS+=("${PFX[$pid]}:${LO[$pid]}:${HI[$pid]}"); done
RANGES=$(P=$P O=$O .venv/bin/python -I - "$K" "${ARGS[@]}" 2>>$LOG <<'PYEOF'
import glob, hashlib, json, os, shutil, sys
K = int(sys.argv[1]); P = os.environ["P"]; O = os.environ["O"]
fs = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
cur = {"jobs": fs(f"{P}/jobs.json"), "glacier_ckpt": fs("data/external/glacier/ckpt/glacier.pt"), "gl_runner": fs("data/external/glacier/gl_runner.py"),
       "gl_simulate": fs("experiments/e115/gl_simulate.py")}
out = []
for a in sys.argv[2:]:
    pf, lo, hi = a.rsplit(":", 2); lo, hi = int(lo), int(hi); m = json.load(open(pf + "_meta.json")); s, c = int(m["stop"]), int(m["chunks"])
    if int(m["start"]) != lo or int(m["requested_stop"]) != hi or not (lo <= s <= hi) or int(m["n_jobs"]) != s - lo: sys.exit(f"{pf}: meta range inconsistent")
    if int(m["n_ok"]) + int(m["n_fail"]) + sum(m.get("rejected", {}).values()) != s - lo: sys.exit(f"{pf}: meta counts inconsistent")
    if m.get("hashes") != cur: sys.exit(f"{pf}: meta hashes differ from the current job list / model / code")
    for k in range(c):
        if not os.path.exists(f"{pf}_{k:04d}.npz"): sys.exit(f"{pf}: confirmed shard {k} missing")
    for f in sorted(glob.glob(pf + "_[0-9]*.npz*")):
        k = int(os.path.basename(f)[len(os.path.basename(pf)) + 1:][:4])
        if f.endswith(".tmp") or k >= c:
            shutil.move(f, os.path.join(O, "quarantine", os.path.basename(f))); print(f"quarantined {f}", file=sys.stderr)
    if m.get("complete") or s == hi: continue
    step = -(-(hi - s) // K)
    for k in range(K):
        x, y = s + k * step, min(hi, s + (k + 1) * step)
        if x < y: out.append(f"{pf}s{k + 1}:{x}:{y}")
print(" ".join(out))
PYEOF
) || fail "old parts inconsistent (details in gen2.log)"
echo "== $(date "+%F %T") new ranges: ${RANGES:-none}" >> $LOG
{ echo "M_all CPU generation, re-split v2 $(date "+%F %T") N=$N K=$K old=${ARGS[*]} new=$RANGES"; for f in $P/catalog.parquet $P/jobs.json $P/jobs_pid.npy $P/plan.npy $P/plan_manifest.json \
   data/external/glacier/ckpt/glacier.pt data/external/glacier/gl_runner.py experiments/e115/gl_simulate.py experiments/e115/make_simplan.py experiments/e115/mall_gen2.sh; do
   echo "$(sha256sum $f | cut -c1-64) $f"; done; } >> $O/manifest2.txt
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=""
PIDS=()
trap 'kill ${PIDS[*]} 2>/dev/null' TERM INT
for r in $RANGES; do pf=${r%%:*}; rest=${r#*:}; a=${rest%%:*}; b=${rest#*:}
  nice -n 19 .venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier $P/jobs.json $pf --device cpu --chunk $CHUNK --start $a --stop $b > $pf.log 2>&1 & PIDS+=($!)
done
echo "== $(date "+%F %T") started ${#PIDS[@]} generators: ${PIDS[*]}" >> $LOG
FAIL=0; for p in "${PIDS[@]}"; do wait $p || FAIL=1; done
[ $FAIL -eq 0 ] || fail "a new part did not finish cleanly"
ALL=$(.venv/bin/python -I - "$N" "$O" 2>>$O/manifest2.txt <<'PYEOF'
import glob, hashlib, json, os, sys
N, O = int(sys.argv[1]), sys.argv[2]
iv = []
for f in glob.glob(os.path.join(O, "*_meta.json")):
    m = json.load(open(f)); iv.append((int(m["start"]), int(m["stop"]), f[:-len("_meta.json")]))
iv.sort(); pos = 0
for a, b, p in iv:
    if a != pos: sys.exit(f"coverage gap / overlap at {pos} ({p} starts at {a})")
    pos = b
if pos != 2 * N: sys.exit(f"coverage ends at {pos}, not {2 * N}")
for a, b, p in iv: print(hashlib.sha256(open(p + "_meta.json", "rb").read()).hexdigest(), p + "_meta.json", file=sys.stderr)
print(",".join(os.path.realpath(p) for a, b, p in iv))
PYEOF
) || fail "final coverage check (details in manifest2.txt)"
echo "MALL_GEN2_DONE $ALL $(date "+%F %T")" | tee -a $LOG > $ST
