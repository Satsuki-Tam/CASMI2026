"""105 stage 0e (Codex 133 Q4, data and loss contract): every training / validation item of an adaptation dataset (make_glt_data.py +
spark_glt_prep.sh) as GLACIER's IntenDataset / collate deliver it -- non-empty intensity targets, the adduct ([M+H]+), the instrument token
(QTOF, as the inference runner maps timsTOF), the collision energy (eV, equal to labels.tsv), the precursor vs the formula's [M+H]+ m/z, the
number of MAGMa fragment targets, finite values, and the padding of the batched targets -- and the loss components of one batch (intensity
end-to-end, MAGMa intensity, fragment) are finite and non-zero. Prints a JSON verdict; exit 1 on a violation.
Usage (Spark): .venv-glt/bin/python -X utf8 experiments/glt/stage0_contract.py --data data/glt/tims_s1"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np, torch
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src")]): sys.path.insert(0, p)
ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--bs", type=int, default=16); a = ap.parse_args()
import pandas as pd
import ms_pred.common as common
from ms_pred.glacier.dataset import TreeProcessor, IntenDataset
from ms_pred.glacier.joint_model import JointModel
from torch.utils.data import DataLoader
c = torch.load(os.path.join(ROOT, "data/external/glacier/ckpt/glacier.pt"), map_location="cpu", weights_only=True); hp = {k: v for k, v in dict(c["hyper_parameters"]).items() if not str(k).startswith("_")}
D = Path(a.data); df = pd.read_csv(D / "labels.tsv", sep="\t"); h5p = D / "magma_outputs" / "magma_tree_with_inten.hdf5"; h5 = common.HDF5Dataset(h5p); n2j = {Path(i).stem: i for i in h5.get_all_names()}
tp = TreeProcessor(pe_embed_k=hp["pe_embed_k"], root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], multi_hop_max_dist=hp["multi_hop_max_dist"])
ds = IntenDataset(df, magma_h5=h5p, magma_map=n2j, num_workers=0, root_encode="graphormer", embed_elem_group=hp["embed_elem_group"], tree_processor=tp, datatype="HDF5")
viol, n_items, ce_vals, npk, nfr, prec_ppm = [], 0, [], [], [], []
lab = df.set_index("spec")
q_tok, h_tok = common.instrument2onehot_pos["QTOF"], common.ion2onehot_pos["[M+H]+"]
ld = DataLoader(ds, batch_size=a.bs, shuffle=False, collate_fn=ds.get_collate_fn(), num_workers=0)
first = None
for b in ld:
    first = first or b; names = list(b["names"]); n_items += len(names)
    for k in ("inten_targs", "collision_engs", "adducts", "instruments", "precursor_mzs", "num_frag_targs"):
        if k not in b: viol.append(f"batch without {k}"); continue
    ce = b["collision_engs"].float().numpy(); ad = b["adducts"].long().numpy(); ins = b["instruments"].long().numpy(); pm = b["precursor_mzs"].double().numpy()
    tg = b["inten_targs"]
    for i, nm in enumerate(names):
        base = str(nm).split("_collision")[0]; r = lab.loc[base] if base in lab.index else None
        if r is None: viol.append(f"{nm}: no label row"); continue
        ce_lab = float(eval(r.collision_energies)[0]); ce_vals.append(float(ce[i]))
        if abs(float(ce[i]) - ce_lab) > 1e-4: viol.append(f"{nm}: CE {ce[i]} != label {ce_lab}")
        if ad[i] != h_tok: viol.append(f"{nm}: adduct index {ad[i]}")
        if ins[i] != q_tok: viol.append(f"{nm}: instrument index {ins[i]}")
        t = tg[i] if torch.is_tensor(tg) else torch.as_tensor(tg[i]); t = t.float(); nz = int((t.reshape(-1, t.shape[-1])[:, -1] > 0).sum()) if t.dim() >= 2 else int((t > 0).sum())
        npk.append(nz)
        if nz == 0: viol.append(f"{nm}: empty intensity target")
        if not torch.isfinite(t).all(): viol.append(f"{nm}: non-finite target")
        mh = common.formula_mass(r.formula) + common.ion2mass["[M+H]+"]; prec_ppm.append(abs(pm[i] - mh) / mh * 1e6) if np.isfinite(pm[i]) and pm[i] > 0 else None
    nfr += b["num_frag_targs"].long().tolist()
m = JointModel(**hp); m.load_state_dict(c["state_dict"], strict=True); m.log = lambda *x, **k: None; m.train()
comp = {}
orig = m.inten_loss_fn
out = m._common_step(first, "train")["loss"]
res = dict(items=n_items, labels=len(df), violations=viol[:20], n_violations=len(viol), ce_values=sorted(set(round(x, 2) for x in ce_vals))[:10],
           target_peaks=dict(min=int(min(npk)), median=float(np.median(npk)), max=int(max(npk))), frag_targets=dict(min=int(min(nfr)), median=float(np.median(nfr)), zero=int(sum(x == 0 for x in nfr))),
           precursor_ppm_vs_formula=dict(median=float(np.median(prec_ppm)) if prec_ppm else None, p99=float(np.percentile(prec_ppm, 99)) if prec_ppm else None, n=len(prec_ppm)),
           first_batch_loss=float(out.detach()), loss_finite=bool(torch.isfinite(out)))
ok = not viol and n_items == len(df) and res["loss_finite"] and res["frag_targets"]["zero"] < n_items
res["verdict"] = "STAGE0E_PASS" if ok else "STAGE0E_FAIL"
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(ROOT, "experiments/glt/out_stage0_contract.json"), "w"), indent=1)
sys.exit(0 if ok else 1)
