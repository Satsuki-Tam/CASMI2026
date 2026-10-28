"""115 pilot step 1 (Codex 115): export round trip of GLACIER predictions, no FPNet involved. For N covered molecules of a runner input (a
TRAINING-side table, never an evaluation set), in ONE process: (A) gl_runner's own score_molecule on the Predictor cache, (B) the same
score_molecule on a cache rebuilt from the peaks written by the gl_simulate.py format (float32 m/z / intensity, offsets) and read back.
A == B on every (molecule, candidate) proves the export is lossless for the runner's scoring path; also records prediction failures, peaks per
prediction and seconds per prediction (for budgeting). Molecules are chosen by a fixed hash of the molecule id (no label, no score).
Usage (.venv-ice, Spark): python gl_simtest.py <glacier pkg> <runner_in.json> <out_dir> [--n 150] [--max_cands 40] [--device cuda]"""
import argparse, hashlib, json, os, sys, time
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("pkg"); ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--n", type=int, default=150); ap.add_argument("--max_cands", type=int, default=40); ap.add_argument("--device", default="cuda"); ap.add_argument("--bs", type=int, default=32)
a = ap.parse_args(); t0 = time.time(); os.makedirs(a.out, exist_ok=True)
pkg = os.path.abspath(a.pkg); sys.path.insert(0, pkg)
import gl_runner as G
ga = G.parse([pkg, "-", "-", "--device", a.device, "--site", "none", "--bs", str(a.bs)]); log = G.Log(False); rd = G.setup_env(ga, log)
import torch
dev = a.device if (a.device != "cuda" or torch.cuda.is_available()) else "cpu"
torch.use_deterministic_algorithms(True, warn_only=True)
model = G.load_model(pkg, dev, log, None); pred = G.Predictor(model, dev, a.bs, log)
mols = json.load(open(a.inp))
h = lambda s: hashlib.sha256(str(s).encode()).hexdigest()
mols = sorted([m for m in mols if any(G.is_covered(sp) for sp in m.get("spectra") or [])], key=lambda m: h(m["mid"]))[:a.n]
plans, cands, jobs = {}, {}, set()
for m in mols:
    mid = str(m["mid"]); plans[mid] = G.molecule_plan(m)
    cs = [c for c in dict.fromkeys(m.get("cands") or []) if G.smiles_ok(c)[0]][:a.max_cands]; cands[mid] = cs; jobs |= G.molecule_jobs(plans[mid], cs)
t1 = time.time(); pred.predict(jobs, float("inf")); tp = time.time() - t1
A = {mid: G.score_molecule(plans[mid], cands[mid], pred.cache) for mid in plans}
keys = sorted(k for k in pred.cache if pred.cache[k] is not None)
off = [0]; mz = []; it = []
for k in keys: mz.append(pred.cache[k][0].astype(np.float32)); it.append(pred.cache[k][1].astype(np.float32)); off.append(off[-1] + len(pred.cache[k][0]))
np.savez(os.path.join(a.out, "simtest_peaks.npz"), off=np.asarray(off, np.int64), mz=np.concatenate(mz) if mz else np.zeros(0, np.float32), it=np.concatenate(it) if it else np.zeros(0, np.float32))
json.dump([list(k) for k in keys], open(os.path.join(a.out, "simtest_keys.json"), "w"))
Z = np.load(os.path.join(a.out, "simtest_peaks.npz")); K = [tuple(k) for k in json.load(open(os.path.join(a.out, "simtest_keys.json")))]
cache2 = {k: (Z["mz"][Z["off"][i]:Z["off"][i + 1]].astype(np.float64), Z["it"][Z["off"][i]:Z["off"][i + 1]].astype(np.float64)) for i, k in enumerate(K)}
for k, v in pred.cache.items():
    if v is None: cache2[k] = None
B = {mid: G.score_molecule(plans[mid], cands[mid], cache2) for mid in plans}
diffs = [abs(A[m][c] - B[m][c]) for m in A for c in A[m] if A[m][c] is not None and B[m][c] is not None]
mism = sum(1 for m in A for c in A[m] if (A[m][c] is None) != (B[m][c] is None))
res = dict(rdkit=rd, device=dev, molecules=len(plans), candidates=sum(len(v) for v in cands.values()), jobs=len(jobs), predicted=len(keys), failed=sum(1 for v in pred.cache.values() if v is None),
           seconds_predict=round(tp, 1), seconds_per_prediction=round(tp / max(1, len(jobs)), 5), peaks_median=float(np.median(np.diff(off))) if len(off) > 1 else 0.0,
           scored_pairs=len(diffs), max_abs_diff=float(max(diffs)) if diffs else None, none_mismatch=mism, passed=bool(diffs) and max(diffs) == 0.0 and mism == 0)
json.dump(res, open(os.path.join(a.out, "simtest_result.json"), "w"), indent=1); log("SIMTEST", json.dumps(res))
