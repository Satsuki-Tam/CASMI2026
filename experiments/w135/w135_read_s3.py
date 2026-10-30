"""W135 142 reader (142_prereg_w135_calib.md; written before any 142 number). Reads s3/confirm_queries.parquet (P, frozen 139 and C142 on the 12
fold-0 confirmation worlds) and applies the registered gate.
Technical checks (STOP = not established): the apply meta (worlds, freeze / base hashes, queries hash); one row per (world, molecule), roster =
batch; pi / wclass / fam / used / truth equal to the batch CSV; RRs recomputed from the saved lists for P, 139 and C142; insertion invariants for
both policies (keep -> list unchanged; insert at k -> top[:k-1] + [x] + top[k-1:24], x not in P's top 25, DB order kept; x = truth -> 1/k).
Primary (pi 0.3 worlds, all queries): Delta = mean(RR C142 - RR P) >= +0.02 AND pair bootstrap lower > 0 (three (eF, eR) pairs; each replicate =
sum of differences / queries of the drawn pairs; 4,000, seed 142; exploratory) AND family bootstrap lower > 0 (auxiliary).
Costs (pair bootstrap lower >= -0.01): C1 at pi 0.3, C2 at pi 0.3, C1 at pi 0, C2 at pi 0, all at pi 0.
Calibration claim (separate): C142 - 139 >= +0.005 and pair lower > 0. PASS (primary + costs) -> Kaggle integration study (separate
registration); otherwise NO. Descriptive: 139 on fold 0, insertion rates, k counts, C3 decomposition, mean p of the chosen x vs its accuracy.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_read_s3.py"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); S3 = os.path.join(ROOT, "experiments/w135/s3")
def stop(m): sys.exit(f"STOP (w135_read_s3, not established): {m}")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
PAIRS = [("eF1", "eR1"), ("eF2", "eR2"), ("eF3", "eR3")]; NEED = sorted(f"{b}_p{p}" for pr in PAIRS for b in pr for p in (30, 0))
mt = json.load(open(os.path.join(S3, "confirm_meta.json"))); QP = os.path.join(S3, "confirm_queries.parquet")
if sorted(mt["worlds"]) != NEED or mt["queries_sha256"] != sha(QP) or mt["freeze_sha256"] != sha(os.path.join(S3, "calib_freeze.json")): stop("apply meta")
D = pd.read_parquet(QP); D["molecule"] = D.molecule.astype(str)
if D.duplicated(["world", "molecule"]).any() or sorted(set(D.world)) != NEED: stop("rows / worlds")
for w, g in D.groupby("world"):
    b, p = w.split("_p"); bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str); bt = bt.set_index("molecule")
    if set(g.molecule) != set(bt.index) or len(g) != len(bt): stop(f"{w}: roster")
    if not ((g.pi == int(p)).all() and (g.wclass.values == bt.loc[g.molecule, f"wclass_p{p}"].astype(str).values).all() and (g.fam.values == bt.loc[g.molecule, "fam"].values).all()
            and (g.used.values == bt.loc[g.molecule, "used"].values).all() and (g.truth.values == bt.loc[g.molecule, "scorer_key"].astype(str).values).all()): stop(f"{w}: columns differ from the batch")
def rr_of(lst, t): return next((1.0 / (i + 1) for i, k in enumerate(lst[:25]) if k == t), 0.0)
for r in D.itertuples(index=False):
    top = json.loads(r.top25)
    if abs(rr_of(top, r.truth) - r.rrP) > 1e-12: stop(f"{r.world} {r.molecule}: P RR")
    for act, k, x, new_s, rr in ((r.action, r.k, r.x_key, r.new25, r.rr), (r.action_139, r.k_139, r.x_key_139, r.new25_139, r.rr_139)):
        new = json.loads(new_s)
        if abs(rr_of(new, r.truth) - rr) > 1e-12: stop(f"{r.world} {r.molecule}: RR recomputation")
        if act == "keep":
            if new != top[:25] or abs(rr - r.rrP) > 1e-12: stop(f"{r.world} {r.molecule}: keep changed the list")
        else:
            k = int(k)
            if x in top or new != (top[:k - 1] + [x] + top[k - 1:])[:25] or [v for v in new if v != x] != top[:len(new) - 1]: stop(f"{r.world} {r.molecule}: insertion invariant")
            if x == r.truth and abs(rr - 1.0 / k) > 1e-12: stop(f"{r.world} {r.molecule}: truth inserted but RR != 1/k")
rng = np.random.default_rng(142)
def pb(df, col):
    by = {pk: (df[df.world.str[2] == pk][col].sum(), int((df.world.str[2] == pk).sum())) for pk in ("1", "2", "3")}; est = df[col].sum() / len(df); bs = []
    for _ in range(4000):
        dr = [("1", "2", "3")[i] for i in rng.integers(0, 3, 3)]; n_ = sum(by[k][1] for k in dr); bs.append(sum(by[k][0] for k in dr) / n_ if n_ else 0.0)
    return float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(len(df))
def fb(df, col):
    groups = {b: [g[col].values for _, g in d_.groupby("fam")] for b, d_ in df.groupby("batch")}; bs = np.empty(4000)
    for t in range(4000):
        tot = cnt = 0.0
        for gl in groups.values():
            for i in rng.integers(0, len(gl), len(gl)): tot += gl[i].sum(); cnt += len(gl[i])
        bs[t] = tot / cnt
    return float(df[col].mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(len(df))
D["d142"] = D.rr - D.rrP; D["d139"] = D.rr_139 - D.rrP; D["d142_139"] = D.rr - D.rr_139
P30 = D[D.pi == 30]; P0 = D[D.pi == 0]
prim = pb(P30, "d142"); primf = fb(P30, "d142")
costs = {"C1 at pi 0.3": pb(P30[P30.wclass == "C1"], "d142"), "C2 at pi 0.3": pb(P30[P30.wclass == "C2"], "d142"), "C1 at pi 0": pb(P0[P0.wclass == "C1"], "d142"),
         "C2 at pi 0": pb(P0[P0.wclass == "C2"], "d142"), "all at pi 0": pb(P0, "d142")}
calib = pb(P30, "d142_139")
gate = prim[0] >= 0.02 and prim[1] > 0 and primf[1] > 0 and all(v[1] >= -0.01 for v in costs.values())
claim = calib[0] >= 0.005 and calib[1] > 0
c3 = P30[P30.wclass == "C3"]; c3b = c3[c3.truth_in_B.astype(bool)]
desc = dict(d139_p30=pb(P30, "d139"), d139_p0=pb(P0, "d139"), insertion_rate_142={str(p): float((D[D.pi == p].action == "insert").mean()) for p in (30, 0)},
            insertion_rate_139={str(p): float((D[D.pi == p].action_139 == "insert").mean()) for p in (30, 0)}, k_counts_142={int(k): int(v) for k, v in D[D.action == "insert"].k.value_counts().items()},
            c3_p30=dict(n=int(len(c3)), truth_in_B=int(len(c3b)), x_is_truth_142=int((c3b.x_key == c3b.truth).sum()), inserted_correct_142=int(((c3b.x_key == c3b.truth) & (c3b.action == "insert")).sum()),
                        rr_142=float(c3.rr.mean()), rr_139=float(c3.rr_139.mean())),
            calibration_p30=dict(mean_p_chosen_142=float(P30[P30.n_b > 0].p_hat.mean()), acc_chosen=float((P30[P30.n_b > 0].x_key == P30[P30.n_b > 0].truth).mean())),
            by_type_p30={t: float(P30[P30.batch.str[1] == t[0].upper()].d142.mean()) for t in ("family", "random")})
L = ["# W135 142 reading (two-stage calibration on the frozen 139; fold-0 confirmation worlds)", "",
     f"- **primary pi 0.3 C142 - P: {prim[0]:+.4f} [pair {prim[1]:+.4f}, {prim[2]:+.4f}] [family {primf[1]:+.4f}, {primf[2]:+.4f}] (n {prim[3]})**"]
L += [f"- cost {k}: {v[0]:+.4f} [{v[1]:+.4f}, {v[2]:+.4f}] (n {v[3]})" for k, v in costs.items()]
L += [f"- calibration claim C142 - 139 (pi 0.3): {calib[0]:+.4f} [{calib[1]:+.4f}, {calib[2]:+.4f}] -> {'established' if claim else 'not established'}", "",
      f"**Gate: {'PASS' if gate else 'NO'}**", "", f"- descriptive: {json.dumps(desc)}"]
open(os.path.join(S3, "reading.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(primary=prim, primary_family=primf, costs=costs, calibration=calib, gate="PASS" if gate else "NO", claim=bool(claim), descriptive=desc, reader_sha256=sha(os.path.abspath(__file__))),
          open(os.path.join(S3, "reading.json"), "w"), indent=1)
print("\n".join(L))
