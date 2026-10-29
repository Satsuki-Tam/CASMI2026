#!/bin/bash
# 134 v2 stage 2 (134_prereg_glt_stage2.md v2): A2 = inten_encoder / inten_decoder / output_map only, explicit end-to-end intensity loss, 1,500
# updates, lr 1e-4, batch 16, warmup 100, seed 0 on data/glt/tims_s1. Order: (1) CUDA pre-check on one batch (finite gradients before clipping,
# finite parameters after the update, frozen parameters / buffers unchanged) -> (2) training -> (3) export + scope check + strict reload by the
# inference runner + scores differ from C0' on the 10-molecule check -> (4) A2 scored by the inference runner on the SAME runner inputs as the
# stored C0' scores of the four cells (data/glt/stage2_gl/gl_<cell>_c0prime.json, same runner options). The reading (x134_read.py) is separate.
# The unread v1 run A1 (CE parameters trainable, MAGMa-phase loss) is not used.
set -u
cd ~/CASMI2026 || exit 1
exec 9>$HOME/CASMI2026/spark/gpu.lock
flock 9
export PYTHONPATH=$HOME/CASMI2026/data/glt/shim_train:$HOME/CASMI2026/data/external/ms-pred-train/ms-pred/src OMP_NUM_THREADS=4 PYTHONUTF8=1
G=data/glt; R=$G/runs/A2; O=$G/stage2_a2; ST=$O/status.txt; PYG=.venv-glt/bin/python; PYI=.venv-ice/bin/python; B=experiments/b1_baseline
mkdir -p $O
fail() { echo "GLT2A2_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ -e $R/state_dict.pt ] && fail "A2 exists"
for c in panel f1G npH f1D; do [ -s $G/stage2_gl/gl_${c}_c0prime.json ] && [ -s $G/stage2_gl/gl_${c}_c0prime.json.meta.json ] || fail "C0' scores of $c missing"; done
$PYG -X utf8 experiments/glt/finetune_glt.py --data $G/tims_s1 --out $G/runs/A2_precheck --trainable inten3 --loss e2e --bs 16 --device cuda --precheck > $G/runs/A2_precheck.log 2>&1 || fail "CUDA pre-check"
echo "== $(date +%T) CUDA pre-check PASS"
$PYG -X utf8 experiments/glt/finetune_glt.py --data $G/tims_s1 --out $R --trainable inten3 --loss e2e --steps 1500 --lr 1e-4 --bs 16 --warmup 100 --seed 0 --device cuda --workers 4 > $R.log 2>&1 || fail "training"
echo "== $(date +%T) trained: $(grep -a FINETUNE_DONE $R.log | cut -c1-300)"
$PYG -X utf8 experiments/glt/export_ckpt.py --out $G/ckpt/A2.pt --weights $R/state_dict.pt --tag A2 > $O/A2_export.json 2>&1 || fail "export"
$PYG -X utf8 - <<'PYEOF' > $O/A2_scope.json 2>&1 || fail "scope check"
import json, torch, sys
c0 = torch.load("data/external/glacier/ckpt/glacier.pt", map_location="cpu", weights_only=True)["state_dict"]; a2 = torch.load("data/glt/ckpt/A2.pt", map_location="cpu", weights_only=True)["state_dict"]
TR = ("inten_encoder", "inten_decoder", "output_map")
fr_bad = [k for k in c0 if k.split(".")[0] not in TR and not torch.equal(c0[k], a2[k])]
tr_all = [k for k in c0 if k.split(".")[0] in TR]; tr_changed = [k for k in tr_all if not torch.equal(c0[k], a2[k])]
r = dict(frozen_changed=fr_bad[:10], n_frozen_changed=len(fr_bad), trainable=len(tr_all), trainable_changed=len(tr_changed), unchanged_trainable=[k for k in tr_all if k not in tr_changed][:10])
print(json.dumps(r)); sys.exit(0 if not fr_bad and len(tr_changed) > 0 else 1)
PYEOF
$PYI data/external/glacier/gl_runner.py data/external/glacier $G/c0check/in10.json $O/check10_A2.json --device cuda --site none --budget 900 --ckpt $G/ckpt/A2.pt > $O/check10_A2.log 2>&1 || fail "runner reload"
$PYG -X utf8 - <<'PYEOF' > $O/check10.json 2>&1 || fail "A2 scores equal C0' (weights not used?)"
import json, sys
a = json.load(open("data/glt/c0check/out_c0prime.json")); b = json.load(open("data/glt/stage2_a2/check10_A2.json"))
pairs = [(v, (b.get(m) or {}).get(s)) for m in a for s, v in (a[m] or {}).items() if v is not None]
n = len(pairs); none_b = sum(1 for _, w in pairs if w is None); diff = sum(1 for v, w in pairs if w is not None and abs(v - w) > 0)
print(json.dumps(dict(pairs=n, A2_missing=none_b, differing=diff))); sys.exit(0 if diff > 0 and none_b == 0 else 1)
PYEOF
echo "== $(date +%T) export checks: $(cat $O/A2_scope.json) $(cat $O/check10.json)"
for spec in "panel|$B/run_panel_fe/b1_runner_P_np250_in.json" "f1G|$B/run_f1dev/b1_runner_G_tims_crosslib_in.json" "npH|$B/run_np053_f1dev/b1_runner_NP_H_in.json" "f1D|$B/run_f1dev/b1_runner_D_np_single_in.json"; do
  IFS='|' read -r T IN <<< "$spec"
  $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $IN $O/gl_${T}_A2.json -- --device cuda --site none --budget 7200 --ckpt $G/ckpt/A2.pt > $O/gl_${T}_A2.log 2>&1 || fail "gl $T A2"
  echo "== $(date +%T) gl $T A2 $(grep -a '\[resume\] done' $O/gl_${T}_A2.log | cut -c1-90)"
done
{ for f in $R/state_dict.pt $G/ckpt/A2.pt $G/ckpt/c0prime.pt $G/stage2_gl/gl_panel_c0prime.json $G/stage2_gl/gl_f1G_c0prime.json $G/stage2_gl/gl_npH_c0prime.json $G/stage2_gl/gl_f1D_c0prime.json \
    $O/gl_panel_A2.json $O/gl_f1G_A2.json $O/gl_npH_A2.json $O/gl_f1D_A2.json experiments/glt/gl_only_eval.py experiments/glt/x134_read.py experiments/glt/finetune_glt.py; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $O/manifest.txt
echo "GLT2A2_SCORED $(date '+%F %T')" | tee $ST
