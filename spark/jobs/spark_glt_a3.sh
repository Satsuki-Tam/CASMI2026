#!/bin/bash
# 141 A3 (141_prereg_gl_retrieval.md): (0) wait for the decoy candidates -> (1) technical check: technical decoys (Tanimoto order) + finetune_glt_v3
# --precheck on CUDA -> (2) hard negatives: runner input per train spectrum, C0' (c0prime.pt) GL scores, top-7 selection (fixed_k7.json) -> (3) A3
# training (1,500 updates) -> (4) export + scope check + strict runner reload + 10-molecule check -> (5) GL scoring of the cells with the SAME
# runner options (f2G with C0' and A2, every cell with A3) -> manifest. The reading (x141_read.py) is separate. GPU steps under gpu.lock.
set -u
cd ~/CASMI2026 || exit 1
export PYTHONPATH=$HOME/CASMI2026/data/glt/shim_train:$HOME/CASMI2026/data/external/ms-pred-train/ms-pred/src OMP_NUM_THREADS=4 PYTHONUTF8=1
G=data/glt; O=$G/a3; R=$G/runs/A3; ST=$O/status.txt; PY=.venv/bin/python; PYG=.venv-glt/bin/python; PYI=.venv-ice/bin/python; B=experiments/b1_baseline; DD=$G/decoys
mkdir -p $O
fail() { echo "GLT_A3_FAIL $* $(date '+%F %T')" | tee -a $ST; exit 1; }
[ -e $R/state_dict.pt ] && fail "A3 exists"
until [ -s $DD/manifest.json ]; do pgrep -f "[m]ake_glt_decoys" > /dev/null || [ -s $DD/manifest.json ] || fail "decoy builder ended without output"; sleep 30; done
echo "== $(date +%T) decoys: $(head -c 400 $DD/manifest.json | tr '\n' ' ')"
$PY -X utf8 experiments/glt/make_glt_hardneg.py --mode tech > $O/tech.log 2>&1 || fail "technical decoys"
flock spark/gpu.lock $PYG -X utf8 experiments/glt/finetune_glt_v3.py --data $G/tims_s1 --decoys $DD/tech_k7.json --out $G/runs/A3_precheck --bs 16 --device cuda --precheck > $G/runs/A3_precheck.log 2>&1 || fail "CUDA pre-check (see A3_precheck.log)"
echo "== $(date +%T) A3 pre-check PASS: $(grep -a 'L_a2\|L_ret\|grad_norm\|peak_mem\|seconds' $G/runs/A3_precheck.log | tr -s ' ' | tr '\n' ' ' | cut -c1-300)"
$PY -X utf8 experiments/glt/make_glt_hardneg.py --mode input > $O/hardneg_input.log 2>&1 || fail "hard-negative runner input"
flock spark/gpu.lock $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $DD/hardneg_runner_in.json $DD/hardneg_gl_c0prime.json \
  -- --device cuda --site none --budget 14400 --ckpt $G/ckpt/c0prime.pt > $DD/hardneg_gl.log 2>&1 || fail "C0' scoring of the candidates"
$PY -X utf8 experiments/glt/make_glt_hardneg.py --mode select > $O/select.log 2>&1 || fail "selection"
echo "== $(date +%T) hard negatives: $(grep -a '"k"\|fewer\|none' $O/select.log | tr -s ' ' | tr '\n' ' ')"
flock spark/gpu.lock $PYG -X utf8 experiments/glt/finetune_glt_v3.py --data $G/tims_s1 --decoys $DD/fixed_k7.json --out $R --steps 1500 --lr 1e-4 --bs 16 --warmup 100 --seed 0 --device cuda --workers 4 > $R.log 2>&1 || fail "training"
echo "== $(date +%T) trained: $(grep -a FINETUNE_DONE $R.log | cut -c1-260)"
$PYG -X utf8 experiments/glt/export_ckpt.py --out $G/ckpt/A3.pt --weights $R/state_dict.pt --tag A3 > $O/A3_export.json 2>&1 || fail "export"
$PYG -X utf8 experiments/glt/a3_checks.py scope > $O/A3_scope.json 2>&1 || fail "scope check"
$PYI data/external/glacier/gl_runner.py data/external/glacier $G/c0check/in10.json $O/check10_A3.json --device cuda --site none --budget 900 --ckpt $G/ckpt/A3.pt > $O/check10_A3.log 2>&1 || fail "runner reload"
$PYG -X utf8 experiments/glt/a3_checks.py check10 > $O/check10.json 2>&1 || fail "A3 scores equal C0' (weights not used?)"
echo "== $(date +%T) export checks: $(cat $O/A3_scope.json) $(cat $O/check10.json)"
sc() { flock spark/gpu.lock $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $1 $O/gl_$2_$3.json -- --device cuda --site none --budget 7200 --ckpt $G/ckpt/$3.pt > $O/gl_$2_$3.log 2>&1 || fail "gl $2 $3"
  echo "== $(date +%T) gl $2 $3 $(grep -a '\[resume\] done' $O/gl_$2_$3.log | cut -c1-80)"; }
sc $B/run_f2dev/b1_runner_G_tims_crosslib_in.json f2G c0prime
sc $B/run_f2dev/b1_runner_G_tims_crosslib_in.json f2G A2
for spec in "f1G|$B/run_f1dev/b1_runner_G_tims_crosslib_in.json" "f2G|$B/run_f2dev/b1_runner_G_tims_crosslib_in.json" "npH|$B/run_np053_f1dev/b1_runner_NP_H_in.json" "f1D|$B/run_f1dev/b1_runner_D_np_single_in.json" "panel|$B/run_panel_fe/b1_runner_P_np250_in.json"; do
  IFS='|' read -r T IN <<< "$spec"; sc $IN $T A3; done
{ for f in $DD/cands.parquet $DD/fixed_k7.json $DD/hardneg_gl_c0prime.json $R/state_dict.pt $G/ckpt/A3.pt $G/ckpt/A2.pt $G/ckpt/c0prime.pt $O/gl_*.json $G/stage2_gl/gl_*_c0prime.json $G/stage2_a2/gl_*_A2.json \
    experiments/glt/finetune_glt_v3.py experiments/glt/make_glt_decoys.py experiments/glt/make_glt_hardneg.py experiments/glt/gl_only_eval.py experiments/glt/x141_read.py; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $O/manifest.txt
echo "GLT_A3_SCORED $(date '+%F %T')" | tee -a $ST
