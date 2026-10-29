#!/bin/bash
# W135 (136 step 2): build the remaining design worlds at pi3 = 0.3 (tables, GL, world P; no reach is computed). Two at a time on CPU; GL serialised by gpu.lock.
cd ~/CASMI2026 || exit 1
( bash spark/jobs/spark_w135_world.sh dF2 30 > logs/w135_dF2_p30.log 2>&1; bash spark/jobs/spark_w135_world.sh dF3 30 > logs/w135_dF3_p30.log 2>&1; bash spark/jobs/spark_w135_world.sh dR3 30 > logs/w135_dR3_p30.log 2>&1 ) &
( bash spark/jobs/spark_w135_world.sh dR1 30 > logs/w135_dR1_p30.log 2>&1; bash spark/jobs/spark_w135_world.sh dR2 30 > logs/w135_dR2_p30.log 2>&1 ) &
wait
echo "W135_P30_REST_DONE $(date '+%F %T')"
