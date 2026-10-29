"""105 stage 0d (Codex 133 Q4): scatter_max -- the only shimmed op on GLACIER's gradient path (stage0_ops.py) -- against a float64 reference of
torch_scatter's semantics (out[s] = max of the segment, 0 when empty; arg = lowest index attaining the max, dim_size when empty; backward: the
segment's whole upstream gradient to src[arg]). Compared: the inference shim (data/external/glacier/shim/torch_scatter) and the training shim
(data/glt/shim_train/torch_scatter = experiments/glt/shim_train_torch_scatter.py). Cases: random 1-D / 2-D sources, duplicate indices, ties
(exact equal values in a segment), empty segments (dim_size beyond the largest index), float32 / float64, CPU (and CUDA if present).
Pass (training shim): forward values and arg identical to the reference, VJP identical (float64 exact, float32 within 1e-6 relative).
The inference shim is reported (expected: equal without ties, gradient split among tied maxima).
Usage (Spark): .venv-glt/bin/python -X utf8 experiments/glt/stage0_scatter.py"""
import importlib.util, json, os, sys
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
INF = load(os.path.join(ROOT, "data/external/glacier/shim/torch_scatter/__init__.py"), "ts_inf"); TRN = load(os.path.join(ROOT, "data/glt/shim_train/torch_scatter/__init__.py"), "ts_trn")


def ref(src, index, dim_size):   # 1-D reference, float64
    src = src.detach().double().cpu().numpy(); idx = index.cpu().numpy(); out = np.zeros(dim_size); arg = np.full(dim_size, len(src))
    for s in range(dim_size):
        w = np.flatnonzero(idx == s)
        if len(w): j = w[np.argmax(src[w])]; out[s] = src[j]; arg[s] = j   # np.argmax = first occurrence among ties = lowest index (w ascending)
    return out, arg


def vjp_ref(arg, up, n):
    g = np.zeros(n)
    for s, j in enumerate(arg):
        if j < n: g[j] += up[s]
    return g


rng = np.random.default_rng(0); res = dict(cases=[])
devs = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])
for dev in devs:
    for dt in (torch.float64, torch.float32):
        for case in range(400):
            n = int(rng.integers(1, 60)); dim_size = int(rng.integers(1, 30)); idx = torch.as_tensor(rng.integers(0, dim_size, n), device=dev)
            vals = rng.normal(size=n)
            tie = case % 3 == 0
            if tie:   # force exact ties inside segments
                for s in set(idx.tolist()):
                    w = np.flatnonzero(idx.cpu().numpy() == s)
                    if len(w) >= 2: vals[w[: max(2, len(w) // 2)]] = vals[w].max() + 1.0
            extra = int(rng.integers(0, 5)); D = dim_size + extra   # empty trailing segments
            x_t = torch.tensor(vals, dtype=dt, device=dev, requires_grad=True); x_i = torch.tensor(vals, dtype=dt, device=dev, requires_grad=True)
            ot, at = TRN.scatter_max(x_t, idx, dim=0, dim_size=D); oi, ai = INF.scatter_max(x_i, idx, dim=0, dim_size=D)
            ro, ra = ref(x_t, idx, D); up = rng.normal(size=D)
            ot.backward(torch.tensor(up, dtype=dt, device=dev)); oi.backward(torch.tensor(up, dtype=dt, device=dev)); rg = vjp_ref(ra, up, n)
            tol = 0.0 if dt == torch.float64 else 1e-6
            c = dict(dev=dev, dtype=str(dt).split(".")[-1], n=n, D=D, tie=tie,
                     trn_fwd=float(np.abs(ot.detach().double().cpu().numpy() - ro).max()), trn_arg=bool((at.cpu().numpy() == ra).all()),
                     trn_grad=float(np.abs(x_t.grad.double().cpu().numpy() - rg).max() / max(1.0, np.abs(rg).max())),
                     inf_fwd=float(np.abs(oi.detach().double().cpu().numpy() - ro).max()), inf_arg=bool((ai.cpu().numpy() == ra).all()),
                     inf_grad=float(np.abs(x_i.grad.double().cpu().numpy() - rg).max() / max(1.0, np.abs(rg).max())))
            c["trn_pass"] = bool(c["trn_fwd"] <= tol and c["trn_arg"] and c["trn_grad"] <= max(tol, 1e-12)); res["cases"].append(c)
C = res["cases"]
res["summary"] = dict(n=len(C), training_shim_pass=all(c["trn_pass"] for c in C), training_max_fwd=max(c["trn_fwd"] for c in C), training_max_grad=max(c["trn_grad"] for c in C),
                      inference_fwd_max=max(c["inf_fwd"] for c in C), inference_arg_all=all(c["inf_arg"] for c in C),
                      inference_grad_max_no_tie=max(c["inf_grad"] for c in C if not c["tie"]), inference_grad_max_tie=max(c["inf_grad"] for c in C if c["tie"]))
print(json.dumps(res["summary"], indent=1)); json.dump(res, open(os.path.join(ROOT, "experiments/glt/out_stage0_scatter.json"), "w"), indent=1)
sys.exit(0 if res["summary"]["training_shim_pass"] else 1)
