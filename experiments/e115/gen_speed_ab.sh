#!/bin/bash
# 115 plan, M_all re-split stop condition (c) (Codex 122): the 111 training speed with the M_all CPU generators PAUSED (SIGSTOP) for W seconds vs
# RUNNING for the next W seconds. Speed = (step_last - step_first) / (t_last - t_first) over the training log lines inside each window (the logged
# "it/s" is cumulative from the start and is not used). Also records MemAvailable and swap in/out (vmstat) of each window. Reads no model result.
# Usage: bash experiments/e115/gen_speed_ab.sh <111 training log> [W=300] ["pid pid ..." = only these generators]  -> appends to experiments/e115/mall_sim/speed_ab.log
LOG=${1:?training log}; W=${2:-300}; OUT=~/CASMI2026/experiments/e115/mall_sim/speed_ab.log
G=${3:-$(pgrep -f "^[.]venv-ice/bin/python experiments/e115/gl_simulate.py data/external/glacier experiments/e115/mall/jobs.json" | tr '\n' ' ')}   # anchored on the interpreter (a shell whose command line merely contains the pattern is not matched); optional explicit PID list
[ -n "$G" ] || { echo "no M_all generator running"; exit 1; }
cont() { kill -CONT $G 2>/dev/null; }
trap cont EXIT INT TERM
t0=$(date +%s); kill -STOP $G; vmstat 30 $((W / 30)) > /tmp/vm_paused.txt; t1=$(date +%s); A1=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo); kill -CONT $G
vmstat 30 $((W / 30)) > /tmp/vm_running.txt; t2=$(date +%s); A2=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
python3 - "$LOG" "$t0" "$t1" "$t2" "$G" "$OUT" "$A1" "$A2" <<'EOF'
import datetime, re, sys
log, t0, t1, t2, g, out, a1, a2 = sys.argv[1], *map(int, sys.argv[2:5]), sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]
day = datetime.datetime.fromtimestamp(t0).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
pts = []
for l in open(log, errors="replace"):
    m = re.match(r"(\d\d):(\d\d):(\d\d) step (\d+) ", l)
    if m: pts.append((day + int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]), int(m[4])))
def rate(a, b):
    w = [p for p in pts if a <= p[0] <= b]
    return (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0]) if len(w) >= 2 and w[-1][0] > w[0][0] else float("nan")
def vm(f):
    rows = [l.split() for l in open(f) if l.strip() and l.split()[0].isdigit()][1:]   # the first vmstat row is the since-boot average
    return (sum(int(r[6]) + int(r[7]) for r in rows), min(int(r[3]) for r in rows) // 1024 if rows else -1)
rp, rr_ = rate(t0, t1), rate(t1, t2); sp, fp = vm("/tmp/vm_paused.txt"); sr, fr = vm("/tmp/vm_running.txt")
slow = (rp - rr_) / rp if rp == rp and rp > 0 else float("nan")
line = (f"{datetime.datetime.fromtimestamp(t2):%F %T} log={log} generators=[{g.strip()}] paused {rp:.3f} it/s (swap io {sp}, min free MiB {fp}) "
        f"running {rr_:.3f} it/s (swap io {sr}, min free MiB {fr}) MemAvailable GB {a1} / {a2} slowdown {slow:+.3%} -> "
        f"{'REDUCE' if (slow == slow and slow >= 0.05) or sr > 0 or min(int(a1), int(a2)) < 20 else 'ok'}")
open(out, "a").write(line + "\n"); print(line)
EOF
