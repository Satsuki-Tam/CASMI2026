"""105 stage 0a (GLACIER training environment): the inference shim of LinSATNet (data/external/glacier/shim/LinSATNet, pure torch, values never
used at inference) vs the real package (pip linsatnet 0.1.3, MIT, installed in .venv-glt) on GLACIER's exact call pattern:
linsat_layer(logits [R, N_atom], E = ones(1, N_atom), f = [k], max_iter = 1, tau = linsat_tau) for k = 1, 2, 3 -- forward values and gradients.
Training must use the real package unless both agree to float tolerance. Prints a JSON verdict; exit 0 always (a report, not a gate).
Usage (Spark): .venv-glt/bin/python experiments/glt/stage0_linsat.py"""
import importlib.util, json, os, sys
import torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import LinSATNet as REAL
spec = importlib.util.spec_from_file_location("linsat_shim", os.path.join(ROOT, "data/external/glacier/shim/LinSATNet/__init__.py")); SHIM = importlib.util.module_from_spec(spec); spec.loader.exec_module(SHIM)
torch.manual_seed(0); out = dict(real=REAL.__file__, cases=[])
for dev in (["cuda"] if torch.cuda.is_available() else []) + ["cpu"]:
    for (R, N, tau) in ((7, 12, 15.0), (64, 40, 15.0), (16, 100, 0.01), (5, 3, 1.0)):
        for k in (1, 2, 3):
            x = (torch.randn(R, N, device=dev, dtype=torch.float32) * 3).requires_grad_(True); x2 = x.detach().clone().requires_grad_(True)
            E = torch.ones(1, N, device=dev); f = torch.tensor([float(k)], device=dev)
            a = REAL.linsat_layer(x, E=E, f=f, no_warning=True, max_iter=1, tau=tau); b = SHIM.linsat_layer(x2, E=E, f=f, no_warning=True, max_iter=1, tau=tau)
            w = torch.randn_like(a); (a * w).sum().backward(); (b * w).sum().backward()
            out["cases"].append(dict(dev=dev, R=R, N=N, tau=tau, k=k, max_abs_val=float((a - b).abs().max()), max_abs_grad=float((x.grad - x2.grad).abs().max()),
                                     val_scale=float(a.abs().max()), finite=bool(torch.isfinite(a).all() and torch.isfinite(x.grad).all())))
mv = max(c["max_abs_val"] for c in out["cases"]); mg = max(c["max_abs_grad"] for c in out["cases"])
out["summary"] = dict(max_abs_val=mv, max_abs_grad=mg, all_finite=all(c["finite"] for c in out["cases"]), agree_1e5=bool(mv < 1e-5 and mg < 1e-5))
print(json.dumps(out["summary"])); json.dump(out, open(os.path.join(ROOT, "experiments/glt/out_stage0_linsat.json"), "w"), indent=1)
