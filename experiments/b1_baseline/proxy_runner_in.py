"""050: forward-model proxy inputs for an EXISTING evaluation run, without recomputing its tables.

b1_features --adduct_proxy writes runner inputs as rspec + forward_proxies(rspec, neg) (proxies only when the molecule has no covered positive
spectrum); this script applies exactly that function to the saved runner input of a run (b1_runner_<set>_in.json) and keeps only the molecules
that gain proxies, so GLACIER is re-run on those molecules only. Every other molecule keeps the run's original forward scores.
Usage: python -X utf8 proxy_runner_in.py --inp RUN/b1_runner_S_in.json --out RUNPX/b1_runner_S_in.json [--neg] --stats RUNPX/proxy_S.json
"""
import argparse, collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_common import forward_proxies
ap = argparse.ArgumentParser(); ap.add_argument("--inp", required=True); ap.add_argument("--out", required=True); ap.add_argument("--neg", action="store_true"); ap.add_argument("--stats", required=True)
a = ap.parse_args()
R = json.load(open(a.inp)); out, kinds, n_with = [], collections.Counter(), 0
for e in R:
    if any(s.get("proxy") for s in e["spectra"]): sys.exit(f"input already has proxies: {e['mid']}")
    px = forward_proxies(e["spectra"], neg=a.neg)
    if not px: continue
    n_with += 1; kinds.update(p["proxy"] for p in px)
    out.append(dict(e, spectra=e["spectra"] + px))
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True); json.dump(out, open(a.out, "w"))
st = dict(inp=a.inp, neg=bool(a.neg), molecules_in=len(R), molecules_with_proxy=n_with, proxy_spectra=dict(kinds), cands=sum(len(e["cands"]) for e in out))
json.dump(st, open(a.stats, "w"), indent=1); print(json.dumps(st))
