#!/bin/bash
# 115 A was refused at 15:38 because CPU-only evaluations (gen_eval2fd) were running (the registered start check of spark_e115_train.sh).
# Wait until no gen_eval2fd process runs (127 learning curve / pop0 local cost finish), start the registered 115 A arm with the MALL_GEN2_DONE
# prefix list, and once its training log shows progress, restart the 128 fold-1 evaluations (CPU; the reader stays withheld until the review).
cd ~/CASMI2026 || exit 1
ST=experiments/e115/mall_sim/status2.txt
grep -q '^MALL_GEN2_DONE ' "$ST" || { echo "generation not done: $(cat "$ST")"; exit 1; }
PREF=$(awk '{print $2}' "$ST")
while pgrep -f "[g]en_eval2fd" > /dev/null; do sleep 30; done
echo "$(date '+%F %T') launching 115 A with $PREF"
nohup bash spark/jobs/spark_e115_train.sh A "$PREF" > logs/spark_e115A_run.log 2>&1 < /dev/null &
for i in $(seq 1 60); do
  sleep 20
  if grep -q " step " experiments/e115/runA/e115A.log 2>/dev/null; then break; fi
  if ! pgrep -f "[s]park_e115_train.sh A" > /dev/null; then echo "$(date '+%F %T') 115 A is not running: $(tail -2 logs/spark_e115A_run.log)"; exit 1; fi
done
echo "$(date '+%F %T') 115 A training started; restarting the 128 evaluations"
EXPECT_SHA=7757b7e2caedf6ee512bb3b2d0ae33a10306eacd4ee39ac34553da0f00e2c2b7 nohup bash spark/jobs/spark_x128.sh > logs/spark_x128.log 2>&1 < /dev/null &
echo "$(date '+%F %T') done"
