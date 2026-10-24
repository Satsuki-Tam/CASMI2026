#!/bin/bash
# v3b: re-compute the B1 feature tables with the C1 reference-selection fix (Codex 012: exclusion before MAX_REF), reusing forward scores,
# then retrain the ranker on the corrected tables and probe it. Sequential (one features job at a time, 16 workers). Markers per stage.
#   stage 1: run_v3b_c1 (dev C1 set), run_v3b_eval (tune/eval A+B), run_v3b_p1 (fit A+B)            -> V3B_TRAIN_TABLES_DONE
#   stage 2: rank_v5a (drop lib_nref/in_train), rank_v5b (+ C1 fit groups x3); probes on dev C1 set / eval A,B  -> V3B_TRAIN_DONE
#   stage 3: run_v3b_locked (locked set; NOT scored here), run_panel_v3b (panel, v3 shortlist) + probes       -> V3B_LOCKED_DONE / V3B_PANEL_DONE
#   stage 4: run_locked_v2b (M1 frozen control's locked tables with the corrected C1 view; GL+ICE seeded)      -> V2B_LOCKED_DONE
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; J=spark/jobs/b1_features_job_v3b.sh
V3="--k_fpp 200 --k_pop 50"; V2="--k_fpp 100 --k_pop 0"
echo "== $(date +%T) v3b chain start (b1_features sha $(sha256sum $B/b1_features.py | cut -c1-16))"
OLD_RUN=$B/run_v3_c1   FEAT_ARGS="$V3" RUNNERS=gl bash $J $B/eval_c1/p1_molecules.csv $B/run_v3b_c1 B_nplib
OLD_RUN=$B/run_v3_eval FEAT_ARGS="$V3" RUNNERS=gl bash $J $B/eval_set/p1_molecules.csv $B/run_v3b_eval A_timstof B_nplib
OLD_RUN=$B/run_v3_p1   FEAT_ARGS="$V3" RUNNERS=gl bash $J experiments/p1_baseline/run1/p1_molecules.csv $B/run_v3b_p1 A_timstof B_nplib
echo "V3B_TRAIN_TABLES_DONE $(date +%T)"
RUNS="$B/run_v3b_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3b_eval:$B/eval_set/p1_molecules.csv $B/run_v3b_c1:$B/eval_c1/p1_molecules.csv"
export OMP_NUM_THREADS=4
for V in a b; do
  if [ $V = a ]; then OPT="--drop lib_nref in_train"; else OPT="--drop lib_nref in_train --c1_repeat 3"; fi
  echo "== $(date +%T) train rank_v5$V [$OPT] on the corrected tables"
  $PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_v5$V --feats v2_noice $OPT > $B/rank_v5${V}_train.log 2>&1; echo "train exit $?"
  grep -a "^selected\|^features\|fit groups after" $B/rank_v5${V}_train.log | cut -c1-200
  $PY -c "import json; d=json.load(open(\"$B/rank_v5$V/rank_results.json\")); print(\"EVAL lambdarank\", {k: round(v[\"strict\"],3) for k,v in d[\"eval_lambdarank\"].items()}, \"fixed\", {k: round(v[\"strict\"],3) for k,v in d[\"eval_fixed\"].items()}, \"delta\", {k: (round(v[\"delta_strict\"],3), [round(x,3) for x in v[\"ci95_strict\"]]) for k,v in d[\"eval_delta\"].items()}); print(\"importance\", sorted(d[\"importance\"].items(), key=lambda kv: -kv[1])[:10])"
  for P in "run_v3b_c1 B_nplib c1set_v3b" "run_v3b_eval A_timstof A_v3b" "run_v3b_eval B_nplib B_v3b"; do
    set -- $P; echo "-- probe $3 rank_v5$V"; $PY -X utf8 $B/b1_learned_probe.py --run $B/$1 --set $2 --model $B/rank_v5$V/lambdarank.txt --w_ice 0 --views c1 c2 --guards 0.8:0.2,0.9:0.2 --out $B/diag/probe_$3_rank_v5$V.md 2>&1 | grep -a "^## view\|^| learned \|^| pipeline \|^| fixed \|^| lib \|^learned loses" | cut -c1-160
  done
done
# the frozen candidates on the corrected tables (same probes), for the paired comparison later
for M in "rank_v3 0" "rank_v4b 0"; do set -- $M
  for P in "run_v3b_c1 B_nplib c1set_v3b" "run_v3b_eval A_timstof A_v3b" "run_v3b_eval B_nplib B_v3b"; do set -- $P $M
    echo "-- probe $3 $4"; $PY -X utf8 $B/b1_learned_probe.py --run $B/$1 --set $2 --model $B/$4/lambdarank.txt --w_ice $5 --views c1 c2 --guards 0.8:0.2,0.9:0.2 --out $B/diag/probe_$3_$4_v3btables.md 2>&1 | grep -a "^## view\|^| learned \|^| fixed \|^| lib " | cut -c1-160
  done
done
echo "V3B_TRAIN_DONE $(date +%T)"
export OMP_NUM_THREADS=1
OLD_RUN=$B/run_v3_locked FEAT_ARGS="$V3" RUNNERS=gl bash $J $B/locked_eval/p1_molecules.csv $B/run_v3b_locked A_timstof B_nplib > $B/run_v3b_locked_job.log 2>&1
echo "V3B_LOCKED_DONE $(date +%T) (not scored; log in run_v3b_locked_job.log)"
OLD_RUN=$B/run_panel_v2 FEAT_ARGS="$V3" RUNNERS="gl ice" bash $J $B/panel_np250/p1_molecules.csv $B/run_panel_v3b P_np250
export OMP_NUM_THREADS=4
for M in "rank_v5a 0" "rank_v5b 0" "rank_v4b 0" "rank_v3 0"; do set -- $M
  echo "-- probe panel_v3b $1"; $PY -X utf8 $B/b1_learned_probe.py --run $B/run_panel_v3b --set P_np250 --model $B/$1/lambdarank.txt --w_ice $2 --views c1 c2 --guards 0.8:0.2,0.9:0.2 --out $B/diag/probe_panel_v3b_$1.md 2>&1 | grep -a "^## view\|^| learned \|^| pipeline \|^| fixed \|^| lib \|^learned loses" | cut -c1-160
done
echo "V3B_PANEL_DONE $(date +%T)"
export OMP_NUM_THREADS=1
OLD_RUN=$B/run_locked_v2 FEAT_ARGS="$V2" RUNNERS="gl ice" bash $J $B/locked_eval/p1_molecules.csv $B/run_locked_v2b A_timstof B_nplib > $B/run_locked_v2b_job.log 2>&1
echo "V2B_LOCKED_DONE $(date +%T) (not scored)"
echo "V3B_ALL_DONE $(date +%T)"
