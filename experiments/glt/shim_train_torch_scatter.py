"""105 stage 0d: torch_scatter for GLACIER TRAINING (installed as data/glt/shim_train/torch_scatter/__init__.py; the inference shim is unchanged).
The only torch_scatter call on GLACIER's gradient path is scatter_max (stage0_ops.py: spectrum binning, max over predicted peaks in one m/z bin).
Forward values and argmax are those of the inference shim (data/external/glacier/shim/torch_scatter: scatter_reduce 'amax', include_self False,
0 for empty segments, arg = the lowest index attaining the maximum, dim_size for empty segments); the BACKWARD follows torch_scatter's
documented semantics -- the whole upstream gradient of a segment goes to its argmax element (the inference shim's scatter_reduce splits it
evenly among tied maxima). Implemented by gathering src at the argmax, so autograd routes the gradient to that element only.
scatter_add / scatter_sum / scatter_mean are re-exported from the inference shim (linear; not on GLACIER's gradient path)."""
import importlib.util, os
import torch
_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "external", "glacier", "shim", "torch_scatter", "__init__.py")   # installed at data/glt/shim_train/torch_scatter/
if not os.path.exists(_P):   # installed copy: resolve the repo from the env
    _P = os.path.join(os.environ.get("CASMI_ROOT", os.path.expanduser("~/CASMI2026")), "data", "external", "glacier", "shim", "torch_scatter", "__init__.py")
_spec = importlib.util.spec_from_file_location("_ts_infer", _P); _I = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_I)
scatter_add, scatter_sum, scatter_mean = _I.scatter_add, _I.scatter_sum, _I.scatter_mean


def _ext(src, index, dim, dim_size, op):
    with torch.no_grad():
        _, arg = _I._scatter_ext(src.detach(), index, dim, dim_size, op)   # values / argmax exactly as the inference shim
    big = src.shape[dim % src.dim()]; valid = arg < big
    out = torch.gather(src, dim % src.dim(), torch.where(valid, arg, torch.zeros_like(arg)))
    return torch.where(valid, out, torch.zeros_like(out)), arg


def scatter_max(src, index, dim=-1, out=None, dim_size=None):
    if out is not None: raise NotImplementedError("training shim: out= not supported")
    return _ext(src, index, dim, dim_size, "amax")


def scatter_min(src, index, dim=-1, out=None, dim_size=None):
    if out is not None: raise NotImplementedError("training shim: out= not supported")
    return _ext(src, index, dim, dim_size, "amin")


def scatter(src, index, dim=-1, out=None, dim_size=None, reduce="sum"):   # = the inference shim's dispatcher, max / min routed to the training versions
    if reduce in ("sum", "add"): return scatter_add(src, index, dim, out, dim_size)
    if reduce == "mean": return scatter_mean(src, index, dim, out, dim_size)
    if reduce == "max": return scatter_max(src, index, dim, out, dim_size)[0]
    if reduce == "min": return scatter_min(src, index, dim, out, dim_size)[0]
    raise NotImplementedError(reduce)


scatter_softmax = _I.scatter_softmax   # max-subtracted softmax (the max is a constant shift; gradients are those of softmax)
