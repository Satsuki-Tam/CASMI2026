#!/bin/bash
# 132 parity (B) (132_prereg_elite_public.md): the E-lite pipeline (experiments/b1_elite) on the 250 panel molecules, both views, evaluation mode,
# same settings as the 087 parity (pc_parity087.sh) with GLACIER reused from the 087 runs (--gl_json; no forward run), against the SAME-PC evaluator
# table run_panel_fe_pc: b1_parity_e132.py must reproduce P (submission_pref.csv) and the E-lite list (submission.csv) exactly (ordered top-25
# official identities, top-1, RR, every molecule) and the E membership of every shared candidate. FPNet runs on the GPU (as when the table was
# built), so the job waits for the PC-GPU window (00:00-09:00 JST) and refuses if another CUDA process is present. No --solution in the pipeline
# runs (no score printed); the solution file is read only by the parity script.
# v2 (Codex 132): each pipeline starts only before 08:00 and is stopped at 08:55 (timeout) -> incomplete = FAIL (the scope is never reduced);
# the parity script runs in its complete E-lite mode (roster / ids / sets checked); the job exits 1 on any FAIL.
set -u
cd /c/kaggle/CASMI || exit 1
until [ "$(date +%H)" -lt 9 ]; do sleep 60; done
GPU_APPS=$(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>&1); rc=$?
PY_APPS=$(echo "$GPU_APPS" | grep -i "python" || true)   # Windows lists the display (C+G) processes too: refuse only for another Python / CUDA job
{ [ $rc -eq 0 ] && [ -z "$PY_APPS" ]; } || { echo "refused: a Python GPU process is present or nvidia-smi failed: rc=$rc $PY_APPS ($(date '+%F %T'))"; exit 1; }
echo "== $(date '+%F %T') GPU check: non-Python GPU clients only ($(echo "$GPU_APPS" | wc -l) listed)"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1
B=experiments/b1_baseline; S=experiments/b1_elite; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; FRUN=$B/run_panel_fe_pc; MODEL=$B/rank_v8w7a/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt; EM=$B/rank_e1r/lambdarank.txt; EK=$B/diag/e_window_keys_v2.parquet
EMS=8f4a81b5f8ba7f589cfd74980ea40075169121b2ce1382cb92a1f2aa150ec1f5; EKS=f572682b47a882de18bbe3ded9129fa0544e3c52281447e90f7bc3f13042a672
echo "== $(date '+%F %T') pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) elite $(sha256sum $S/elite.py | cut -c1-12) parity $(sha256sum $S/b1_parity_e132.py | cut -c1-12) model $(sha256sum $MODEL | cut -c1-12)"
FAIL=0
for mode in c2 c1; do
  W=$E/run_e132_${mode}; G=$E/run_v8w7a_${mode}
  [ -e $W ] && { echo "refused: $W exists"; exit 1; }
  H=$((10#$(date +%H))); [ $H -lt 8 ] || { echo "== $(date +%T) pipeline $mode NOT started: past 08:00, the GPU part must end before 09:00 (Codex 132) -> incomplete"; FAIL=1; continue; }
  LEFT=$(( $(date -d "today 08:55" +%s) - $(date +%s) )); [ $LEFT -gt 600 ] || { echo "== $(date +%T) pipeline $mode NOT started: less than 10 min before 08:55 -> incomplete"; FAIL=1; continue; }
  timeout $LEFT $PY -X utf8 $S/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_$mode.json --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0 --analog_w_fallback 1 --analog_feat ap --frag_w_fallback 1 \
    --gl_json $G/gl_out.json --elite_model $EM --elite_keys $EK --elite_model_sha $EMS --elite_keys_sha $EKS > $W.log 2>&1
  rc=$?; echo "== $(date +%T) pipeline $mode exit $rc (124 = stopped at the 08:55 deadline) $(grep -a '132 E-lite: [0-9]' $W.log | tail -1 | cut -c1-200)"; [ $rc = 0 ] || FAIL=1
done
for mode in c2 c1; do
  W=$E/run_e132_${mode}; G=$E/run_v8w7a_${mode}
  [ -s $W/submission.csv ] || { FAIL=1; continue; }
  $PY -X utf8 $S/b1_parity_e132.py --dump $W/b1_candidates.parquet --features_run $FRUN --view $mode --solution $E/solution.csv --out $W/parity_${mode}.md \
    --pred_main $W/submission_pref.csv --pred_fixed $W/submission_fixed.csv --stage_stats $W/b1_stage_stats.csv --model $MODEL --w_ice 0 --tau 0.9 --main blend21 \
    --margin 0.2 --min_gl_cover 0.5 --pipe_work $G --forward_from pipe --top25_set_min_share 1.0 --top25_min_share 1.0 --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
    --analog_parquet $B/diag/analog3_fe_pcpc.parquet --frag_w_fallback 1 --frag_parquet $B/diag/frag_panel_pc.parquet \
    --elite_model $EM --elite_keys $EK --pred_elite $W/submission.csv > $W/parity.log 2>&1
  rc=$?; echo "parity132 $mode exit $rc $(tail -1 $W/parity.log | cut -c1-250)"; [ $rc = 0 ] || FAIL=1
  $PY -X utf8 -c "
import sys, pandas as pd
a = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False).set_index('molecule_id').smiles; b = pd.read_csv(sys.argv[2], dtype=str, keep_default_na=False).set_index('molecule_id').smiles
d = [m for m in a.index if m not in b.index or a[m] != b[m]]
print('descriptive: P of this run vs the 087 run main list:', len(a), 'molecules,', len(d), 'differ', d[:3])" $W/submission_pref.csv $G/submission.csv
done
if [ $FAIL = 0 ]; then echo "PARITY132_DONE PASS $(date '+%F %T')"; exit 0; fi   # Codex 132: FAIL -> non-zero exit
echo "PARITY132_DONE FAIL $(date '+%F %T')"; exit 1
