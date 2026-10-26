"""050: merge a run's original GLACIER output with the proxy-only GLACIER output (proxy molecules only; a molecule that already had a finite
score in the original output is NEVER overwritten -- proxies are only built for molecules without a covered positive spectrum, so this is an
assertion, not a policy). Writes <out> + <out>.meta.json in the runner format read by b1_locked_eval.runner().
Usage: python px_merge.py --orig RUN/work/gl_S.json --px RUNPX/work/glpx_S.json --out RUNPX/work/gl_S.json
"""
import argparse, json, os
ap = argparse.ArgumentParser(); ap.add_argument("--orig", required=True); ap.add_argument("--px", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
def load(p):
    try: return json.load(open(p))
    except Exception: return {}
O, P = load(a.orig), load(a.px); om = load(a.orig + ".meta.json"); pm = load(a.px + ".meta.json")
fin = lambda d: any(v is not None for v in (d or {}).values())
M = {k: v for k, v in O.items()}; clash, added = [], 0
for mid, d in P.items():
    if not fin(d): continue
    if fin(O.get(mid)): clash.append(mid); continue
    M[mid] = d; added += 1
assert not clash, f"proxy molecules that already had forward scores: {clash[:5]}"
json.dump(M, open(a.out, "w"))
meta = dict(status="ok", n_mols=len(M), n_mols_scored=sum(fin(v) for v in M.values()), merged=dict(orig=a.orig, orig_status=om.get("status"), orig_scored=sum(fin(v) for v in O.values()),
            px=a.px, px_status=pm.get("status"), px_scored=sum(fin(v) for v in P.values()), added=added))
json.dump(meta, open(a.out + ".meta.json", "w"), indent=1); print(json.dumps(meta["merged"]))
