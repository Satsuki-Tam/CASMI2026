"""105 stage 1: export a GLACIER JointModel (the released checkpoint, optionally with fine-tuned weights) to the released file format
{'hyper_parameters', 'state_dict', 'source'} that data/external/glacier/gl_runner.py --ckpt loads (weights_only, JointModel(**hp), strict).
--weights none = C0' (the released weights passed through the training environment unchanged: every tensor must equal the original bitwise).
Usage (Spark, .venv-glt): python experiments/glt/export_ckpt.py --out data/glt/ckpt/c0prime.pt [--weights finetuned_state_dict.pt] [--tag NAME]"""
import argparse, hashlib, json, os, sys
import torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]): sys.path.insert(0, p)
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--weights", default="none"); ap.add_argument("--tag", default="c0prime"); a = ap.parse_args()
from ms_pred.glacier.joint_model import JointModel
SRC = os.path.join(ROOT, "data/external/glacier/ckpt/glacier.pt")
c = torch.load(SRC, map_location="cpu", weights_only=True); hp = {k: v for k, v in dict(c["hyper_parameters"]).items() if not str(k).startswith("_")}
m = JointModel(**hp); m.load_state_dict(c["state_dict"], strict=True)
if a.weights != "none":
    w = torch.load(a.weights, map_location="cpu", weights_only=True); m.load_state_dict(w, strict=True)
sd = {k: v.detach().cpu().clone() for k, v in m.state_dict().items()}
same = all(torch.equal(sd[k], c["state_dict"][k]) for k in c["state_dict"]) and set(sd) == set(c["state_dict"])
if a.weights == "none" and not same: sys.exit("C0' export: the state dict changed without training")
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
torch.save(dict(hyper_parameters=dict(c["hyper_parameters"]), state_dict=sd, source=dict(base=SRC, base_sha256=hashlib.sha256(open(SRC, "rb").read()).hexdigest(), weights=a.weights, tag=a.tag)), a.out)
print(json.dumps(dict(out=a.out, sha256=hashlib.sha256(open(a.out, "rb").read()).hexdigest(), tensors=len(sd), equal_to_released=bool(same), tag=a.tag)))
