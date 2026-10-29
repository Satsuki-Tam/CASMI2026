"""105 stage 0c (Codex 133 Q4): which shimmed DGL / torch_scatter operations (and LinSATNet / pygmtools calls) does a GLACIER training step
actually execute, with which inputs requiring gradients, for (a) the registered variant A (intensity side trainable) and (b) all parameters?
Every public function / method of the training shims (data/glt/shim_train: dgl, dgl.function messages / reductions, dgl.nn pooling,
torch_scatter) and LinSATNet.linsat_layer / pygmtools.sinkhorn / pygmtools.hungarian are wrapped with a counter that records the call count and
whether any tensor argument requires grad (= the call is on a gradient path). One forward + backward of _common_step('train') on the stage-0
MSG batch per variant. Also records the parameter scope: trainable tensors that got a non-zero gradient, trainable tensors without one,
frozen tensors (must have no gradient).
Usage (Spark): .venv-glt/bin/python -X utf8 experiments/glt/stage0_ops.py [--data data/glt/stage0]"""
import argparse, functools, inspect, json, os, sys
from collections import defaultdict
from pathlib import Path
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]): sys.path.insert(0, p)
ap = argparse.ArgumentParser(); ap.add_argument("--data", default=os.path.join(ROOT, "data/glt/stage0")); ap.add_argument("--bs", type=int, default=8); a = ap.parse_args()
import LinSATNet, pygmtools
import dgl, dgl.function as dfn, dgl.nn as dnn, torch_scatter
CALLS = defaultdict(lambda: [0, 0])   # name -> [calls, calls with a grad-requiring tensor argument]


def has_grad(x):
    if torch.is_tensor(x): return x.requires_grad
    if isinstance(x, (list, tuple)): return any(has_grad(v) for v in x)
    if isinstance(x, dict): return any(has_grad(v) for v in x.values())
    if hasattr(x, "ndata"): return any(has_grad(v) for v in list(x.ndata.values()) + list(x.edata.values()))
    return False


def wrap(owner, name, label):
    f = getattr(owner, name)
    if getattr(f, "__glt_wrapped__", False): return
    @functools.wraps(f)
    def g(*args, **kw):
        c = CALLS[label]; c[0] += 1; c[1] += int(has_grad(args) or has_grad(kw)); return f(*args, **kw)
    g.__glt_wrapped__ = True; setattr(owner, name, g)


for mod, pre in ((dgl, "dgl"), (dfn, "dgl.function"), (torch_scatter, "torch_scatter")):
    for n, f in list(vars(mod).items()):
        if callable(f) and not n.startswith("_") and inspect.isfunction(f) and getattr(f, "__module__", "").startswith(mod.__name__): wrap(mod, n, f"{pre}.{n}")
for n in ("apply_edges", "update_all", "subgraph", "local_scope"): wrap(dgl.DGLGraph, n, f"DGLGraph.{n}")
for cls in ("AvgPooling", "SumPooling", "GlobalAttentionPooling"): wrap(getattr(dnn, cls), "forward", f"dgl.nn.{cls}")
for n in ("__call__",): wrap(dfn._Msg, n, "dgl.function._Msg (message)")
wrap(LinSATNet, "linsat_layer", "LinSATNet.linsat_layer"); wrap(pygmtools, "sinkhorn", "pygmtools.sinkhorn"); wrap(pygmtools, "hungarian", "pygmtools.hungarian")
import ms_pred.common as common
from ms_pred.glacier import joint_model as JM
from ms_pred.glacier.dataset import TreeProcessor, IntenDataset
from torch.utils.data import DataLoader
for n in ("linsat_layer",):
    if hasattr(JM, n): setattr(JM, n, LinSATNet.linsat_layer)   # joint_model imported the name directly
JM.pygm = pygmtools
c = torch.load(os.path.join(ROOT, "data/external/glacier/ckpt/glacier.pt"), map_location="cpu", weights_only=True); hp = {k: v for k, v in dict(c["hyper_parameters"]).items() if not str(k).startswith("_")}
D = Path(a.data); df = pd = None
import pandas as pd
df = pd.read_csv(D / "labels.tsv", sep="\t"); h5p = D / "magma_outputs" / "magma_tree_with_inten.hdf5"; h5 = common.HDF5Dataset(h5p); n2j = {Path(i).stem: i for i in h5.get_all_names()}
tp = TreeProcessor(pe_embed_k=hp["pe_embed_k"], root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], multi_hop_max_dist=hp["multi_hop_max_dist"])
ds = IntenDataset(df, magma_h5=h5p, magma_map=n2j, num_workers=0, root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], tree_processor=tp, datatype="HDF5")
batch = next(iter(DataLoader(ds, batch_size=a.bs, shuffle=False, collate_fn=ds.get_collate_fn(), num_workers=0)))
TRAIN_A = ("inten_encoder", "inten_decoder", "output_map", "collision_embed_merged", "collision_embedder_denominators")
out = {}
for variant in ("A_inten", "all"):
    torch.manual_seed(0); CALLS.clear()
    m = JM.JointModel(**hp); m.load_state_dict(c["state_dict"], strict=True); m.log = lambda *x, **k: None; m.train()
    for n, p in m.named_parameters(): p.requires_grad_(variant == "all" or n.split(".")[0] in TRAIN_A)
    loss = m._common_step(batch, "train")["loss"]; loss.backward()
    tr = [(n, p) for n, p in m.named_parameters() if p.requires_grad]; fr = [(n, p) for n, p in m.named_parameters() if not p.requires_grad]
    out[variant] = dict(loss=float(loss.detach()), calls={k: dict(calls=v[0], grad_path=v[1]) for k, v in sorted(CALLS.items())},
                        trainable=len(tr), trainable_nonzero_grad=sum(int(p.grad is not None and float(p.grad.abs().max()) > 0) for _, p in tr),
                        trainable_without_grad=[n for n, p in tr if p.grad is None or float(p.grad.abs().max()) == 0][:20],
                        frozen=len(fr), frozen_with_grad=sum(int(p.grad is not None) for _, p in fr))
print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(ROOT, "experiments/glt/out_stage0_ops.json"), "w"), indent=1)
