#!/bin/bash
# After the 115 A training (experiments/e115/runA/status.txt = E115_A_DONE), wait until no CPU evaluation (gen_eval2fd) runs - spark_x115.sh refuses
# to start next to one - and start the registered 115 evaluation (spark/jobs/spark_x115.sh does all of its own checks). A failed A stops here.
cd ~/CASMI2026 || exit 1
until [ -s experiments/e115/runA/status.txt ]; do sleep 60; done
grep -q '^E115_A_DONE' experiments/e115/runA/status.txt || { echo "115 A did not finish: $(cat experiments/e115/runA/status.txt)"; exit 1; }
while pgrep -f "[g]en_eval2fd" > /dev/null; do sleep 30; done
echo "$(date '+%F %T') launching x115"
exec bash spark/jobs/spark_x115.sh
