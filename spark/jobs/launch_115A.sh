#!/bin/bash
# Wait for MALL_GEN2_DONE (experiments/e115/mall_sim/status2.txt), then start the registered 115 A arm with the reported prefix list.
# spark/jobs/spark_e115_train.sh does every check itself (GPU lock, plan / pool hashes, coverage, R/A identical manifests).
cd ~/CASMI2026 || exit 1
ST=experiments/e115/mall_sim/status2.txt
until [ -s "$ST" ]; do sleep 60; done
grep -q '^MALL_GEN2_DONE ' "$ST" || { echo "generation did not finish: $(cat "$ST")"; exit 1; }
PREF=$(awk '{print $2}' "$ST")
echo "$(date '+%F %T') launching 115 A with $PREF"
exec bash spark/jobs/spark_e115_train.sh A "$PREF"
