"""W135 stage-2 preparation (137 sketch; used only if stage 1 is INVEST / LIMITED): GLACIER runner input for the B products of one world.
Reads ONLY the molecule ids and the B_detail_<arm> column of the generation table (no truth, class, reach or P-rank column) and the world's
runner input (query spectra); writes <out>.json = [{mid, spectra, cands: B product SMILES (heavy-atom filter as b1_features)}] for gl_runner.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_prodgl_in.py --world experiments/w135/worlds/dF1_p30 --set dF1 --arm both
       --out experiments/w135/worlds/dF1_p30/prod_runner_in.json"""
import argparse, json, os, sys
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_features import heavy_ok
ap = argparse.ArgumentParser(); ap.add_argument("--world", required=True); ap.add_argument("--set", required=True); ap.add_argument("--arm", default="both")
ap.add_argument("--table", default="gen_full_v2"); ap.add_argument("--out", required=True); a = ap.parse_args()
W = a.world if os.path.isabs(a.world) else os.path.join(ROOT, a.world)
G = pd.read_parquet(os.path.join(W, a.table + ".parquet"), columns=["molecule", f"B_detail_{a.arm}"]); G["molecule"] = G.molecule.astype(str)
R = {d["mid"]: d for d in json.load(open(os.path.join(W, f"b1_runner_{a.set}_in.json")))}
out, n = [], 0
for m, det in zip(G.molecule, G[f"B_detail_{a.arm}"]):
    if m not in R: sys.exit(f"STOP: {m} has no world runner entry")
    cands = [d[1] for d in json.loads(det) if heavy_ok(d[1])]; n += len(cands)
    out.append(dict(mid=m, spectra=R[m]["spectra"], cands=cands))
json.dump(out, open(a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out), "w")); print(f"{len(out)} molecules, {n} product candidates -> {a.out}")
