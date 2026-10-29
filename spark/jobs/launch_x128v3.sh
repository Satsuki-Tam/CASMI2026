#!/bin/bash
# Start the 128 v3 fold-1 evaluations once the MIST v3 scores are complete (spark_x128v3.sh refuses otherwise). The reader stays withheld.
cd ~/CASMI2026 || exit 1
until [ -s experiments/mist/scores_v3/status.txt ]; do sleep 30; done
grep -q '^MIST_SCORE_DONE' experiments/mist/scores_v3/status.txt || { echo "MIST v3 scoring failed: $(cat experiments/mist/scores_v3/status.txt)"; exit 1; }
echo "$(date '+%F %T') launching x128v3 fold 1"
EXPECT_SHA=3c51a35b0f0b2082932c1618dc9fa276d0d6895fe4a57ca4db4025b4e874c71d exec bash spark/jobs/spark_x128v3.sh
