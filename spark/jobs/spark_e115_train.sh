#!/bin/bash
# 115 v2 (reports/agent_review/115_plan.md "v2 の固定値", Codex 118 / 119): trains ONE arm of the registered main comparison with the fixed recipe
# and runs the completion check. R = real only (--sim_frac 0, may start before the M_all generation is complete); A = --sim_frac 0.25 over the
# FIXED plan experiments/e115/mall, the generation parts given as a comma list of prefixes (the trainer itself checks the plan / pool hashes, exact
# coverage of the job list, NPZ structure and recorded failures <= 1%, and stops otherwise).
# Recipe (identical for R / A, fixed before any result): init = public fpnet_fold1 (sha 1739d568...), S = 24,000 updates, batch 256, K 63, lr 1e-4,
# wd 0.01, warmup 500, merge_p 0.3, w_bce 1, w_el 0.1, seed 0, 6 loader workers, holdout 'hold,np' (the f1s1 split, already built and audited in
# runR / runA), cuda. The completion check (ck115_check.py) uses the REGISTERED trainer sha256 below, not the file's current hash.
# Gate: refuses to start while any 110 / 111 / fold-2 / c1-bank job, trainer, GLACIER scorer or main evaluation runs, or while the other arm trains.
# Status line in <run>/status.txt: E115_<ARM>_DONE / E115_<ARM>_FAIL <reason>. Usage: bash spark/jobs/spark_e115_train.sh R
#                                                                                      bash spark/jobs/spark_e115_train.sh A <prefix>[,<prefix>...]
set -u
cd ~/CASMI2026 || exit 1
ARM=${1:-}; S=24000; E=experiments/e115; H=$HOME/CASMI2026
TRAINER_SHA=67ca8f213ca3109729d7f60a97822ade4f3bcdacc546929fc03c005643feaa48
INIT_SHA=1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4; BITS_SHA=c3869e86449d6fed6e79e9655f8a7d35bd55c3138ecddfc1dae5072627e78677
case "$ARM" in
  R) RUN=$E/runR; TAG=e115R; SIM=();;
  A) RUN=$E/runA; TAG=e115A; [ -n "${2:-}" ] || { echo "A needs the generation prefixes"; exit 1; }   # prefixes made absolute (the trainer runs inside the run dir)
     PREF=$(echo "$2" | tr ',' '\n' | while read -r p; do realpath -m "$p"; done | paste -sd,); SIM=(--sim_dir $H/$E/mall --sim_out "$PREF" --sim_frac 0.25);;
  *) echo "usage: $0 R | A <prefix>[,<prefix>...]"; exit 1;;
esac
ST=$H/$RUN/status.txt
fail() { echo "E115_${ARM}_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
for p in "[s]park_x110" "[s]park_n111" "[t]rain_n111.py" "[t]rain_fivefold.py" "[s]park_fpnet_f2s1" "[s]park_c1bank" "[g]l_runner.py" "[g]en_eval2fd" "[t]rain_fpaug2.py"; do
  if pgrep -f "$p" >/dev/null; then echo "refused: '$p' is running ($(date '+%F %T'))"; exit 1; fi; done
[ "$(sha256sum $E/train_fpaug2.py | cut -c1-64)" = "$TRAINER_SHA" ] || { echo "refused: train_fpaug2.py is not the registered version"; exit 1; }
{ [ -s $RUN/split_audit.json ] && [ -s $RUN/check_inputs.json ] && [ -s $RUN/work/fp_bits.npy ]; } || { echo "refused: $RUN lacks its split / input audits"; exit 1; }
{ [ -e $RUN/${TAG}_final.pt ] || [ -e $RUN/${TAG}_receipt.json ]; } && { echo "refused: $RUN already holds $TAG (fresh output only)"; exit 1; }
rm -f $ST
{ echo "== $(date '+%F %T') 115 arm $ARM, tag $TAG, S $S, sim ${SIM[*]:-none}"; nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv,noheader; } > $RUN/${TAG}_job.log
.venv/bin/python -X utf8 $E/train_fpaug2.py --code $H/data/external/v3_models/code --run $H/$RUN --init $H/data/external/fpnet_fold1_as_fold0/fpnet_fold0.pt \
  --init_sha $INIT_SHA --bits_sha $BITS_SHA --folds $H/data/external/identity_folds/structures.parquet --tag $TAG --steps $S --bs 256 --K 63 --lr 1e-4 \
  --wd 0.01 --warmup 500 --merge_p 0.3 --w_bce 1 --w_el 0.1 --workers 6 --seed 0 --holdout hold,np --device cuda --max_fail 0.01 "${SIM[@]}" \
  > $RUN/$TAG.log 2>&1; rc=$?
echo "== $(date '+%F %T') trainer rc=$rc" >> $RUN/${TAG}_job.log; [ $rc -eq 0 ] || fail "trainer rc=$rc ($(tail -1 $RUN/$TAG.log | cut -c1-200))"
.venv/bin/python -I $E/ck115_check.py $RUN $TAG $S $ARM $TRAINER_SHA > $RUN/${TAG}_ck115.log 2>&1; rc=$?
grep -a -E "^(PASS|FAIL)" $RUN/${TAG}_ck115.log >> $RUN/${TAG}_job.log; [ $rc -eq 0 ] || fail "completion check rc=$rc"
echo "E115_${ARM}_DONE $(date '+%F %T')" | tee $ST
