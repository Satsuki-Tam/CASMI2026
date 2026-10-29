"""MIST check C (117 section 3; technical): the CASMI adapter (mist_adapter.featurize, MIST's merge -> assign path) applied to the MSG TEST
spectra's raw peaks (data/external/massspecgym/MassSpecGym.tsv) versus the official compact test rows (built from no_subform.hdf5, a different
assignment source): per-field exact agreement of the discrete arrays (lengths, peak_type, ion_vec, form_vec) and intensities (float16), then
the effect on the model: mean Tanimoto at the validation threshold of check A with adapter features vs compact features (same spectra, same
truth fingerprints). Also check B (part 2): CPU predictions are invariant to the row order (reversed batch).
Usage (Spark, .venv-mist, CUDA hidden): python -X utf8 experiments/mist/check_c.py <ckpt> <compact msg dir> <MassSpecGym.tsv> <check_a json> <out.json>"""
import json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mist_adapter as A
from mist.data.input_signal import SpectrumOnlyDataset, collate_spectrum_only
from mist.metrics import metric_summary, tanimoto_scores
from mist.models.scaled_mist import ScaledMIST
ck_path, root, tsv, cka, out = sys.argv[1], Path(sys.argv[2]) / "test", sys.argv[3], sys.argv[4], sys.argv[5]
torch.set_num_threads(8); t0 = time.time()
thr = json.load(open(cka))["val_threshold"]
ck = torch.load(ck_path, map_location="cpu", weights_only=True); model = ScaledMIST(**ck["config"]["model"]); model.load_state_dict(ck["ema_model"], strict=True); model.eval()
ds = SpectrumOnlyDataset(root); names = ds.names(); N = len(ds)
fps = np.concatenate([np.load(p / "fingerprints.npy", mmap_mode="r") for p in ds.part_paths]).astype(bool); assert len(fps) == N
msg = pd.read_csv(tsv, sep="\t", usecols=["identifier", "mzs", "intensities", "precursor_mz", "adduct", "formula", "instrument_type"]).set_index("identifier")
ids = [n.split("_collision")[0] for n in names]; assert len(set(ids)) == N, "identifier not unique"
rows_c = [ds[i] for i in range(N)]; rows_a, fail = [], 0
for i, sid in enumerate(ids):
    r = msg.loc[sid]
    try:
        rows_a.append(A.featurize([float(x) for x in r.mzs.split(",")], [float(x) for x in r.intensities.split(",")], r.precursor_mz, r.formula, r.adduct, r.instrument_type))
    except Exception as e:
        fail += 1; rows_a.append(None)
ok = [i for i in range(N) if rows_a[i] is not None]
agree = {}
for k in ("lengths", "peak_type", "ion_vec", "form_vec", "intens"):
    agree[k] = float(np.mean([np.array_equal(np.asarray(rows_a[i][k]), np.asarray(rows_c[i][k])) for i in ok]))
def predict(rows, bs=256, reverse=False):
    idx = list(range(len(rows)))[::-1] if reverse else list(range(len(rows)))
    out_ = np.zeros((len(rows), 4096), np.float32)
    with torch.inference_mode():
        for s in range(0, len(idx), bs):
            b = idx[s:s + bs]; p, _ = model(A.collate([rows[j] for j in b])); out_[b] = p.float().numpy()
    return out_
pc = predict([rows_c[i] for i in ok]); pa = predict([rows_a[i] for i in ok]); pr = predict([rows_a[i] for i in ok], reverse=True)
tc = tanimoto_scores(pc, fps[ok], thr); ta = tanimoto_scores(pa, fps[ok], thr)
res = dict(n=N, adapter_failures=fail, field_exact_agreement=agree, threshold=thr, tanimoto_compact=metric_summary(tc), tanimoto_adapter=metric_summary(ta),
           mean_diff_adapter_minus_compact=float(ta.mean() - tc.mean()), check_b_reverse_order_maxabs=float(np.abs(pr - pa).max()), seconds=round(time.time() - t0))
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
