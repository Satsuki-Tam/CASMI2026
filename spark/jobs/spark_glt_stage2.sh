#!/bin/bash
# 105 / 134 stage 2 (134_prereg_glt_stage2.md): train the registered variant A1 (intensity side, 1,500 updates, lr 1e-4, batch 16, seed 0) on
# data/glt/tims_s1 under the shared GPU lock, export it, check the export (frozen tensors bit-equal to the released checkpoint, trainable tensors
# changed, strict reload by the inference runner, scores on the 10-molecule check input differ from C0'), then score C0' and A1 with the
# inference runner on the SAME runner inputs of the four registered cells (panel P_np250, f1dev G_tims_crosslib, np053f1dev NP_H,
# f1dev D_np_single). The GL-only reading (gl_only_eval.py) is run separately after the registration is final.
set -u
cd ~/CASMI2026 || exit 1
exec 9>$HOME/CASMI2026/spark/gpu.lock
flock 9
export PYTHONPATH=$HOME/CASMI2026/data/glt/shim_train:$HOME/CASMI2026/data/external/ms-pred-train/ms-pred/src OMP_NUM_THREADS=4 PYTHONUTF8=1
G=data/glt; R=$G/runs/A1; ST=$G/stage2_status.txt; PYG=.venv-glt/bin/python; PYI=.venv-ice/bin/python; B=experiments/b1_baseline
fail() { echo "GLT2_FAIL $* $(date '+%F %T')" | tee $ST; exit 1; }
[ -e $R/state_dict.pt ] && fail "A1 exists"
$PYG -X utf8 experiments/glt/finetune_glt.py --data $G/tims_s1 --out $R --trainable inten --steps 1500 --lr 1e-4 --bs 16 --warmup 100 --seed 0 --device cuda --workers 4 > $R.log 2>&1 || fail "training"
echo "== $(date +%T) trained: $(tail -1 $R.log | cut -c1-160)"
$PYG -X utf8 experiments/glt/export_ckpt.py --out $G/ckpt/A1.pt --weights $R/state_dict.pt --tag A1 > $G/ckpt/A1_export.json 2>&1 || fail "export"
$PYG -X utf8 - <<'PYEOF' > $G/ckpt/A1_scope.json 2>&1 || fail "scope check"
import json, torch, sys
c0 = torch.load("data/external/glacier/ckpt/glacier.pt", map_location="cpu", weights_only=True)["state_dict"]; a1 = torch.load("data/glt/ckpt/A1.pt", map_location="cpu", weights_only=True)["state_dict"]
TR = ("inten_encoder", "inten_decoder", "output_map", "collision_embed_merged", "collision_embedder_denominators")
fr_bad = [k for k in c0 if k.split(".")[0] not in TR and not torch.equal(c0[k], a1[k])]
tr_changed = [k for k in c0 if k.split(".")[0] in TR and not torch.equal(c0[k], a1[k])]; tr_all = [k for k in c0 if k.split(".")[0] in TR]
r = dict(frozen_changed=fr_bad[:10], n_frozen_changed=len(fr_bad), trainable=len(tr_all), trainable_changed=len(tr_changed), unchanged_trainable=[k for k in tr_all if k not in tr_changed][:10])
print(json.dumps(r)); sys.exit(0 if not fr_bad and len(tr_changed) > 0 else 1)
PYEOF
mkdir -p $G/stage2_gl
$PYI data/external/glacier/gl_runner.py data/external/glacier $G/c0check/in10.json $G/stage2_gl/check10_A1.json --device cuda --site none --budget 900 --ckpt $G/ckpt/A1.pt > $G/stage2_gl/check10_A1.log 2>&1 || fail "runner reload"
$PYG -X utf8 - <<'PYEOF' > $G/stage2_gl/check10.json 2>&1 || fail "A1 scores equal C0' (weights not used?)"
import json, sys
a = json.load(open("data/glt/c0check/out_c0prime.json")); b = json.load(open("data/glt/stage2_gl/check10_A1.json"))
pairs = [(v, (b.get(m) or {}).get(s)) for m in a for s, v in (a[m] or {}).items() if v is not None]
n = len(pairs); none_b = sum(1 for _, w in pairs if w is None); diff = sum(1 for v, w in pairs if w is not None and abs(v - w) > 0)
print(json.dumps(dict(pairs=n, A1_missing=none_b, differing=diff))); sys.exit(0 if diff > 0 and none_b == 0 else 1)
PYEOF
echo "== $(date +%T) export checks: $(cat $G/ckpt/A1_scope.json) $(cat $G/stage2_gl/check10.json)"
for spec in "panel|$B/run_panel_fe/b1_runner_P_np250_in.json" "f1G|$B/run_f1dev/b1_runner_G_tims_crosslib_in.json" "npH|$B/run_np053_f1dev/b1_runner_NP_H_in.json" "f1D|$B/run_f1dev/b1_runner_D_np_single_in.json"; do
  IFS='|' read -r T IN <<< "$spec"
  for K in c0prime A1; do
    $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $IN $G/stage2_gl/gl_${T}_$K.json -- --device cuda --site none --budget 7200 --ckpt $G/ckpt/$K.pt > $G/stage2_gl/gl_${T}_$K.log 2>&1 || fail "gl $T $K"
    echo "== $(date +%T) gl $T $K $(grep -a '\[resume\] done' $G/stage2_gl/gl_${T}_$K.log | cut -c1-90)"
  done
done
{ for f in $R/state_dict.pt $G/ckpt/A1.pt $G/ckpt/c0prime.pt $G/stage2_gl/gl_*.json; do echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $G/stage2_manifest.txt
echo "GLT2_SCORED $(date '+%F %T')" | tee $ST
