"""MIST check C2 (Codex 128 Q2): separate the packing of the adapter from the assignment source, on the MSG TEST split.
  (1) same assigned table: MSG's own no_subform.hdf5 entry of each test spectrum -> mist_adapter.tree_to_row (the adapter's top-10 / CLS / padding /
      float16 packing, with MIST's PeakFormula rules: a table with invalid formula / ion fields is re-assigned) vs the official compact row:
      every field must agree exactly (expected 100%: same table, same packing);
  (2) raw-peak path (merge -> assign, what CASMI needs) vs compact, per spectrum id, classified: identical / tie-order only (same fragment multiset,
      different order) / different fragment formulas / different count or ions / adapter failure (id + exception recorded);
  (3) prediction differences raw path vs compact: per-spectrum |Tanimoto difference| quantiles and max, max |probability difference|.
Usage (Spark, .venv-mist, CUDA hidden): python -X utf8 experiments/mist/check_c2.py <ckpt> <compact msg dir> <msg_all dir> <MassSpecGym.tsv> <check_a json> <out.json>"""
import json, os, sys, time
from collections import Counter
from pathlib import Path
import numpy as np, pandas as pd, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mist_adapter as A
from mist.data import featurizers as FZ
from mist.data.atlas import unpack_fingerprints
from mist.data.input_signal import SpectrumOnlyDataset
from mist.metrics import tanimoto_scores
from mist.models.scaled_mist import ScaledMIST
from mist.utils import chem_utils as C
ck_path, root, msg_all, tsv, cka, out = sys.argv[1], Path(sys.argv[2]) / "test", Path(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
torch.set_num_threads(8); t0 = time.time(); thr = json.load(open(cka))["val_threshold"]
ds = SpectrumOnlyDataset(root); names = ds.names(); N = len(ds)
fps = unpack_fingerprints(np.concatenate([np.load(p / "fingerprints.npy", mmap_mode="r") for p in ds.part_paths])).astype(bool)
rows_c = [ds[i] for i in range(N)]
store = FZ.HDF5TextStore(msg_all / "subformulae" / "no_subform.hdf5")
msg = pd.read_csv(tsv, sep="\t", usecols=["identifier", "mzs", "intensities", "precursor_mz", "adduct", "formula", "instrument_type"]).set_index("identifier")
FIELDS = ("lengths", "peak_type", "ion_vec", "form_vec", "intens")
def same(a, b): return all(np.array_equal(np.asarray(a[k]), np.asarray(b[k])) for k in FIELDS)
# (1) same table
agree1, fail1 = Counter(), []
for i, nm in enumerate(names):
    try:
        tree = json.loads(store.read(f"{nm}.json")); tab = tree.get("output_tbl")
        if tab is not None:
            cnt = len(tab.get("mz", [])); fo = tab.get("formula", []); io = tab.get("ions", [])
            if len(fo) != cnt or len(io) != cnt or any(not isinstance(v, str) or not v for v in fo) or any(v not in C.ION_LST for v in io): tree = FZ.assign_subformulae(tree, 20.0)
        r = A.tree_to_row(tree, msg.loc[nm.split("_collision")[0]].instrument_type)
        for k in FIELDS: agree1[k] += int(np.array_equal(np.asarray(r[k]), np.asarray(rows_c[i][k])))
        agree1["all"] += int(same(r, rows_c[i]))
    except Exception as e:
        fail1.append((nm, repr(e)[:160]))
# (2) raw path, classified
cls, fail2, rows_a, okidx = Counter(), [], [], []
for i, nm in enumerate(names):
    r0 = msg.loc[nm.split("_collision")[0]]
    try:
        ra = A.featurize([float(x) for x in r0.mzs.split(",")], [float(x) for x in r0.intensities.split(",")], r0.precursor_mz, r0.formula, r0.adduct, r0.instrument_type)
    except Exception as e:
        fail2.append((nm, repr(e)[:160])); cls["failure"] += 1; continue
    rc = rows_c[i]; rows_a.append(ra); okidx.append(i)
    if same(ra, rc): cls["identical"] += 1; continue
    na, nc = int(ra["lengths"]), int(rc["lengths"])
    fa = sorted(tuple(ra["form_vec"][k].tolist()) + (int(ra["ion_vec"][k]),) for k in range(na)); fc = sorted(tuple(rc["form_vec"][k].tolist()) + (int(rc["ion_vec"][k]),) for k in range(nc))
    if na != nc or not np.array_equal(ra["ion_vec"][:na], rc["ion_vec"][:nc]): cls["count_or_ion"] += 1
    elif fa == fc: cls["tie_order_only"] += 1
    else: cls["fragment_formulas"] += 1
# (3) prediction differences
ck = torch.load(ck_path, map_location="cpu", weights_only=True); model = ScaledMIST(**ck["config"]["model"]); model.load_state_dict(ck["ema_model"], strict=True); model.eval()
def predict(rows):
    o = np.zeros((len(rows), 4096), np.float32)
    with torch.inference_mode():
        for s in range(0, len(rows), 256): o[s:s + 256] = model(A.collate(rows[s:s + 256]))[0].float().numpy()
    return o
pa = predict(rows_a); pc = predict([rows_c[i] for i in okidx])
dt = np.abs(tanimoto_scores(pa, fps[okidx], thr) - tanimoto_scores(pc, fps[okidx], thr))
res = dict(n=N, same_table=dict(agree={k: v / max(N - len(fail1), 1) for k, v in agree1.items()}, failures=len(fail1), failure_examples=fail1[:5]),
           raw_path=dict(classes=dict(cls), failures=fail2[:10]),
           prediction=dict(abs_tanimoto_diff_quantiles={q: float(np.quantile(dt, q)) for q in (0.5, 0.9, 0.99, 0.999)}, abs_tanimoto_diff_max=float(dt.max()),
                           share_changed=float((dt > 1e-9).mean()), max_abs_probability_diff=float(np.abs(pa - pc).max())), seconds=round(time.time() - t0))
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
