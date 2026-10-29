"""MIST check C2 v2 (Codex 128 Q2 / 129 Q3) on the MSG TEST split; writes a machine-readable PASS / FAIL and exits 0 only on PASS.
Bound to: checkpoint sha256, check-A json (its checkpoint must be the same; its val threshold is used), mist_adapter.py sha256, the compact test
manifest sha256, no_subform.hdf5 sha256, MassSpecGym.tsv sha256.
  (0) consistency: N rows, unique names, every name maps to one MassSpecGym.tsv identifier, fingerprints (N, 4096), CLS at length - 1 with
      peak_type 3, zero padding after the length in the compact rows.
  (1) SAME assigned table: MSG's no_subform.hdf5 entry -> mist_adapter.tree_to_row (MIST's PeakFormula rule: an invalid table is re-assigned) vs
      the official compact row, model-relevant fields lengths / peak_type / ion_vec / form_vec / intens. The released cache was built from labels
      whose formula may carry a charge sign (e.g. 'C22H28N7O+', parsed there as C22H28N7O; the pinned parser rejects it): the ONLY normalisation
      applied here is stripping one trailing '+' / '-' from the root and fragment formulas, and every such row is listed by id. PASS(1) = every
      one of the N rows converts and agrees on all five fields (denominator N, no exclusions). instruments are compared and reported separately
      (the model does not read them: embed_instrument=False).
  (2) RAW-peak path (merge -> assign, the CASMI preprocessing) vs compact, per id: identical / tie_order_only (same length, same CLS row and padding,
      same per-position intensity sequence, same multiset of fragment tuples (formula vector, ion, peak_type, stored intensity)) / otherwise flags
      count, root, intensity, formula, ion, peak_type (several allowed) / failure (exception). Written to check_c2_raw_ids.csv; totals = N.
  (3) prediction differences raw vs compact: signed Tanimoto difference (mean, quantiles, improved / worse / unchanged), absolute quantiles,
      per class, the ids with the largest differences, max absolute probability difference.
Usage (Spark, .venv-mist, CUDA hidden): python -X utf8 experiments/mist/check_c2.py <ckpt> <compact msg dir> <msg_all dir> <MassSpecGym.tsv> <check_a json> <out.json>"""
import hashlib, json, os, sys, time
from collections import Counter
from pathlib import Path
import numpy as np, pandas as pd, torch
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mist_adapter as A
from mist.data import featurizers as FZ
from mist.data.atlas import unpack_fingerprints
from mist.data.input_signal import SpectrumOnlyDataset
from mist.metrics import tanimoto_scores
from mist.models.scaled_mist import ScaledMIST
from mist.utils import chem_utils as C
ck_path, croot, msg_all, tsv, cka, out = sys.argv[1], Path(sys.argv[2]) / "test", Path(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4"))); t0 = time.time()
ck_sha = sha(ck_path); ca = json.load(open(cka))
if os.path.basename(ca["checkpoint"]) != os.path.basename(ck_path): sys.exit("check A json is for another checkpoint")
thr = ca["val_threshold"]
bind = dict(checkpoint_sha256=ck_sha, check_a_sha256=sha(cka), adapter_sha256=sha(os.path.join(HERE, "mist_adapter.py")), compact_manifest_sha256=sha(croot / "manifest.json"),
            no_subform_sha256=sha(msg_all / "subformulae" / "no_subform.hdf5"), massspecgym_tsv_sha256=sha(tsv), threshold=thr)
ds = SpectrumOnlyDataset(croot); names = ds.names(); N = len(ds)
cons = dict(n=N, names_unique=bool(len(set(names)) == N))
fps = unpack_fingerprints(np.concatenate([np.load(p / "fingerprints.npy", mmap_mode="r") for p in ds.part_paths])).astype(bool); cons["fingerprints_shape_ok"] = bool(fps.shape == (N, 4096))
rows_c = [ds[i] for i in range(N)]
cls_ok = pad_ok = 0
for r in rows_c:
    L = int(r["lengths"]); cls_ok += int(r["peak_type"][L - 1] == 3 and (r["peak_type"][:L - 1] == 0).all())
    pad_ok += int((r["form_vec"][L:] == 0).all() and (r["ion_vec"][L:] == 0).all() and (np.asarray(r["intens"][L:], float) == 0).all() and (r["peak_type"][L:] == 0).all())
cons.update(cls_position_ok=cls_ok, padding_ok=pad_ok)
msg = pd.read_csv(tsv, sep="\t", usecols=["identifier", "mzs", "intensities", "precursor_mz", "adduct", "formula", "instrument_type"])
cons["tsv_identifiers_unique"] = bool(msg.identifier.is_unique); msg = msg.set_index("identifier")
ids = [n.split("_collision")[0] for n in names]; cons["names_map_to_tsv"] = int(sum(i in msg.index for i in ids))
MF = ("lengths", "peak_type", "ion_vec", "form_vec", "intens")
strip = lambda f: f[:-1] if isinstance(f, str) and f[-1:] in "+-" and len(f) > 1 else f
store = FZ.HDF5TextStore(msg_all / "subformulae" / "no_subform.hdf5")
agree1, fail1, charged1, inst1 = Counter(), [], [], 0
for i, nm in enumerate(names):
    try:
        tree = json.loads(store.read(f"{nm}.json")); tab = tree.get("output_tbl")
        if strip(tree["cand_form"]) != tree["cand_form"]: charged1.append(nm)
        tree["cand_form"] = strip(tree["cand_form"])
        if tab is not None:
            cnt = len(tab.get("mz", [])); fo = tab.get("formula", []); io = tab.get("ions", [])
            if len(fo) != cnt or len(io) != cnt or any(not isinstance(v, str) or not v for v in fo) or any(v not in C.ION_LST for v in io): tree = FZ.assign_subformulae(tree, 20.0)
            else: tab["formula"] = [strip(v) for v in fo]
        r = A.tree_to_row(tree, msg.loc[ids[i]].instrument_type)
        ok_all = True
        for k in MF:
            e = bool(np.array_equal(np.asarray(r[k]), np.asarray(rows_c[i][k]))); agree1[k] += int(e); ok_all &= e
        agree1["all"] += int(ok_all); inst1 += int(np.asarray(r["instruments"]) == np.asarray(rows_c[i]["instruments"]))
    except Exception as e:
        fail1.append((nm, repr(e)[:200]))
pass1 = (not fail1) and agree1["all"] == N
same_table = dict(agree_counts={k: int(v) for k, v in agree1.items()}, agree_share={k: v / N for k, v in agree1.items()}, failures=fail1, charge_stripped_ids=charged1,
                  instruments_agree=inst1 / N, pass_=bool(pass1))
recs, rows_a, okidx = [], [], []
for i, nm in enumerate(names):
    r0 = msg.loc[ids[i]]
    try:
        ra = A.featurize([float(x) for x in r0.mzs.split(",")], [float(x) for x in r0.intensities.split(",")], r0.precursor_mz, r0.formula, r0.adduct, r0.instrument_type)
    except Exception as e:
        recs.append(dict(id=nm, cls="failure", flags="", reason=repr(e)[:200])); continue
    rc = rows_c[i]; rows_a.append(ra); okidx.append(i)
    if all(np.array_equal(np.asarray(ra[k]), np.asarray(rc[k])) for k in MF): recs.append(dict(id=nm, cls="identical", flags="", reason="")); continue
    na, nc = int(ra["lengths"]), int(rc["lengths"]); fl = []
    if na != nc: fl.append("count")
    if not (np.array_equal(ra["form_vec"][na - 1], rc["form_vec"][nc - 1]) and int(ra["ion_vec"][na - 1]) == int(rc["ion_vec"][nc - 1])): fl.append("root")
    if na == nc:
        ia, ic = np.asarray(ra["intens"][:na - 1], float), np.asarray(rc["intens"][:nc - 1], float)
        tup = lambda r, n: sorted(tuple(r["form_vec"][k].tolist()) + (int(r["ion_vec"][k]), int(r["peak_type"][k]), float(r["intens"][k])) for k in range(n - 1))
        if not np.array_equal(ia, ic): fl.append("intensity")
        if sorted(tuple(ra["form_vec"][k].tolist()) for k in range(na - 1)) != sorted(tuple(rc["form_vec"][k].tolist()) for k in range(nc - 1)): fl.append("formula")
        if sorted(int(ra["ion_vec"][k]) for k in range(na - 1)) != sorted(int(rc["ion_vec"][k]) for k in range(nc - 1)): fl.append("ion")
        if not np.array_equal(ra["peak_type"][:na], rc["peak_type"][:nc]): fl.append("peak_type")
        if not fl and tup(ra, na) == tup(rc, nc): recs.append(dict(id=nm, cls="tie_order_only", flags="", reason="")); continue
    recs.append(dict(id=nm, cls="other", flags="+".join(fl) if fl else "unclassified", reason=""))
R = pd.DataFrame(recs); assert len(R) == N
ck = torch.load(ck_path, map_location="cpu", weights_only=True); model = ScaledMIST(**ck["config"]["model"]); model.load_state_dict(ck["ema_model"], strict=True); model.eval()
def predict(rows):
    o = np.zeros((len(rows), 4096), np.float32)
    with torch.inference_mode():
        for s in range(0, len(rows), 256): o[s:s + 256] = model(A.collate(rows[s:s + 256]))[0].float().numpy()
    return o
pa = predict(rows_a); pc = predict([rows_c[i] for i in okidx])
ta, tc = tanimoto_scores(pa, fps[okidx], thr), tanimoto_scores(pc, fps[okidx], thr); d = ta - tc
R["t_raw"] = np.nan; R["t_compact"] = np.nan; R.loc[R.cls != "failure", "t_raw"] = ta; R.loc[R.cls != "failure", "t_compact"] = tc; R["d"] = R.t_raw - R.t_compact
R.to_csv(os.path.splitext(out)[0] + "_raw_ids.csv", index=False)
q = lambda v, qs: {str(x): float(np.quantile(v, x)) for x in qs} if len(v) else {}
pred = dict(signed=dict(mean=float(d.mean()), quantiles=q(d, (0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999)), improved=int((d > 1e-12).sum()), worse=int((d < -1e-12).sum()), unchanged=int((np.abs(d) <= 1e-12).sum())),
            absolute=dict(quantiles=q(np.abs(d), (0.5, 0.9, 0.99, 0.999)), max=float(np.abs(d).max())),
            by_class={c: dict(n=int(len(g)), mean=float(g.d.mean()), min=float(g.d.min()), max=float(g.d.max())) for c, g in R[R.cls != "failure"].groupby("cls")},
            largest=R.reindex(R.d.abs().sort_values(ascending=False).index).head(10)[["id", "cls", "flags", "d"]].to_dict("records"),
            max_abs_probability_diff=float(np.abs(pa - pc).max()))
res = dict(binding=bind, consistency=cons, same_table=same_table, raw_path=dict(classes=R.cls.value_counts().to_dict(), flags=R[R.cls == "other"]["flags"].value_counts().to_dict(),
           failures=R[R.cls == "failure"][["id", "reason"]].to_dict("records")), prediction=pred,
           status=("C2_PASS" if (pass1 and cons["names_unique"] and cons["fingerprints_shape_ok"] and cons["cls_position_ok"] == N and cons["padding_ok"] == N and cons["names_map_to_tsv"] == N) else "C2_FAIL"),
           seconds=round(time.time() - t0))
json.dump(res, open(out, "w"), indent=1, default=str); print(json.dumps({k: res[k] for k in ("status", "consistency", "raw_path")}, indent=1, default=str)[:3000])
raise SystemExit(0 if res["status"] == "C2_PASS" else 1)
