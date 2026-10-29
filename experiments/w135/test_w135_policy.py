"""Synthetic checks of w135_selector.policy / q_table (Codex 139): no real data is read."""
import json, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w135_selector as S
F = S.FEATS
def mk_model(p):   # all features standardised to 0 -> p = sigmoid(intercept)
    return dict(mean=[0.0] * len(F), scale=[1.0] * len(F), coef=[0.0] * len(F), intercept=float(np.log(p / (1 - p))))
def row(w, m, key, fz=1.0): return dict(world=w, molecule=m, key=key, w=1.0, **{f: (fz if f == "fz" else 0.0) for f in F})
q = [0.4, 0.3] + [0.0] * 23; qt = {"lib": q, "gl": q, "fb": q}
def Q(w, m, top, bn="gl"): return dict(world=w, batch="x", pi=30, molecule=m, fam=1, wclass="C3", used=False, top25=json.dumps(top), bin=bn, n_b=1, n_cand=len(top))
top25 = [f"K{i}" for i in range(25)]
cases = [("codex example", [row("w", "m", "X")], [Q("w", "m", top25)], 0.3, ("insert", 2)),
         ("P empty, B present", [row("w", "m", "X")], [Q("w", "m", [])], 0.05, ("insert", 1)),
         ("P length 1", [row("w", "m", "X")], [Q("w", "m", ["K0"])], 0.3, None),
         ("P length 2", [row("w", "m", "X")], [Q("w", "m", ["K0", "K1"])], 0.3, None),
         ("B empty", [], [Q("w", "m", top25)], 0.9, ("keep", 0)),
         ("low p, no tail cost: rank 3", [row("w", "m", "X")], [Q("w", "m", top25)], 0.01, ("insert", 3)),
         ("very low p keeps", [row("w", "m", "X")], [Q("w", "m", top25)], 0.0, None)]
ok = True
for name, rows, qs, p, want in cases:
    R = pd.DataFrame(rows, columns=["world", "molecule", "key", "w"] + F); res = S.policy(R, pd.DataFrame(qs), mk_model(p), qt).iloc[0]
    # expected from the formula
    top = json.loads(qs[0]["top25"]); G = []
    if len(R):
        for k in range(1, min(3, len(top) + 1) + 1):
            loss = sum(q[r - 1] * ((1 / r - 1 / (r + 1)) if r < 25 else 1 / 25) for r in range(k, min(25, len(top)) + 1)); G.append(p / k - loss)
    exp = ("insert", int(np.argmax(G)) + 1) if G and max(G) > 0 else ("keep", 0)
    got = (res.action, int(res.k)); new = json.loads(res.new25)
    good = got == exp and (want is None or got == want) and (new == top[:25] if got[0] == "keep" else new == (top[:got[1] - 1] + ["X"] + top[got[1] - 1:])[:25])
    ok &= good; print(f"{name:22s} G={[round(g, 4) for g in G]} got={got} expected={exp} {'OK' if good else 'FAIL'}")
# q_table: mixture pooling and empty-bin fallback
Qa = pd.DataFrame([dict(world="A", truth="t", top25=json.dumps(["t"] + ["u"] * 24), bin="gl")] * 90 + [dict(world="A", truth="t", top25=json.dumps(["u"] * 25), bin="fb")] * 10)
Qb = pd.DataFrame([dict(world="B", truth="t", top25=json.dumps(["u"] * 25), bin="gl")] * 1 + [dict(world="B", truth="t", top25=json.dumps(["u"] * 25), bin="fb")] * 99)
qt2 = S.q_table(pd.concat([Qa, Qb]))
ok &= abs(qt2["gl"][0] - 90 / 91) < 1e-12 and qt2["lib"] == S.q_table(pd.concat([Qa, Qb]))["lib"]
print("q_table gl q1", qt2["gl"][0], "expected", 90 / 91, "| empty lib bin falls back to all bins:", abs(qt2["lib"][0] - 90 / 200) < 1e-12)
ok &= abs(qt2["lib"][0] - 90 / 200) < 1e-12
print("POLICY_TESTS " + ("PASS" if ok else "FAIL")); sys.exit(0 if ok else 1)
