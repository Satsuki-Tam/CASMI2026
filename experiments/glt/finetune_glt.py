"""105 stage 2: fine-tune the released GLACIER (JointModel, ms-pred 708148c2) on an ms-pred dataset (make_glt_data.py + spark_glt_prep.sh) with a
FIXED recipe (no early stopping, no checkpoint selection on validation; the val loss is recorded only).
v2 (Codex 134, before any stage-2 result; v1 = the unread A1 run):
  --trainable inten3 (default): ONLY inten_encoder, inten_decoder, output_map are updated. Everything else keeps requires_grad False, including the
                      collision-energy encoding (collision_embedder_denominators / collision_embed_merged are non-trainable in the original
                      constructor and the CE representation also feeds the fragment side): the fragment proposals of the model are unchanged.
  --loss e2e (default): the END-TO-END intensity loss is optimised explicitly = inten_loss_fn(intensities predicted on the model's own predicted
                      fragments, as at inference; cosine, no Hungarian, as the model's training branch) x inten_weight. (The model's own training
                      step would, during its first magma_warmup_steps = 2,500 updates, optimise the MAGMa-fragment intensity + fragment loss
                      instead; --loss model keeps that behaviour and is not the registered variant.)
  Each update: gradients checked finite BEFORE value clipping (5, as the original trainer), parameters finite after the update; at the end every
  frozen parameter and every buffer is compared bit for bit with the released checkpoint. --precheck runs one batch (forward / backward / update)
  with these checks on the chosen device and exits (the pre-run technical check). The paths / versions of LinSATNet, pygmtools, the training
  torch_scatter shim and torch are recorded.
Writes <out>/state_dict.pt (weights_only loadable) and <out>/train_log.json (losses, val losses (the model's validation loss with Hungarian
matching, recorded only), recipe, data manifest hash, trainable counts, checks).
Usage (Spark, .venv-glt; PYTHONPATH = data/glt/shim_train:ms-pred src for the loader workers):
  python experiments/glt/finetune_glt.py --data data/glt/tims_s1 --out data/glt/runs/A2 --steps 1500 --lr 1e-4 --bs 16 --device cuda [--precheck]"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]): sys.path.insert(0, p)
TRAIN3 = ("inten_encoder", "inten_decoder", "output_map")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--trainable", choices=["inten3", "all"], default="inten3")
    ap.add_argument("--loss", choices=["e2e", "model"], default="e2e"); ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--steps", type=int, default=1500); ap.add_argument("--lr", type=float, default=1e-4); ap.add_argument("--bs", type=int, default=16); ap.add_argument("--warmup", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--device", default="cuda"); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--val_every", type=int, default=250)
    a = ap.parse_args()
    import LinSATNet, pygmtools, torch_scatter   # noqa: F401
    assert "glacier/shim" not in LinSATNet.__file__ and "shim_train" in torch_scatter.__file__, (LinSATNet.__file__, torch_scatter.__file__)
    env = dict(linsatnet=LinSATNet.__file__, pygmtools=getattr(pygmtools, "__version__", "?"), pygmtools_file=pygmtools.__file__, torch_scatter=torch_scatter.__file__, torch=torch.__version__)
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
    orig_rg = {n: p.requires_grad for n, p in m.named_parameters()}
    for n, p in m.named_parameters(): p.requires_grad_(orig_rg[n] and (a.trainable == "all" or n.split(".")[0] in TRAIN3))
    trainable = {n for n, p in m.named_parameters() if p.requires_grad}
    D = Path(a.data); df = pd.read_csv(D / "labels.tsv", sep="\t"); sp = pd.read_csv(D / "splits" / "split.tsv", sep="\t"); spl = dict(zip(sp.name, sp.split))
    tr_df, va_df = df[df.spec.map(spl) == "train"].reset_index(drop=True), df[df.spec.map(spl) == "val"].reset_index(drop=True)
    h5p = D / "magma_outputs" / "magma_tree_with_inten.hdf5"; h5 = common.HDF5Dataset(h5p); name_to_json = {Path(i).stem: i for i in h5.get_all_names()}; h5.close()
    tp = TreeProcessor(pe_embed_k=hp["pe_embed_k"], root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], multi_hop_max_dist=hp["multi_hop_max_dist"])
    mk = lambda d: IntenDataset(d, magma_h5=h5p, magma_map=name_to_json, num_workers=0, root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], tree_processor=tp, datatype="HDF5")
    tr_ds, va_ds = mk(tr_df), mk(va_df)
    g = torch.Generator(); g.manual_seed(a.seed)
    nw = 0 if a.precheck else a.workers
    kw = dict(collate_fn=tr_ds.get_collate_fn(), num_workers=nw, persistent_workers=nw > 0, multiprocessing_context=("spawn" if nw > 0 else None))
    tr_ld = DataLoader(tr_ds, batch_size=a.bs, shuffle=True, generator=g, drop_last=True, **kw); va_ld = DataLoader(va_ds, batch_size=a.bs, shuffle=False, **kw)
    dev = torch.device(a.device)

    def to_dev(x):
        if torch.is_tensor(x): return x.to(dev, non_blocking=True)
        if isinstance(x, dict): return {k: to_dev(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)): return type(x)(to_dev(v) for v in x)
        return x.to(dev) if hasattr(x, "to") and not isinstance(x, (str, bytes)) else x

    m = m.to(dev); m.log = lambda *x, **k: None
    params = [p for n, p in m.named_parameters() if n in trainable]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(1, a.warmup)))

    def e2e_loss(b):   # = the model's training branch for the end-to-end term (no Hungarian), on the model's own predicted fragments
        pred = m.forward(graphormer_input=b.get("graphormer_input"), num_atoms=b["num_atoms"], adducts=b["adducts"], collision_engs=b["collision_engs"],
                         root_form_vecs=b["root_form_vecs"], masses=b["masses"], adduct_mass_shifts=b["adduct_mass_shifts"], atom_form_vecs=b["atom_form_vecs"],
                         adj_matrices=b["adj_matrices"], atom_hs=b["atom_hs"], total_hs=b["total_hs"], instruments=b["instruments"] if m.embed_instrument else None,
                         include_magma=False, frag_targs=None, num_frag_targs=None)
        return m.inten_loss_fn(pred["inten_pred_end_to_end"]["output"], b["inten_targs"], parent_mass=b["precursor_mzs"])["loss"].mean() * m.inten_weight

    loss_of = (lambda b: e2e_loss(b)) if a.loss == "e2e" else (lambda b: m._common_step(b, "train")["loss"])

    def update(b):
        loss = loss_of(to_dev(b))
        if not torch.isfinite(loss): sys.exit("non-finite loss")
        opt.zero_grad(set_to_none=True); loss.backward()
        bad = [n for n, p in m.named_parameters() if n in trainable and p.grad is not None and not torch.isfinite(p.grad).all()]
        if bad: sys.exit(f"non-finite gradient before clipping: {bad[:5]}")
        torch.nn.utils.clip_grad_value_(params, 5.0); opt.step(); sched.step()
        badp = [n for n, p in m.named_parameters() if n in trainable and not torch.isfinite(p).all()]
        if badp: sys.exit(f"non-finite parameter after the update: {badp[:5]}")
        return float(loss.detach())

    def frozen_check():
        sd = m.state_dict(); bufs = {n for n, _ in m.named_buffers()}
        changed_frozen = [k for k, v in c["state_dict"].items() if k not in trainable and not torch.equal(v, sd[k].detach().cpu())]
        changed_tr = [k for k in trainable if not torch.equal(c["state_dict"][k], sd[k].detach().cpu())]
        return dict(frozen_or_buffer_changed=changed_frozen[:10], n_frozen_or_buffer_changed=len(changed_frozen), n_buffers=len(bufs), trainable=len(trainable), trainable_changed=len(changed_tr),
                    trainable_unchanged=[k for k in trainable if k not in set(changed_tr)][:10])

    def val_loss():
        m.eval(); ls = []
        with torch.no_grad():
            for b in va_ld: ls.append(float(m._common_step(to_dev(b), "val")["loss"]))
        m.train(); return float(np.mean(ls)) if ls else float("nan")

    m.train()
    if a.precheck:
        b = next(iter(tr_ld)); l0 = update(b); chk = frozen_check()
        ok = chk["n_frozen_or_buffer_changed"] == 0 and chk["trainable_changed"] > 0
        out = dict(precheck=("PASS" if ok else "FAIL"), device=a.device, loss=l0, env=env, trainable_modules=sorted({n.split(".")[0] for n in trainable}), **chk)
        print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(a.out, "precheck.json"), "w"), indent=1); sys.exit(0 if ok else 1)
    log = dict(recipe=vars(a), env=env, trainable_modules=sorted({n.split(".")[0] for n in trainable}), trainable_tensors=len(trainable), trainable_params=int(sum(p.numel() for p in params)),
               total_params=int(sum(p.numel() for p in m.parameters())), data_manifest_sha256=hashlib.sha256(open(D / "manifest.json", "rb").read()).hexdigest(), n_train=len(tr_ds), n_val=len(va_ds),
               sampling="spectrum-uniform shuffle (<= 4 spectra per identity)", losses=[], val=[(0, val_loss())])
    print(json.dumps({k: log[k] for k in ("trainable_modules", "trainable_tensors", "trainable_params", "n_train", "n_val")}), "val0", log["val"][0], flush=True)
    m.train(); step = 0; t0 = time.time(); run = []
    while step < a.steps:
        for b in tr_ld:
            run.append(update(b)); step += 1
            if step % 50 == 0: log["losses"].append((step, float(np.mean(run[-50:])))); print(f"step {step} loss {np.mean(run[-50:]):.4f} {time.time() - t0:.0f}s", flush=True)
            if step % a.val_every == 0 or step == a.steps: log["val"].append((step, val_loss())); print(f"step {step} val {log['val'][-1][1]:.4f}", flush=True)
            if step >= a.steps: break
    log["final_check"] = frozen_check()
    if log["final_check"]["n_frozen_or_buffer_changed"]: sys.exit(f"frozen parameters / buffers changed: {log['final_check']['frozen_or_buffer_changed']}")
    torch.save({k: v.detach().cpu() for k, v in m.state_dict().items()}, os.path.join(a.out, "state_dict.pt"))
    log["seconds"] = round(time.time() - t0); log["state_dict_sha256"] = hashlib.sha256(open(os.path.join(a.out, "state_dict.pt"), "rb").read()).hexdigest()
    json.dump(log, open(os.path.join(a.out, "train_log.json"), "w"), indent=1); print("FINETUNE_DONE", json.dumps({k: log[k] for k in ("seconds", "state_dict_sha256")}), json.dumps(log["final_check"]))


if __name__ == "__main__":   # spawn-safe: DataLoader workers re-import this module without running the training
    main()
