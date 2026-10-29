"""141 A3: fine-tune the released GLACIER with the END-TO-END reconstruction term of A2 plus a same-formula RETRIEVAL term over FIXED hard negatives
(141_decision.md / Codex 141). finetune_glt.py v2 (A2) is unchanged; this file adds --loss ret.
  L = L_A2_positive + lam * L_ret, L_A2_positive = inten_loss_fn(pred_e2e(true), observed) x inten_weight (A2's term, per query mean);
  s_j = -cos_loss_sparse(pred_e2e(candidate j), observed spectrum of the query) for j in {true} + fixed negatives (the model's own predicted
  fragments, include_magma False; negatives through the model's decoy path, is_decoy True, as GLACIER's contrastive step);
  L_ret = mean over queries WITH negatives of -log softmax_true(s / tau); queries without negatives keep only L_A2; padding is masked.
  tau = 0.1, lam = 0.1 (one fixed candidate, Codex 141). Trainable: inten_encoder / inten_decoder / output_map only (as A2).
Negatives: --decoys JSON {base spectrum name (labels.tsv spec): [SMILES, ...]} fixed before training (C0' top-K, make_glt_decoys + scoring);
at most --k per spectrum; never re-selected during training. Featurised from their OWN structures by GLACIER's tree processor (no targets).
--precheck: one batch; L_A2 and L_ret are back-propagated separately and both gradients must be finite and non-zero on the trainable tensors; then
one combined update; frozen parameters / buffers bit-identical; time and peak memory recorded.
Usage (Spark, .venv-glt; PYTHONPATH = data/glt/shim_train:ms-pred src):
  python experiments/glt/finetune_glt_v3.py --data data/glt/tims_s1 --decoys data/glt/decoys/fixed_k7.json --out data/glt/runs/A3 --steps 1500 --lr 1e-4 --bs 16 --device cuda [--precheck]"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]): sys.path.insert(0, p)
TRAIN3 = ("inten_encoder", "inten_decoder", "output_map")


def make_dataset_cls():
    import ms_pred.common as common
    from ms_pred.glacier.dataset import IntenDataset, IntenContrDataset

    class FixedDecoyDataset(IntenDataset):
        """IntenDataset items + FIXED decoys featurised exactly as GLACIER's IntenContrDataset does (own structure, no targets)."""
        def __init__(self, *args, decoys=None, k=7, **kw):
            super().__init__(*args, **kw); self.decoys = decoys or {}; self.k = k

        @classmethod
        def get_collate_fn(cls): return IntenContrDataset.collate_fn

        def __getitem__(self, idx):
            name = self.spec_names[idx]; colli_eng = common.get_collision_energy(name); adduct = self.name_to_adducts[name]
            precursor = self.name_to_precursors[name]; instrument = self.name_to_instruments[name]; entry = self.read_fn(name)
            outdict = {"name": name, "adduct": adduct, "precursor": precursor, "instrument": instrument, "smiles": self.name_to_smiles[name], "decoy": 0}; outdict.update(entry)
            base = str(name).split("_collision")[0]; dl = []
            for smi in self.decoys.get(base, [])[:self.k]:
                dd = common.MassSpec(colli_eng, smi, common.onehot_pos2ion[adduct])
                tr = self.tree_processor.featurize_tree(dd, include_inten_targs=False, include_frag_targs=False)
                tr.update({"name": name + "_decoy", "adduct": adduct, "precursor": precursor, "instrument": instrument, "collision_energy": colli_eng, "smiles": dd})
                dl.append(tr)
            return [outdict, dl]
    return FixedDecoyDataset


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--decoys", required=True)
    ap.add_argument("--precheck", action="store_true"); ap.add_argument("--steps", type=int, default=1500); ap.add_argument("--lr", type=float, default=1e-4); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--warmup", type=int, default=100); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--device", default="cuda"); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--k", type=int, default=7); ap.add_argument("--tau", type=float, default=0.1); ap.add_argument("--lam", type=float, default=0.1); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    import LinSATNet, pygmtools, torch_scatter   # noqa: F401
    assert "glacier/shim" not in LinSATNet.__file__ and "shim_train" in torch_scatter.__file__, (LinSATNet.__file__, torch_scatter.__file__)
    env = dict(linsatnet=LinSATNet.__file__, pygmtools=getattr(pygmtools, "__version__", "?"), torch_scatter=torch_scatter.__file__, torch=torch.__version__)
    import pandas as pd
    import ms_pred.common as common
    from ms_pred.glacier.dataset import TreeProcessor
    from ms_pred.glacier.joint_model import JointModel
    from torch.utils.data import DataLoader
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    os.makedirs(a.out, exist_ok=True)
    if os.path.exists(os.path.join(a.out, "state_dict.pt")): sys.exit(f"refused: {a.out}/state_dict.pt exists")
    c = torch.load(os.path.join(ROOT, "data/external/glacier/ckpt/glacier.pt"), map_location="cpu", weights_only=True)
    hp = {k: v for k, v in dict(c["hyper_parameters"]).items() if not str(k).startswith("_")}
    m = JointModel(**hp); m.load_state_dict(c["state_dict"], strict=True)
    orig_rg = {n: p.requires_grad for n, p in m.named_parameters()}
    for n, p in m.named_parameters(): p.requires_grad_(orig_rg[n] and n.split(".")[0] in TRAIN3)
    trainable = {n for n, p in m.named_parameters() if p.requires_grad}
    decoys = json.load(open(a.decoys)); D = Path(a.data); df = pd.read_csv(D / "labels.tsv", sep="\t"); sp = pd.read_csv(D / "splits" / "split.tsv", sep="\t"); spl = dict(zip(sp.name, sp.split))
    tr_df = df[df.spec.map(spl) == "train"].reset_index(drop=True)
    if set(decoys) - set(tr_df.spec): sys.exit("decoys keyed by a non-train spectrum (val / unknown)")
    if a.limit: tr_df = tr_df.head(a.limit)
    h5p = D / "magma_outputs" / "magma_tree_with_inten.hdf5"; h5 = common.HDF5Dataset(h5p); name_to_json = {Path(i).stem: i for i in h5.get_all_names()}; h5.close()
    tp = TreeProcessor(pe_embed_k=hp["pe_embed_k"], root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], multi_hop_max_dist=hp["multi_hop_max_dist"])
    DS = make_dataset_cls()
    tr_ds = DS(tr_df, magma_h5=h5p, magma_map=name_to_json, num_workers=0, root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], tree_processor=tp, datatype="HDF5", decoys=decoys, k=a.k)
    g = torch.Generator(); g.manual_seed(a.seed); nw = 0 if a.precheck else a.workers
    kw = dict(collate_fn=tr_ds.get_collate_fn(), num_workers=nw, persistent_workers=nw > 0, multiprocessing_context=("spawn" if nw > 0 else None))
    tr_ld = DataLoader(tr_ds, batch_size=a.bs, shuffle=True, generator=g, drop_last=True, **kw); dev = torch.device(a.device)

    def to_dev(x):
        if torch.is_tensor(x): return x.to(dev, non_blocking=True)
        if isinstance(x, dict): return {k: to_dev(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)): return type(x)(to_dev(v) for v in x)
        return x.to(dev) if hasattr(x, "to") and not isinstance(x, (str, bytes)) else x

    m = m.to(dev); m.log = lambda *x, **k: None
    params = [p for n, p in m.named_parameters() if n in trainable]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0); sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(1, a.warmup)))

    def fwd(b, is_decoy=False):
        return m.forward(graphormer_input=b.get("graphormer_input"), num_atoms=b["num_atoms"], adducts=b["adducts"], collision_engs=b["collision_engs"], root_form_vecs=b["root_form_vecs"],
                         masses=b["masses"], adduct_mass_shifts=b["adduct_mass_shifts"], atom_form_vecs=b["atom_form_vecs"], adj_matrices=b["adj_matrices"], atom_hs=b["atom_hs"],
                         total_hs=b["total_hs"], instruments=b["instruments"] if m.embed_instrument else None, include_magma=False, frag_targs=None, num_frag_targs=None,
                         is_decoy=is_decoy)["inten_pred_end_to_end"]["output"]

    def terms(b):
        """-> (L_A2, L_ret or None, n queries with negatives)."""
        if "targ" not in b:   # no negatives in the whole batch (collate fallback)
            out = fwd(b); return m.inten_loss_fn(out, b["inten_targs"], parent_mass=b["precursor_mzs"])["loss"].mean() * m.inten_weight, None, 0
        tb, db, nd = b["targ"], b["decoy"], b["num_decoys_per_entry"]
        to = fwd(tb); L_a2 = m.inten_loss_fn(to, tb["inten_targs"], parent_mass=tb["precursor_mzs"])["loss"].mean() * m.inten_weight
        do = fwd(db, is_decoy=True); d_targs = tb["inten_targs"].repeat_interleave(nd, dim=0)
        lt = m.cos_loss_sparse(to, tb["inten_targs"], parent_mass=tb["precursor_mzs"])["loss"]; ld = m.cos_loss_sparse(do, d_targs, parent_mass=db["precursor_mzs"])["loss"]
        end = torch.cumsum(nd, 0); start = end - nd; kmax = int(nd.max())
        S = torch.full((len(nd), kmax + 1), float("-inf"), device=lt.device); S[:, 0] = -lt / a.tau
        for i in range(len(nd)):
            if nd[i] > 0: S[i, 1:1 + int(nd[i])] = -ld[int(start[i]):int(end[i])] / a.tau
        has = nd > 0
        L_ret = -torch.log_softmax(S[has], dim=1)[:, 0].mean() if bool(has.any()) else None
        return L_a2, L_ret, int(has.sum())

    def grad_norm(loss):
        gs = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
        fin = all(gg is None or torch.isfinite(gg).all() for gg in gs); nrm = float(torch.sqrt(sum((gg.float() ** 2).sum() for gg in gs if gg is not None)))
        return fin, nrm

    def update(b, check=False):
        b = to_dev(b); L_a2, L_ret, nq = terms(b); info = {}
        if check:
            f1, n1 = grad_norm(L_a2); info.update(a2_grad_finite=f1, a2_grad_norm=n1)
            if L_ret is not None: f2, n2 = grad_norm(L_ret); info.update(ret_grad_finite=f2, ret_grad_norm=n2)
        loss = L_a2 + (a.lam * L_ret if L_ret is not None else 0.0)
        if not torch.isfinite(loss): sys.exit("non-finite loss")
        opt.zero_grad(set_to_none=True); loss.backward()
        bad = [n for n, p in m.named_parameters() if n in trainable and p.grad is not None and not torch.isfinite(p.grad).all()]
        if bad: sys.exit(f"non-finite gradient before clipping: {bad[:5]}")
        torch.nn.utils.clip_grad_value_(params, 5.0); opt.step(); sched.step()
        if [n for n, p in m.named_parameters() if n in trainable and not torch.isfinite(p).all()]: sys.exit("non-finite parameter after the update")
        return float(L_a2.detach()), (float(L_ret.detach()) if L_ret is not None else None), nq, info

    def frozen_check():
        sd = m.state_dict()
        changed_frozen = [k for k, v in c["state_dict"].items() if k not in trainable and not torch.equal(v, sd[k].detach().cpu())]
        changed_tr = [k for k in trainable if not torch.equal(c["state_dict"][k], sd[k].detach().cpu())]
        return dict(frozen_or_buffer_changed=changed_frozen[:10], n_frozen_or_buffer_changed=len(changed_frozen), trainable=len(trainable), trainable_changed=len(changed_tr))

    m.train()
    if a.precheck:
        if torch.cuda.is_available(): torch.cuda.reset_peak_memory_stats()
        t0 = time.time(); b = next(iter(tr_ld)); la2, lret, nq, info = update(b, check=True); sec = time.time() - t0; chk = frozen_check()
        ok = (chk["n_frozen_or_buffer_changed"] == 0 and chk["trainable_changed"] > 0 and info.get("a2_grad_finite") and info.get("a2_grad_norm", 0) > 0
              and (lret is None or (info.get("ret_grad_finite") and info.get("ret_grad_norm", 0) > 0)) and lret is not None)
        out = dict(precheck=("PASS" if ok else "FAIL"), device=a.device, L_a2=la2, L_ret=lret, queries_with_negatives=nq, seconds_one_batch=round(sec, 2),
                   peak_mem_gb=round(torch.cuda.max_memory_allocated() / 1e9, 2) if torch.cuda.is_available() else None, env=env, **info, **chk)
        print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(a.out, "precheck.json"), "w"), indent=1); sys.exit(0 if ok else 1)
    log = dict(recipe=vars(a), env=env, trainable_tensors=len(trainable), n_train=len(tr_ds), decoys_sha256=hashlib.sha256(open(a.decoys, "rb").read()).hexdigest(),
               data_manifest_sha256=hashlib.sha256(open(D / "manifest.json", "rb").read()).hexdigest(), losses=[])
    step = 0; t0 = time.time(); run = []
    while step < a.steps:
        for b in tr_ld:
            la2, lret, nq, _ = update(b); run.append((la2, lret if lret is not None else np.nan, nq)); step += 1
            if step % 50 == 0:
                r = np.array(run[-50:], float); log["losses"].append((step, float(np.nanmean(r[:, 0])), float(np.nanmean(r[:, 1])), float(r[:, 2].mean())))
                print(f"step {step} L_a2 {np.nanmean(r[:, 0]):.4f} L_ret {np.nanmean(r[:, 1]):.4f} q_with_neg {r[:, 2].mean():.1f} {time.time() - t0:.0f}s", flush=True)
            if step >= a.steps: break
    log["final_check"] = frozen_check()
    if log["final_check"]["n_frozen_or_buffer_changed"]: sys.exit(f"frozen parameters / buffers changed: {log['final_check']['frozen_or_buffer_changed']}")
    torch.save({k: v.detach().cpu() for k, v in m.state_dict().items()}, os.path.join(a.out, "state_dict.pt"))
    log["seconds"] = round(time.time() - t0); log["state_dict_sha256"] = hashlib.sha256(open(os.path.join(a.out, "state_dict.pt"), "rb").read()).hexdigest()
    json.dump(log, open(os.path.join(a.out, "train_log.json"), "w"), indent=1); print("FINETUNE_DONE", json.dumps({k: log[k] for k in ("seconds", "state_dict_sha256")}), json.dumps(log["final_check"]))


if __name__ == "__main__":
    main()
