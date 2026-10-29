"""W135 stage 2 reader (139_prereg_w135_stage2.md; written before any selector result). Reads the per-query outcomes of the frozen policy on the
confirmation worlds (w135_selector.py --mode apply) and applies the registered gate.
Checks (STOP): one row per (world, molecule) and the roster of each world = its batch; every confirmation world present; RR in [0, 1].
Primary: pi3 = 0.3, the three confirmation pairs (cF1, cR1), (cF2, cR2), (cF3, cR3): Delta = mean(RR policy - RR P) >= +0.02 AND the pair
bootstrap lower bound > 0 (three units, exploratory) AND the family bootstrap lower bound > 0 (auxiliary; families resampled within batches).
Costs (lower >= -0.01, family bootstrap): C1 queries (pi 0.3 and 0 pooled), C2 queries (pi 0.3 and 0 pooled), all queries at pi 0.
PASS if all hold, else NO. Descriptive: insertion rate, k counts, C3 mean RR, accuracy of insertions, cU1, family / random, per batch.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_read_s2.py --queries experiments/w135/s2/confirm_queries.parquet"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--queries", required=True); a = ap.parse_args()
def stop(m): sys.exit(f"STOP (w135_read_s2): {m}")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
PAIRS = [("cF1", "cR1"), ("cF2", "cR2"), ("cF3", "cR3")]
NEED = [f"{b}_p{p}" for pr in PAIRS for b in pr for p in (30, 0)] + ["cU1_p30"]
D = pd.read_parquet(a.queries); D["molecule"] = D.molecule.astype(str)
if D.duplicated(["world", "molecule"]).any(): stop("duplicate rows")
if sorted(set(D.world)) != sorted(NEED): stop(f"worlds {sorted(set(D.world))} != {sorted(NEED)}")
for w, g in D.groupby("world"):
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", w.split("_p")[0] + ".csv")); bt["molecule"] = bt.molecule.astype(str)
    if set(g.molecule) != set(bt.molecule): stop(f"{w}: roster differs from the batch")
if not ((D.rr >= 0) & (D.rr <= 1) & (D.rrP >= 0) & (D.rrP <= 1)).all(): stop("RR out of range")
D["d"] = D.rr - D.rrP
rng = np.random.default_rng(139)
def fam_boot(df, n=4000):
    groups = {b: [g.d.values for _, g in d_.groupby("fam")] for b, d_ in df.groupby("world")}; bs = np.empty(n)
    for t in range(n):
        tot = cnt = 0.0
        for gl in groups.values():
            for i in rng.integers(0, len(gl), len(gl)): tot += gl[i].sum(); cnt += len(gl[i])
        bs[t] = tot / cnt
    return float(df.d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
def pair_boot(pi, n=4000):
    pm = np.array([0.5 * D[D.world == f"{f_}_p{pi}"].d.mean() + 0.5 * D[D.world == f"{r_}_p{pi}"].d.mean() for f_, r_ in PAIRS])
    bs = np.array([pm[rng.integers(0, len(pm), len(pm))].mean() for _ in range(n)]); return float(pm.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
main_worlds = [f"{b}_p30" for pr in PAIRS for b in pr]; zero_worlds = [f"{b}_p0" for pr in PAIRS for b in pr]
P30 = D[D.world.isin(main_worlds)]; P0 = D[D.world.isin(zero_worlds)]; C12 = D[D.world.isin(main_worlds + zero_worlds)]
prim_pair = pair_boot(30); prim_fam = fam_boot(P30)
costs = {"C1 (pi 0.3 + 0)": fam_boot(C12[C12.wclass == "C1"]), "C2 (pi 0.3 + 0)": fam_boot(C12[C12.wclass == "C2"]), "all at pi 0": fam_boot(P0)}
gate = prim_pair[0] >= 0.02 and prim_pair[1] > 0 and prim_fam[1] > 0 and all(v[1] >= -0.01 for v in costs.values())
ins = D[D.action == "insert"]
desc = dict(insertion_rate={w: float((g.action == "insert").mean()) for w, g in D.groupby("world")}, k_counts=ins.k.value_counts().to_dict(),
            insert_accuracy=float(ins.x_is_truth.mean()) if len(ins) else None, c3_mean_rr_p30=float(P30[P30.wclass == "C3"].rr.mean()),
            c3_rescued_p30=int(((P30.wclass == "C3") & (P30.rr > 0)).sum()), by_world={w: dict(d=float(g.d.mean()), rrP=float(g.rrP.mean()), rr=float(g.rr.mean())) for w, g in D.groupby("world")},
            by_type_p30={t: float(P30[P30.world.str[1] == t[0].upper()].d.mean()) for t in ("family", "random")}, cU1=float(D[D.world == "cU1_p30"].d.mean()))
L = ["# W135 stage 2 reading (frozen selector + policy on the fold-2 confirmation worlds)", "",
     f"- **primary pi 0.3 (3 pairs): {prim_pair[0]:+.4f} [pair {prim_pair[1]:+.4f}, {prim_pair[2]:+.4f}] [family {prim_fam[1]:+.4f}, {prim_fam[2]:+.4f}]**"]
L += [f"- cost {k}: {v[0]:+.4f} [{v[1]:+.4f}, {v[2]:+.4f}]" for k, v in costs.items()]
L += ["", f"**Gate: {'PASS' if gate else 'NO'}**", "", f"- descriptive: {json.dumps(desc)}"]
out = os.path.splitext(a.queries)[0]
open(out + "_reading.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(primary_pair=prim_pair, primary_family=prim_fam, costs=costs, gate="PASS" if gate else "NO", descriptive=desc, queries_sha256=sha(a.queries), reader_sha256=sha(os.path.abspath(__file__))),
          open(out + "_reading.json", "w"), indent=1)
print("\n".join(L))
