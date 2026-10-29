"""W135 stage 2 reader v2 (139_decision.md / Codex 139; written before any selector result). Reads the per-query outcomes of the FROZEN policy on
the 13 confirmation worlds (w135_selector.py --mode apply) and applies the registered gate.
Technical checks (STOP = not established, never a performance NO): the apply meta (frozen model + freeze manifest hashes, the queries hash, the
13 worlds); one row per (world, molecule) and roster = batch; pi / wclass / fam / used equal to the batch CSV columns; the RRs recomputed from the
saved P list, the new list and the truth; invariants: keep -> new list = P's top 25 and RR unchanged; insert at k -> new = top[:k-1] + [x] +
top[k-1:24], x not in P's top 25, the DB candidates keep their relative order, x = truth -> RR = 1/k.
Primary (pi3 = 0.3, the 598 queries of (cF1, cR1), (cF2, cR2), (cF3, cR3)): Delta = mean(RR policy - RR P) over ALL 598 queries >= +0.02 AND the
pair bootstrap lower bound > 0 (pairs resampled, each replicate = sum of differences / number of queries of the drawn pairs; 4,000, seed 139;
three units -> exploratory) AND the family bootstrap lower bound > 0 (auxiliary: families resampled within each batch).
Costs (each: pair bootstrap lower >= -0.01, a pair keeps all its queries of both pi): C1 at pi 0.3, C2 at pi 0.3, C1 at pi 0, C2 at pi 0, all at pi 0.
PASS (all of the above) -> the next technical study (Kaggle integration, separate registration); otherwise NO.
Descriptive: pooled C1 / C2, insertion rate by world, k counts, C3 decomposition (truth in B; x = truth; inserted; RR by k), accuracy of insertions,
used / unused, structural proximity (< 0.85 to every design molecule; the frozen table w135_prox_audit.parquet), cU1, family / random.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_read_s2.py --queries experiments/w135/s2/confirm_queries.parquet"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--queries", required=True); ap.add_argument("--prox", default="experiments/w135/s2/w135_prox_audit.parquet"); a = ap.parse_args()
def stop(m): sys.exit(f"STOP (w135_read_s2, not established): {m}")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
PAIRS = [("cF1", "cR1"), ("cF2", "cR2"), ("cF3", "cR3")]
NEED = sorted([f"{b}_p{p}" for pr in PAIRS for b in pr for p in (30, 0)] + ["cU1_p30"])
QP = os.path.join(ROOT, a.queries) if not os.path.isabs(a.queries) else a.queries; MP = QP.replace("_queries.parquet", "_meta.json")
mt = json.load(open(MP))
if mt["mode"] != "apply" or sorted(mt["worlds"]) != NEED or mt["queries_sha256"] != sha(QP): stop("apply meta / worlds / hash")
D = pd.read_parquet(QP); D["molecule"] = D.molecule.astype(str)
if D.duplicated(["world", "molecule"]).any(): stop("duplicate (world, molecule)")
for w, g in D.groupby("world"):
    b, p = w.split("_p"); bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str); bt = bt.set_index("molecule")
    if set(g.molecule) != set(bt.index) or len(g) != len(bt): stop(f"{w}: roster")
    if not ((g.pi == int(p)).all() and (g.wclass.values == bt.loc[g.molecule, f"wclass_p{p}"].astype(str).values).all() and (g.fam.values == bt.loc[g.molecule, "fam"].values).all()
            and (g.used.values == bt.loc[g.molecule, "used"].values).all() and (g.truth.values == bt.loc[g.molecule, "scorer_key"].astype(str).values).all()): stop(f"{w}: columns differ from the batch")
def rr_of(lst, t): return next((1.0 / (i + 1) for i, k in enumerate(lst[:25]) if k == t), 0.0)
for r in D.itertuples(index=False):
    top, new = json.loads(r.top25), json.loads(r.new25)
    if abs(rr_of(top, r.truth) - r.rrP) > 1e-12 or abs(rr_of(new, r.truth) - r.rr) > 1e-12: stop(f"{r.world} {r.molecule}: RR recomputation")
    if r.action == "keep":
        if new != top[:25] or r.rr != r.rrP: stop(f"{r.world} {r.molecule}: keep changed the list")
    else:
        k = int(r.k)
        if r.x_key in top or new != (top[:k - 1] + [r.x_key] + top[k - 1:])[:25] or [x for x in new if x != r.x_key] != top[:len(new) - 1]: stop(f"{r.world} {r.molecule}: insertion invariant")
        if r.x_key == r.truth and abs(r.rr - 1.0 / k) > 1e-12: stop(f"{r.world} {r.molecule}: truth inserted but RR != 1/k")
D["d"] = D.rr - D.rrP
rng = np.random.default_rng(139)
MAIN = [f"{b}_p30" for pr in PAIRS for b in pr]; ZERO = [f"{b}_p0" for pr in PAIRS for b in pr]
def pair_of(w): return w.split("_p")[0][-1]
def pair_boot(df, n=4000):
    by = {pk: (g.d.sum(), len(g)) for pk, g in df.groupby(df.world.map(pair_of))}; keys = sorted(by); est = df.d.sum() / len(df)
    bs = []
    for _ in range(n):
        dr = [keys[i] for i in rng.integers(0, len(keys), len(keys))]; bs.append(sum(by[k][0] for k in dr) / sum(by[k][1] for k in dr))
    return float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(len(df))
def fam_boot(df, n=4000):
    groups = {b: [g.d.values for _, g in d_.groupby("fam")] for b, d_ in df.groupby("batch")}; bs = np.empty(n)
    for t in range(n):
        tot = cnt = 0.0
        for gl in groups.values():
            for i in rng.integers(0, len(gl), len(gl)): tot += gl[i].sum(); cnt += len(gl[i])
        bs[t] = tot / cnt
    return float(df.d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(len(df))
P30 = D[D.world.isin(MAIN)]; P0 = D[D.world.isin(ZERO)]
if len(P30) != 598: stop(f"primary set has {len(P30)} queries, registered 598")
prim_pair = pair_boot(P30); prim_fam = fam_boot(P30)
costs = {"C1 at pi 0.3": pair_boot(P30[P30.wclass == "C1"]), "C2 at pi 0.3": pair_boot(P30[P30.wclass == "C2"]), "C1 at pi 0": pair_boot(P0[P0.wclass == "C1"]),
         "C2 at pi 0": pair_boot(P0[P0.wclass == "C2"]), "all at pi 0": pair_boot(P0)}
gate = prim_pair[0] >= 0.02 and prim_pair[1] > 0 and prim_fam[1] > 0 and all(v[1] >= -0.01 for v in costs.values())
c3 = P30[P30.wclass == "C3"]; c3b = c3[c3.truth_in_B.astype(bool)]; ins = D[D.action == "insert"]
desc = dict(pooled_C1=pair_boot(D[D.world.isin(MAIN + ZERO) & (D.wclass == "C1")]), pooled_C2=pair_boot(D[D.world.isin(MAIN + ZERO) & (D.wclass == "C2")]),
            insertion_rate={w: float((g.action == "insert").mean()) for w, g in D.groupby("world")}, k_counts={int(k): int(v) for k, v in ins.k.value_counts().items()},
            insert_accuracy=float((ins.x_key == ins.truth).mean()) if len(ins) else None,
            c3_p30=dict(n=int(len(c3)), truth_in_B=int(len(c3b)), x_is_truth=int((c3b.x_key == c3b.truth).sum()), x_is_truth_and_inserted=int(((c3b.x_key == c3b.truth) & (c3b.action == "insert")).sum()),
                        rr_by_k={int(k): int(v) for k, v in c3[(c3.rr > 0)].k.value_counts().items()}, mean_rr=float(c3.rr.mean())),
            by_world={w: dict(d=float(g.d.mean()), rrP=float(g.rrP.mean()), rr=float(g.rr.mean()), n=int(len(g))) for w, g in D.groupby("world")},
            by_type_p30={t: float(P30[P30.batch.str[1] == t[0].upper()].d.mean()) for t in ("family", "random")},
            used_p30={str(u): float(g.d.mean()) for u, g in P30.groupby("used")}, cU1=float(D[D.world == "cU1_p30"].d.mean()))
PX = os.path.join(ROOT, a.prox)
if os.path.exists(PX):
    X = pd.read_parquet(PX); X["molecule"] = X.molecule.astype(str); far = set(X[X.max_tan_design < 0.85].molecule)
    desc["prox_far_p30"] = dict(n=int(P30.molecule.isin(far).sum()), d=float(P30[P30.molecule.isin(far)].d.mean()), prox_table_sha256=sha(PX))
L = ["# W135 stage 2 reading v2 (frozen selector + policy, fold-2 confirmation worlds)", "",
     f"- **primary pi 0.3 (598 queries): {prim_pair[0]:+.4f} [pair {prim_pair[1]:+.4f}, {prim_pair[2]:+.4f}] [family {prim_fam[1]:+.4f}, {prim_fam[2]:+.4f}]**"]
L += [f"- cost {k}: {v[0]:+.4f} [{v[1]:+.4f}, {v[2]:+.4f}] (n {v[3]})" for k, v in costs.items()]
L += ["", f"**Gate: {'PASS' if gate else 'NO'}**", "", f"- descriptive: {json.dumps(desc)}"]
out = os.path.splitext(QP)[0]
open(out + "_reading.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(primary_pair=prim_pair, primary_family=prim_fam, costs=costs, gate="PASS" if gate else "NO", descriptive=desc, queries_sha256=sha(QP), reader_sha256=sha(os.path.abspath(__file__)),
               model_sha256=mt.get("model_sha256"), freeze_sha256=mt.get("freeze_sha256")), open(out + "_reading.json", "w"), indent=1)
print("\n".join(L))
