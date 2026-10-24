"""Resumable ICEBERG/GLACIER runner driver: restarts the runner on the molecules that have no scores yet after a crash (the GB10 CUDA
illegal-access error in ICEBERG's random-walk PE is sporadic), merging outputs; a molecule that heads three crashed runs is skipped.
Usage: python ice_resume.py <runner.py> <pkg_dir> <in.json> <out.json> [--python PY] [--max_restarts 12] [runner args...]
"""
import argparse, json, os, shutil, subprocess, sys, time

ap = argparse.ArgumentParser(); ap.add_argument("runner"); ap.add_argument("pkg"); ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--python", default=sys.executable); ap.add_argument("--max_restarts", type=int, default=12); ap.add_argument("rest", nargs=argparse.REMAINDER)
a = ap.parse_args(); t0 = time.time()
items = json.load(open(a.inp)); order = [it["mid"] for it in items]; by_mid = {it["mid"]: it for it in items}
merged = {}; skipped = []; head_fail = {}
for attempt in range(a.max_restarts + 1):
    todo = [m for m in order if m not in merged and m not in skipped]
    if not todo: break
    part_in = a.out + f".part{attempt}.in.json"; part_out = a.out + f".part{attempt}.json"
    json.dump([by_mid[m] for m in todo], open(part_in, "w"))
    cmd = [a.python, a.runner, a.pkg, part_in, part_out] + [x for x in a.rest if x != "--"]
    print(f"[resume] attempt {attempt}: {len(todo)} molecules remaining ({time.time()-t0:.0f}s)", flush=True)
    rc = subprocess.run(cmd, stdout=open(a.out + f".part{attempt}.log", "w"), stderr=subprocess.STDOUT).returncode
    try: res = json.load(open(part_out)); meta = json.load(open(part_out + ".meta.json"))
    except Exception as e: print("[resume] no output:", repr(e)); res, meta = {}, {"status": "missing"}
    done = {m: d for m, d in res.items() if d and any(v is not None for v in d.values())}
    merged.update(done)
    print(f"[resume] attempt {attempt}: status {meta.get('status')} rc {rc}, scored {len(done)} (total {len(merged)}/{len(order)})", flush=True)
    if meta.get("status") == "ok": break
    nxt = [m for m in todo if m not in merged]
    if nxt:
        head_fail[nxt[0]] = head_fail.get(nxt[0], 0) + 1
        if head_fail[nxt[0]] >= 3: skipped.append(nxt[0]); print(f"[resume] skipping {nxt[0]} after 3 failed heads", flush=True)
json.dump({m: merged.get(m, {s: None for s in by_mid[m]["cands"]}) for m in order}, open(a.out, "w"))
status = "ok" if not skipped and len(merged) == len(order) else ("partial" if merged else "error")
json.dump(dict(status=status, n_mols=len(order), n_mols_scored=len(merged), skipped=skipped, restarts=attempt, seconds=round(time.time() - t0), via="ice_resume.py"), open(a.out + ".meta.json", "w"), indent=1)
print(f"[resume] done: {status}, scored {len(merged)}/{len(order)}, skipped {len(skipped)}, {time.time()-t0:.0f}s", flush=True)
