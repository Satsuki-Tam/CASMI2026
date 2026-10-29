"""105 stage 2: fine-tune the released GLACIER (JointModel, ms-pred 708148c2) on an ms-pred dataset (make_glt_data.py + spark_glt_prep.sh) with a
FIXED recipe (no early stopping, no checkpoint selection on validation; the val loss is recorded only):
  --trainable inten : only the intensity side (inten_encoder, inten_decoder, output_map, collision embedders) is updated; the graph encoder
                      (root_module), the fragment decoder and the mappers stay frozen (the fragment set the model proposes is unchanged);
  --trainable all   : every parameter.
Loss = the model's own training objective (_common_step 'train': end-to-end + MAGMa intensity terms, fragment term), AdamW(lr, wd 0), linear
warmup --warmup steps then constant, gradient clipping 5 (value, as the original trainer), --steps updates, batch --bs, seed --seed.
Writes <out>/state_dict.pt (weights_only loadable), <out>/train_log.json (losses, val losses, recipe, data manifest hash, trainable counts).
Usage (Spark, .venv-glt; PYTHONPATH = data/glt/shim_train:ms-pred src for the loader workers):
  python experiments/glt/finetune_glt.py --data data/glt/tims_s1 --out data/glt/runs/A1 --trainable inten --steps 1500 --lr 1e-4 --bs 16 --device cuda"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]): sys.path.insert(0, p)
ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--trainable", choices=["inten", "all"], default="inten")
ap.add_argument("--steps", type=int, default=1500); ap.add_argument("--lr", type=float, default=1e-4); ap.add_argument("--bs", type=int, default=16); ap.add_argument("--warmup", type=int, default=100)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--device", default="cuda"); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--val_every", type=int, default=250)
a = ap.parse_args()
import LinSATNet, pygmtools   # noqa: F401
assert "glacier/shim" not in LinSATNet.__file__
import pandas as pd
import ms_pred.common as common
from ms_pred.glacier.dataset import TreeProcessor, IntenDataset
from ms_pred.glacier.joint_model import JointModel
from torch.utils.data import DataLoader
torch.manual_seed(a.seed); np.random.seed(a.seed)
os.makedirs(a.out, exist_ok=True)
if os.path.exists(os.path.join(a.out, "state_dict.pt")): sys.exit(f"refused: {a.out}/state_dict.pt exists")
c = torch.load(os.path.join(ROOT, "data/external/glacier/ckpt/glacier.pt"), map_location="cpu", weights_only=True)
hp = {k: v for k, v in dict(c["hyper_parameters"]).items() if not str(k).startswith("_")}
m = JointModel(**hp); m.load_state_dict(c["state_dict"], strict=True)
TRAIN_MODS = ("inten_encoder", "inten_decoder", "output_map", "collision_embed_merged", "collision_embedder_denominators")
for n, p in m.named_parameters(): p.requires_grad_(a.trainable == "all" or n.split(".")[0] in TRAIN_MODS)
D = Path(a.data); df = pd.read_csv(D / "labels.tsv", sep="\t"); sp = pd.read_csv(D / "splits" / "split.tsv", sep="\t"); spl = dict(zip(sp.name, sp.split))
tr_df, va_df = df[df.spec.map(spl) == "train"].reset_index(drop=True), df[df.spec.map(spl) == "val"].reset_index(drop=True)
h5p = D / "magma_outputs" / "magma_tree_with_inten.hdf5"; h5 = common.HDF5Dataset(h5p); name_to_json = {Path(i).stem: i for i in h5.get_all_names()}; h5.close()
tp = TreeProcessor(pe_embed_k=hp["pe_embed_k"], root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], multi_hop_max_dist=hp["multi_hop_max_dist"])
mk = lambda d: IntenDataset(d, magma_h5=h5p, magma_map=name_to_json, num_workers=0, root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], tree_processor=tp, datatype="HDF5")
tr_ds, va_ds = mk(tr_df), mk(va_df)
g = torch.Generator(); g.manual_seed(a.seed)
kw = dict(collate_fn=tr_ds.get_collate_fn(), num_workers=a.workers, persistent_workers=a.workers > 0, multiprocessing_context=("spawn" if a.workers > 0 else None))
tr_ld = DataLoader(tr_ds, batch_size=a.bs, shuffle=True, generator=g, drop_last=True, **kw); va_ld = DataLoader(va_ds, batch_size=a.bs, shuffle=False, **kw)
dev = torch.device(a.device)


def to_dev(x):
    if torch.is_tensor(x): return x.to(dev, non_blocking=True)
    if isinstance(x, dict): return {k: to_dev(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return type(x)(to_dev(v) for v in x)
    return x.to(dev) if hasattr(x, "to") and not isinstance(x, (str, bytes)) else x


m = m.to(dev); m.log = lambda *x, **k: None
params = [p for p in m.parameters() if p.requires_grad]
opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(1, a.warmup)))


def val_loss():
    m.eval(); ls = []
    with torch.no_grad():
        for b in va_ld: ls.append(float(m._common_step(to_dev(b), "val")["loss"]))
    m.train(); return float(np.mean(ls)) if ls else float("nan")


log = dict(recipe=vars(a), trainable_tensors=sum(1 for _ in params), trainable_params=int(sum(p.numel() for p in params)), total_params=int(sum(p.numel() for p in m.parameters())),
           data_manifest_sha256=hashlib.sha256(open(D / "manifest.json", "rb").read()).hexdigest(), n_train=len(tr_ds), n_val=len(va_ds), losses=[], val=[(0, val_loss())])
print(json.dumps({k: log[k] for k in ("trainable_tensors", "trainable_params", "total_params", "n_train", "n_val")}), "val0", log["val"][0], flush=True)
m.train(); step = 0; t0 = time.time(); run = []
while step < a.steps:
    for b in tr_ld:
        loss = m._common_step(to_dev(b), "train")["loss"]
        if not torch.isfinite(loss): sys.exit(f"non-finite loss at step {step}")
        opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_value_(params, 5.0); opt.step(); sched.step(); step += 1
        run.append(float(loss.detach()))
        if step % 50 == 0: log["losses"].append((step, float(np.mean(run[-50:])))); print(f"step {step} loss {np.mean(run[-50:]):.4f} {time.time() - t0:.0f}s", flush=True)
        if step % a.val_every == 0 or step == a.steps: log["val"].append((step, val_loss())); print(f"step {step} val {log['val'][-1][1]:.4f}", flush=True)
        if step >= a.steps: break
torch.save({k: v.detach().cpu() for k, v in m.state_dict().items()}, os.path.join(a.out, "state_dict.pt"))
log["seconds"] = round(time.time() - t0); log["state_dict_sha256"] = hashlib.sha256(open(os.path.join(a.out, "state_dict.pt"), "rb").read()).hexdigest()
json.dump(log, open(os.path.join(a.out, "train_log.json"), "w"), indent=1); print("FINETUNE_DONE", json.dumps({k: log[k] for k in ("seconds", "state_dict_sha256")}))
