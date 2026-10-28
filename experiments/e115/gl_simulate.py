"""115 (pilot tool, not a registered experiment): GLACIER-simulated spectra for a list of structures. The gl_runner machinery is used unchanged
(setup_env, load_model, the canonicalisation smiles_ok, Predictor = JointModel.predict_inten_frag_batch + the runner's post-processing: drop
non-positive rows, merge identical m/z by max, top 100, sort by m/z, max 1); only the output differs: the predicted peaks of every
(smiles, adduct, instrument token, CE) job are stored instead of a similarity to a query.
Usage (.venv-ice, on the Spark): python gl_simulate.py <glacier pkg> <jobs.json> <out_prefix> [--device cuda] [--site none] [--chunk 20000] [--bs 32]
  jobs.json : [[smiles, adduct, instr_token, ce], ...]  (instr_token 'QTOF' / 'Orbitrap'; adduct '[M+H]+' / '[M+Na]+')
  output    : <out_prefix>_<k>.npz per chunk (job index, offsets, concatenated mz / intensity as float32) + <out_prefix>_meta.json
              (counts, rejected structures by reason, failed predictions, seconds)."""
import argparse, json, os, sys, time
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("pkg"); ap.add_argument("jobs"); ap.add_argument("out")
ap.add_argument("--device", default="cuda"); ap.add_argument("--site", default="none"); ap.add_argument("--chunk", type=int, default=20000); ap.add_argument("--bs", type=int, default=32)
a = ap.parse_args(); t0 = time.time()
pkg = os.path.abspath(a.pkg); sys.path.insert(0, pkg)
import gl_runner as G
ga = G.parse([pkg, "-", "-", "--device", a.device, "--site", a.site, "--bs", str(a.bs)])
log = G.Log(False)
rd = G.setup_env(ga, log)
import torch
dev = a.device if (a.device != "cuda" or torch.cuda.is_available()) else "cpu"
torch.use_deterministic_algorithms(True, warn_only=True)
model = G.load_model(pkg, dev, log, None)
pred = G.Predictor(model, dev, a.bs, log)
jobs = [tuple(j) for j in json.load(open(a.jobs))]
meta = dict(n_jobs=len(jobs), rdkit=rd, device=dev, rejected={}, n_ok=0, n_fail=0, chunks=0)
okc = {}
for k0 in range(0, len(jobs), a.chunk):
    part = jobs[k0:k0 + a.chunk]; keep = []
    for n, (smi, ad, ins, ce) in enumerate(part):
        if smi not in okc:
            okc[smi] = G.smiles_ok(smi)
        ok, why = okc[smi]
        if ok: keep.append((k0 + n, (smi, ad, ins, float(ce))))
        else: meta["rejected"][why] = meta["rejected"].get(why, 0) + 1
    pred.predict({j for _, j in keep}, float("inf"))
    idx, off, mz, it = [], [0], [], []
    for i, j in keep:
        v = pred.cache.get(j)
        if v is None or len(v[0]) == 0: meta["n_fail"] += 1; continue
        idx.append(i); mz.append(v[0].astype(np.float32)); it.append(v[1].astype(np.float32)); off.append(off[-1] + len(v[0])); meta["n_ok"] += 1
    np.savez(f"{a.out}_{meta['chunks']:04d}.npz", idx=np.asarray(idx, np.int64), off=np.asarray(off, np.int64),
             mz=np.concatenate(mz) if mz else np.zeros(0, np.float32), it=np.concatenate(it) if it else np.zeros(0, np.float32))
    meta["chunks"] += 1; pred.cache.clear(); pred.pcache.clear()
    log(f"chunk {meta['chunks']}: jobs {len(part)}, predicted {len(idx)}, total ok {meta['n_ok']} fail {meta['n_fail']} ({time.time() - t0:.0f}s)")
meta["seconds"] = round(time.time() - t0, 1)
json.dump(meta, open(f"{a.out}_meta.json", "w"), indent=1); log("DONE", json.dumps(meta)[:400])
