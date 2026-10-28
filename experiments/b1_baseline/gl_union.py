"""115 v2 (Codex 120 Q3): ONE GLACIER run for the candidates that the frozen existing cache does not cover, over the UNION of the arms' todo lists,
so a new candidate's value does not depend on which arm happened to compute it first. Input: the per-arm todo files written by
`gl_share.py prepare --cache <existing run>` (runner-input format: [{mid, spectra..., cands}], scoreable uncovered candidates only). Output: one
runner input with, per molecule, the identical query (every field except 'cands'; a molecule whose query differs between arms -> STOP) and the
sorted union of the arms' candidates; molecules sorted by mid. Arm names never enter the order. Usage: python gl_union.py OUT.json TODO_1.json ..."""
import json, sys
out, ins = sys.argv[1], sys.argv[2:]
if len(ins) < 2: sys.exit("STOP: need at least two arm todo files")
key = lambda it: json.dumps({k: v for k, v in it.items() if k != "cands"}, sort_keys=True)
Q, C = {}, {}
for f in ins:
    items = json.load(open(f)); mids = [it["mid"] for it in items]
    if len(mids) != len(set(mids)): sys.exit(f"STOP: duplicate molecules in {f}")
    for it in items:
        m = str(it["mid"])
        if Q.setdefault(m, (key(it), it))[0] != key(it): sys.exit(f"STOP: molecule {m}: the query differs between the arm todo files")
        C.setdefault(m, set()).update(it["cands"])
U = [dict(Q[m][1], cands=sorted(C[m])) for m in sorted(Q)]
json.dump(U, open(out, "w"))
print(f"union: molecules {len(U)}, candidates {sum(len(u['cands']) for u in U)} (per arm: {', '.join(str(sum(len(it['cands']) for it in json.load(open(f))) ) for f in ins)})")
