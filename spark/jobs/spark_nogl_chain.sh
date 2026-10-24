#!/bin/bash
# Codex 017 proposal 1: a fallback-branch ranker trained WITHOUT the GL features (same tables, drop list and C1 replication as rank_v4b), then
# probes on the same molecules as rank_v4b: dev2 strata (run_p2dev_v3), the panel (run_panel_v3b) and the dev sets (run_v3b_eval), both views.
# The probe CSVs (diag/probe_*_rank_v4b_nogl_{c1,c2}.csv) are compared with the rank_v4b CSVs on the GL-uncovered molecules (gl_ok == False).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python
RUNS="$B/run_v3_p1:experiments/p1_baseline/run1/p1_molecules.csv:fit $B/run_v3_eval:$B/eval_set/p1_molecules.csv $B/run_v3_c1:$B/eval_c1/p1_molecules.csv"
echo "== $(date +%T) train rank_v4b_nogl (v2_noice minus z_gl/gl/gl_missing; drop lib_nref in_train; c1_repeat 3)"
$PY -X utf8 $B/b1_rank_train.py --runs $RUNS --out $B/rank_v4b_nogl --feats v2_noice --drop lib_nref in_train z_gl gl gl_missing --c1_repeat 3 > $B/rank_v4b_nogl_train.log 2>&1; echo "train exit $?"
grep -a "^features\|fit groups" $B/rank_v4b_nogl_train.log | cut -c1-200
$PY -c "import json; d=json.load(open('$B/rank_v4b_nogl/rank_results.json')); print('EVAL lambdarank', {k: round(v['strict'],3) for k,v in d['eval_lambdarank'].items()}, 'fixed', {k: round(v['strict'],3) for k,v in d['eval_fixed'].items()})"
for P in "run_p2dev_v3 E_np_negonly p2dev_E" "run_p2dev_v3 F_np_uncovered p2dev_F" "run_p2dev_v3 G_tims_crosslib p2dev_G" "run_p2dev_v3 C_np_crosslib p2dev_C" "run_panel_v3b P_np250 panel_v3b" "run_v3b_eval A_timstof A_v3b" "run_v3b_eval B_nplib B_v3b"; do
  set -- $P; echo "-- probe $3 rank_v4b_nogl"
  $PY -X utf8 $B/b1_learned_probe.py --run $B/$1 --set $2 --model $B/rank_v4b_nogl/lambdarank.txt --w_ice 0 --views c1 c2 --guards 0.9:0.2 --label ${3}_rank_v4b_nogl --out $B/diag/probe_${3}_rank_v4b_nogl.md 2>&1 | grep -a "^## view\|^| learned \|^| pipeline \|^| fixed \|^| lib \|^| guard\|Traceback\|Error" | cut -c1-160
done
echo "NOGL_DONE $(date +%T)"
