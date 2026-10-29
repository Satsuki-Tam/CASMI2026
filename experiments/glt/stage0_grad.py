"""105 stage 0b (GLACIER training environment): the released GLACIER checkpoint (data/external/glacier/ckpt/glacier.pt, weights_only) loaded into
ms-pred-train's JointModel (commit 708148c2) with the dgl / torch_scatter pure-torch shims and the REAL LinSATNet / pygmtools, trained on a tiny
MAGMa-labelled MassSpecGym batch (data/glt/stage0, make_msdata.py -> run_magma -> 01_assign_subformulae -> add_dag_intens) through the model's own
_common_step('train') (joint loss = intensity + MAGMa fragment terms; the contrastive branch needs decoys and is checked in stage 1).
Checks (verdict printed as JSON; exit 1 on FAIL): the checkpoint loads strictly; loss finite; every trainable parameter that receives a gradient has
a finite one and the share of parameters without a gradient is listed by module (expected: contrastive-only heads); one AdamW step changes the
weights; 30 steps on the same batch lower the loss (overfit sanity). CPU by default (--device cuda optional).
Usage (Spark): .venv-glt/bin/python -X utf8 experiments/glt/stage0_grad.py [--device cpu]"""
import argparse, json, os, sys
from collections import Counter
from pathlib import Path
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]):
    sys.path.insert(0, p)
ap = argparse.ArgumentParser(); ap.add_argument("--device", default="cpu"); ap.add_argument("--data", default=os.path.join(ROOT, "data/glt/stage0")); ap.add_argument("--bs", type=int, default=8)
ap.add_argument("--steps", type=int, default=30); a = ap.parse_args()
import LinSATNet, pygmtools   # noqa: F401
assert "glacier/shim" not in LinSATNet.__file__, LinSATNet.__file__
import pandas as pd
import ms_pred.common as common
from ms_pred.glacier.dataset import TreeProcessor, IntenDataset
from ms_pred.glacier.joint_model import JointModel
from torch.utils.data import DataLoader
torch.manual_seed(0); np.random.seed(0)
c = torch.load(os.path.join(ROOT, "data/external/glacier/ckpt/glacier.pt"), map_location="cpu", weights_only=True)
sd = c["state_dict"]; hp = {k: v for k, v in dict(c["hyper_parameters"]).items() if not str(k).startswith("_")}
notes = []
if sd["instrument_embedder"].shape[0] != len(set(common.instrument2onehot_pos.values())):   # = gl_runner._align_onehot_tables (2-slot checkpoint)
    assert sd["instrument_embedder"].shape[0] == 2
    for k in [k for k, v in common.instrument2onehot_pos.items() if v >= 2]: del common.instrument2onehot_pos[k]
    notes.append("instrument table trimmed to the checkpoint's 2 slots")
assert sd["adduct_embedder"].shape[0] == len(set(common.ion2onehot_pos.values()))
m = JointModel(**hp); m.load_state_dict(sd, strict=True); notes.append("checkpoint loaded strictly")
D = Path(a.data); df = pd.read_csv(D / "labels.tsv", sep="\t")
h5p = D / "magma_outputs" / "magma_tree_with_inten.hdf5"; h5 = common.HDF5Dataset(h5p); name_to_json = {Path(i).stem: i for i in h5.get_all_names()}
tp = TreeProcessor(pe_embed_k=hp["pe_embed_k"], root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], multi_hop_max_dist=hp["multi_hop_max_dist"])
ds = IntenDataset(df, magma_h5=h5p, magma_map=name_to_json, num_workers=0, root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], tree_processor=tp, datatype="HDF5")
loader = DataLoader(ds, batch_size=a.bs, shuffle=False, collate_fn=ds.get_collate_fn(), num_workers=0)
batch = next(iter(loader)); dev = torch.device(a.device)


def to_dev(x):
    if torch.is_tensor(x): return x.to(dev)
    if isinstance(x, dict): return {k: to_dev(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return type(x)(to_dev(v) for v in x)
    return x.to(dev) if hasattr(x, "to") and not isinstance(x, (str, bytes)) else x


batch = to_dev(batch); m = m.to(dev); m.log = lambda *x, **k: None; m.train()
loss = m._common_step(batch, "train")["loss"]; l0 = float(loss.detach())
loss.backward()
params = [(n, p) for n, p in m.named_parameters() if p.requires_grad]
nograd = [n for n, p in params if p.grad is None]; bad = [n for n, p in params if p.grad is not None and not torch.isfinite(p.grad).all()]
zero = [n for n, p in params if p.grad is not None and float(p.grad.abs().max()) == 0.0]
opt = torch.optim.AdamW([p for _, p in params], lr=1e-4); before = {n: p.detach().clone() for n, p in params}
opt.step(); opt.zero_grad(set_to_none=True)
changed = sum(int(not torch.equal(before[n], p.detach())) for n, p in params)
losses = [l0]
for i in range(a.steps):
    loss = m._common_step(batch, "train")["loss"]; loss.backward(); opt.step(); opt.zero_grad(set_to_none=True); losses.append(float(loss.detach()))
mod = lambda n: n.split(".")[0]
res = dict(device=a.device, batch=len(batch["names"]) if "names" in batch else None, n_params=len(params), params_total=sum(p.numel() for _, p in params), loss0=l0, finite_loss=bool(np.isfinite(l0)),
           no_grad_by_module=dict(Counter(mod(n) for n in nograd)), nonfinite_grads=bad[:10], zero_grads_by_module=dict(Counter(mod(n) for n in zero)), changed_after_step=changed,
           losses=[round(x, 5) for x in losses[:5]] + [round(x, 5) for x in losses[-3:]], loss_drop=losses[0] - min(losses[-5:]), notes=notes, linsat=LinSATNet.__file__)
ok = res["finite_loss"] and not bad and changed > 0 and res["loss_drop"] > 0 and len(nograd) < len(params)
res["verdict"] = "STAGE0B_PASS" if ok else "STAGE0B_FAIL"
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(ROOT, "experiments/glt/out_stage0_grad.json"), "w"), indent=1)
sys.exit(0 if ok else 1)
