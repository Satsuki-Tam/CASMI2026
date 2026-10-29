"""105 stage 0a addendum: do the shim and the real LinSATNet select the same top-k atom indices (the only use at GLACIER inference)?
Random logits with the scales GLACIER produces (std 1-5), tau 15 and 0.05, k = 1, 2, 3; also the max |value| difference by tau.
Usage (Spark): .venv-glt/bin/python experiments/glt/stage0_linsat_topk.py"""
import importlib.util, json, os
import torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import LinSATNet as REAL
spec = importlib.util.spec_from_file_location("linsat_shim", os.path.join(ROOT, "data/external/glacier/shim/LinSATNet/__init__.py")); SHIM = importlib.util.module_from_spec(spec); spec.loader.exec_module(SHIM)
torch.manual_seed(1); res = []
for tau in (15.0, 1.0, 0.05):
    for sd in (1.0, 5.0):
        for N in (10, 40, 100):
            x = torch.randn(2000, N) * sd; E = torch.ones(1, N)
            for k in (1, 2, 3):
                with torch.no_grad():
                    a = REAL.linsat_layer(x, E=E, f=torch.tensor([float(k)]), no_warning=True, max_iter=1, tau=tau); b = SHIM.linsat_layer(x, E=E, f=torch.tensor([float(k)]), no_warning=True, max_iter=1, tau=tau)
                ta = torch.topk(a, k, dim=-1).indices.sort(-1).values; tb = torch.topk(b, k, dim=-1).indices.sort(-1).values; tx = torch.topk(x, k, dim=-1).indices.sort(-1).values
                res.append(dict(tau=tau, sd=sd, N=N, k=k, topk_same_real_shim=float((ta == tb).all(-1).float().mean()), topk_real_eq_logit=float((ta == tx).all(-1).float().mean()),
                                max_abs_val=float((a - b).abs().max()), real_sum=float(a.sum(-1).mean())))
for r in res: print(json.dumps(r))
json.dump(res, open(os.path.join(ROOT, "experiments/glt/out_stage0_linsat_topk.json"), "w"), indent=1)
