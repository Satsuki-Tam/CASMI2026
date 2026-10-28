#!/bin/bash
# 104 v2 chain (Codex 104 (3)): wait for the running v1 evaluation, quarantine its outputs unread, swap in the evaluator with the position-preservation
# asserts (staged as gen_eval2fd.py.v2), rerun the 104 dev evaluation (v2), then the top-25 dump + fam_audit2 (CPU, after the evaluation).
set -u
cd ~/CASMI2026 || exit 1
B=experiments/b1_baseline
until grep -q "E104_DONE" spark/jobs/spark_e104dev.out 2>/dev/null; do sleep 20; done
mkdir -p $B/diag/r104v1_unread && mv $B/diag/r104_* $B/diag/r104v1_unread/ 2>/dev/null; mv $B/r103_manifest_csv.txt $B/diag/r104v1_unread/ 2>/dev/null
cp $B/gen_eval2fd.py $B/diag/r104v1_unread/gen_eval2fd_v1.py && cp $B/gen_eval2fd.py.v2 $B/gen_eval2fd.py
echo "== $(date +%T) v1 quarantined; evaluator v2 $(sha256sum $B/gen_eval2fd.py | cut -c1-16)"
bash spark/jobs/spark_e104dev.sh > spark/jobs/spark_e104dev_v2.out 2>&1
echo "== $(date +%T) v2 evaluation: $(tail -1 spark/jobs/spark_e104dev_v2.out)"
sed -e 's#^until grep -q "E104_DONE".*##' spark/jobs/spark_top102.sh > spark/jobs/spark_top102_now.sh
bash spark/jobs/spark_top102_now.sh > spark/jobs/spark_top102.out 2>&1
echo "CHAIN104_DONE $(date +%T)"
