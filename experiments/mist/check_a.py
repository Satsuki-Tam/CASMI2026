"""MIST check A (117 section 3; technical, no CASMI data): reproduce the published MSG numbers of a checkpoint with the official evaluation
path (mist.evaluate_scaled: CompactFeatureDataset + make_compact_loader + calibrate_threshold on val + tanimoto_scores on test, EMA weights),
changing only the loading to torch.load(weights_only=True) and the device to CPU. Published (MSG in the Wild / FRIGID 'MIST 4M-aug'): aug
threshold 0.1879101470 and MSG test mean Tanimoto 0.433; noaug has no published number (its values are recorded, not compared).
Also check B (part 1): the same val predictions with batch size 256 and 61 (different batch composition) must agree to 1e-5.
Usage (Spark, .venv-mist, CUDA hidden): python -X utf8 experiments/mist/check_a.py <ckpt> <compact msg dir> <out.json>"""
import json, sys, time
from pathlib import Path
import numpy as np, torch
from mist.data.compact import CompactFeatureDataset, make_compact_loader
from mist.metrics import calibrate_threshold, metric_summary, tanimoto_scores
from mist.models.scaled_mist import ScaledMIST
ck_path, root, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
torch.set_num_threads(8)
ck = torch.load(ck_path, map_location="cpu", weights_only=True)
model = ScaledMIST(**ck["config"]["model"]); model.load_state_dict(ck["ema_model"], strict=True); model.eval()
def predict(split, bs):
    ds = CompactFeatureDataset(root / split)
    loader, sampler = make_compact_loader(ds, batch_size=bs, rank=0, world_size=1, seed=0, num_workers=0, prefetch_factor=2, drop_last=False, even_divisible=False)
    sampler.set_epoch(0); P, T, I = [], [], []
    with torch.inference_mode():
        for b in loader:
            p, _ = model(b); P.append(p.float()); T.append(b["targets"].to(torch.uint8)); I.append(b["row_indices"])
    P, T, I = torch.cat(P), torch.cat(T), torch.cat(I); o = torch.argsort(I)
    assert np.array_equal(I[o].numpy(), np.arange(len(ds))), "rows missing / duplicated"
    return P[o].numpy(), T[o].numpy()
t0 = time.time(); res = dict(checkpoint=ck_path, step=int(ck["step"]))
pv, tv = predict("val", 256); thr, cal = calibrate_threshold(pv, tv); res.update(val_threshold=float(thr), val_spectrum=metric_summary(tanimoto_scores(pv, tv, thr)))
pv2, _ = predict("val", 61); res["check_b_val_batch61_maxabs"] = float(np.abs(pv2 - pv).max())
pt, tt = predict("test", 256); st = tanimoto_scores(pt, tt, thr); res.update(test_spectrum=metric_summary(st), seconds=round(time.time() - t0))
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
