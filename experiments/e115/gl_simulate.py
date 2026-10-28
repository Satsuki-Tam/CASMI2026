"""115 (pilot tool, not a registered experiment): GLACIER-simulated spectra for a list of structures. The gl_runner machinery is used unchanged
(setup_env, load_model, the canonicalisation smiles_ok, Predictor = JointModel.predict_inten_frag_batch + the runner's post-processing: drop
non-positive rows, merge identical m/z by max, top 100, sort by m/z, max 1); only the output differs: the predicted peaks of every
(smiles, adduct, instrument token, CE) job are stored instead of a similarity to a query.
Usage (.venv-ice, on the Spark): python gl_simulate.py <glacier pkg> <jobs.json> <out_prefix> [--device cuda] [--site none] [--chunk 20000] [--bs 32]
  [--start S --stop E]  (115 v2: only jobs[S:E]; stored job indices stay GLOBAL)
  jobs.json : [[smiles, adduct, instr_token, ce], ...]  (instr_token 'QTOF' / 'Orbitrap'; adduct '[M+H]+' / '[M+Na]+')
  output    : <out_prefix>_<k>.npz per chunk (GLOBAL job index, offsets, concatenated mz / intensity as float32), each written to a temp file and
              renamed (atomic); <out_prefix>_meta.json rewritten (temp + rename) after EVERY chunk and at the end: it covers jobs[start:stop] of the
              chunks written so far (complete = the requested range is done), with counts, the failed and rejected job indices, and the sha256
              of the job list, the GLACIER checkpoint, the runner and this script (Codex 119), so a stopped run can be continued under a NEW
              prefix with --start <stop>. An existing meta or shard under the prefix is refused (no overwrite)."""
import argparse, glob, hashlib, json, os, sys, time
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("pkg"); ap.add_argument("jobs"); ap.add_argument("out")
ap.add_argument("--device", default="cuda"); ap.add_argument("--site", default="none"); ap.add_argument("--chunk", type=int, default=20000); ap.add_argument("--bs", type=int, default=32)
ap.add_argument("--start", type=int, default=0); ap.add_argument("--stop", type=int, default=-1)
a = ap.parse_args(); t0 = time.time()


def fsha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


if os.path.exists(a.out + "_meta.json") or glob.glob(a.out + "_[0-9]*.npz"): sys.exit(f"STOP: {a.out} already has a meta or shards (use a new prefix)")
pkg = os.path.abspath(a.pkg); sys.path.insert(0, pkg)
jobs_all = json.load(open(a.jobs)); NJ = len(jobs_all); STOP_ = NJ if a.stop < 0 else a.stop; OFF = a.start
if not (0 <= OFF <= STOP_ <= NJ): sys.exit(f"STOP: range [{OFF}, {STOP_}) outside the job list of {NJ}")
jobs = [tuple(j) for j in jobs_all[OFF:STOP_]]; del jobs_all
CK = os.path.join(pkg, "ckpt", "glacier.pt")
hashes = dict(jobs=fsha(a.jobs), glacier_ckpt=fsha(CK) if os.path.exists(CK) else None, gl_runner=fsha(os.path.join(pkg, "gl_runner.py")), gl_simulate=fsha(os.path.abspath(__file__)))
import gl_runner as G
ga = G.parse([pkg, "-", "-", "--device", a.device, "--site", a.site, "--bs", str(a.bs)])
log = G.Log(False)
rd = G.setup_env(ga, log)
import torch
dev = a.device if (a.device != "cuda" or torch.cuda.is_available()) else "cpu"
torch.use_deterministic_algorithms(True, warn_only=True)
model = G.load_model(pkg, dev, log, None)
pred = G.Predictor(model, dev, a.bs, log)
meta = dict(n_jobs=0, n_jobs_list=NJ, start=OFF, stop=OFF, requested_stop=STOP_, complete=False, rdkit=rd, device=dev, threads=torch.get_num_threads(),
            hashes=hashes, rejected={}, rejected_idx=[], failed_idx=[], n_ok=0, n_fail=0, chunks=0)


def write_meta():
    json.dump(meta, open(a.out + "_meta.json.tmp", "w"), indent=1); os.replace(a.out + "_meta.json.tmp", a.out + "_meta.json")


okc = {}
for k0 in range(0, len(jobs), a.chunk):
    part = jobs[k0:k0 + a.chunk]; keep = []
    for n, (smi, ad, ins, ce) in enumerate(part):
        if smi not in okc:
            okc[smi] = G.smiles_ok(smi)
        ok, why = okc[smi]
        if ok: keep.append((OFF + k0 + n, (smi, ad, ins, float(ce))))
        else: meta["rejected"][why] = meta["rejected"].get(why, 0) + 1; meta["rejected_idx"].append(OFF + k0 + n)
    pred.predict({j for _, j in keep}, float("inf"))
    idx, off, mz, it = [], [0], [], []
    for i, j in keep:
        v = pred.cache.get(j)
        if v is None or len(v[0]) == 0: meta["n_fail"] += 1; meta["failed_idx"].append(i); continue
        idx.append(i); mz.append(v[0].astype(np.float32)); it.append(v[1].astype(np.float32)); off.append(off[-1] + len(v[0])); meta["n_ok"] += 1
    fn = f"{a.out}_{meta['chunks']:04d}.npz"
    with open(fn + ".tmp", "wb") as fh:   # atomic: a killed run never leaves a truncated shard under the final name
        np.savez(fh, idx=np.asarray(idx, np.int64), off=np.asarray(off, np.int64),
                 mz=np.concatenate(mz) if mz else np.zeros(0, np.float32), it=np.concatenate(it) if it else np.zeros(0, np.float32))
    os.replace(fn + ".tmp", fn)
    meta["chunks"] += 1; pred.cache.clear(); pred.pcache.clear()
    meta["n_jobs"] += len(part); meta["stop"] = OFF + k0 + len(part); meta["seconds"] = round(time.time() - t0, 1)
    write_meta()   # covers jobs[start:stop] after EVERY chunk
    log(f"chunk {meta['chunks']}: jobs {len(part)}, predicted {len(idx)}, total ok {meta['n_ok']} fail {meta['n_fail']} ({time.time() - t0:.0f}s)")
meta["seconds"] = round(time.time() - t0, 1); meta["complete"] = meta["stop"] == STOP_
write_meta(); log("DONE", json.dumps({k: v for k, v in meta.items() if k not in ("failed_idx", "rejected_idx")})[:400])
