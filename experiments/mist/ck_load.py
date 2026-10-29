"""MIST checkpoint load check (A0): torch.load(weights_only=True) only - no automatic fallback to weights_only=False (if it fails, stop and
inspect the types). Builds ScaledMIST from the checkpoint config, loads the EMA weights strictly, prints the parameter count / step / sha256.
Usage (Spark, .venv-mist): python -X utf8 experiments/mist/ck_load.py <ckpt> [<ckpt> ...]"""
import hashlib, sys
import torch
from mist.models.scaled_mist import ScaledMIST
for p in sys.argv[1:]:
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    ck = torch.load(p, map_location="cpu", weights_only=True)
    m = ScaledMIST(**ck["config"]["model"]); missing = m.load_state_dict(ck["ema_model"], strict=True)
    n = sum(x.numel() for x in m.parameters())
    print(p, "sha256", h[:16], "| keys", sorted(ck.keys()), "| step", ck.get("step"), "| params", n, "| dataset", ck["config"].get("data", {}).get("dataset_name"),
          "| model cfg", {k: ck["config"]["model"][k] for k in list(ck["config"]["model"])[:12]}, flush=True)
