#!/bin/bash
# Copy a B1 run's small outputs (features, molecules, forward-model scores, results) from the Spark to the PC.
# Usage: bash spark/fetch_run.sh experiments/b1_baseline/run_p1
RUN=$1
SSH_OPTS="-i $HOME/.ssh/spark_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes"
mkdir -p "/c/kaggle/CASMI/$RUN/work" "/c/kaggle/CASMI/$RUN/results"
scp $SSH_OPTS -q "svlg@spark-8fda.local:~/CASMI2026/$RUN/b1_features_*.parquet" "svlg@spark-8fda.local:~/CASMI2026/$RUN/b1_molecules_*.csv" "svlg@spark-8fda.local:~/CASMI2026/$RUN/features.log" "/c/kaggle/CASMI/$RUN/" 2>/dev/null
scp $SSH_OPTS -q "svlg@spark-8fda.local:~/CASMI2026/$RUN/work/*.json" "svlg@spark-8fda.local:~/CASMI2026/$RUN/work/*.meta.json" "/c/kaggle/CASMI/$RUN/work/" 2>/dev/null
scp $SSH_OPTS -q "svlg@spark-8fda.local:~/CASMI2026/$RUN/results/*" "/c/kaggle/CASMI/$RUN/results/" 2>/dev/null
scp $SSH_OPTS -q "svlg@spark-8fda.local:~/CASMI2026/$RUN/runners.log" "/c/kaggle/CASMI/$RUN/" 2>/dev/null
ls -la "/c/kaggle/CASMI/$RUN" "/c/kaggle/CASMI/$RUN/work" | head -30
