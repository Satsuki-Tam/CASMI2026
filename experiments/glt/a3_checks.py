"""141 A3 export checks (same as 134's A2 checks): scope = frozen tensors bit-equal to the released checkpoint, trainable (inten3) changed;
check10 = the A3 runner scores on the 10-molecule check differ from C0' with no missing pair. Usage: python a3_checks.py scope|check10"""
import json, sys
import torch
mode = sys.argv[1]
if mode == "scope":
    c0 = torch.load("data/external/glacier/ckpt/glacier.pt", map_location="cpu", weights_only=True)["state_dict"]; a3 = torch.load("data/glt/ckpt/A3.pt", map_location="cpu", weights_only=True)["state_dict"]
    TR = ("inten_encoder", "inten_decoder", "output_map")
    fr_bad = [k for k in c0 if k.split(".")[0] not in TR and not torch.equal(c0[k], a3[k])]; tr_all = [k for k in c0 if k.split(".")[0] in TR]; tr_ch = [k for k in tr_all if not torch.equal(c0[k], a3[k])]
    r = dict(frozen_changed=fr_bad[:10], n_frozen_changed=len(fr_bad), trainable=len(tr_all), trainable_changed=len(tr_ch)); print(json.dumps(r)); sys.exit(0 if not fr_bad and tr_ch else 1)
a = json.load(open("data/glt/c0check/out_c0prime.json")); b = json.load(open("data/glt/a3/check10_A3.json"))
pairs = [(v, (b.get(m) or {}).get(s)) for m in a for s, v in (a[m] or {}).items() if v is not None]
r = dict(pairs=len(pairs), A3_missing=sum(1 for _, w in pairs if w is None), differing=sum(1 for v, w in pairs if w is not None and abs(v - w) > 0)); print(json.dumps(r)); sys.exit(0 if r["differing"] > 0 and r["A3_missing"] == 0 else 1)
