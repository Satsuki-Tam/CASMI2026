"""W135 stage 1 reader (136 pre-registration; written before any reach / oracle number). Reads the full-mode w135_gen.py tables of the design
worlds and computes, per pi3 world set:
  U    = mean over all batch queries of 1[truth among the B pre-selected products] (arm 'both' = train + peer parents) -- the oracle gain of
         the best allowed action (insert the truth at rank 1; the truth is then outside P's top 25 by construction), split into
         C3 rescue (class C3) and DB-miss rescue (C1 / C2);
  arm 'train' (train-analog parents only, same budget) and the reach h per class at the generation / pre-selection stages (descriptive);
  cluster bootstrap over families (Butina 0.5 labels; resampled within each batch; 4,000, seed 136), query-weighted.
Checks (STOP): every batch molecule has a row; no C3 truth is located 'short' / 'window' (a C3 truth in the world DB = leak); the rows
manifest of every world matches; the generation tables were written in full mode.
Decision (registered, pi3 = 0.3, pooled design batches dF1-3 + dR1-3, arm 'both', B = 50):
  U >= 0.04 -> INVEST (one small selector training, separate registration); 0.02 <= U < 0.04 -> LIMITED; U < 0.02 and 95% upper < 0.02 ->
  STOP (this generation configuration); U < 0.02 with upper >= 0.02 -> UNDETERMINED (registered extension: dF4-6 / dR4-6 at pi3 = 0.3).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_read.py --pi 30 [--batches dF1 dF2 dF3 dR1 dR2 dR3] [--decide]"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--pi", type=int, required=True); ap.add_argument("--batches", nargs="+", default=["dF1", "dF2", "dF3", "dR1", "dR2", "dR3"])
ap.add_argument("--decide", action="store_true", help="apply the registered decision (only for --pi 30 with the six design batches)"); ap.add_argument("--tag", default="")
a = ap.parse_args()
def stop(m): sys.exit(f"STOP (w135_read): {m}")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
rows = []
for b in a.batches:
    W = os.path.join(ROOT, "experiments/w135/worlds", f"{b}_p{a.pi}"); f = os.path.join(W, "gen_full.parquet")
    if not os.path.exists(f): stop(f"{f} missing")
    for ln in open(os.path.join(W, "manifest.txt")):
        h, p = ln.split()
        if sha(os.path.join(ROOT, p)) != h: stop(f"{p} differs from the world manifest")
    G = pd.read_parquet(f); bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str); G["molecule"] = G.molecule.astype(str)
    if "reach_both" not in G.columns: stop(f"{b}: generation table not in full mode")
    miss = set(bt.molecule) - set(G.molecule)
    if miss: stop(f"{b}: {len(miss)} batch molecules without a generation row")
    G = G.merge(bt[["molecule", "fam", f"wclass_p{a.pi}"]], on="molecule", how="left")
    if (G.wclass != G[f"wclass_p{a.pi}"]).any(): stop(f"{b}: class mismatch")
    leak = G[(G.wclass == "C3") & (G.truth_loc_both.isin(["short", "window"]) | G.truth_loc_train.isin(["short", "window"]))]
    if len(leak): stop(f"{b}: C3 truth found in the world DB for {len(leak)} queries")
    G["batch"] = b; rows.append(G)
D = pd.concat(rows, ignore_index=True); D["kind"] = np.where(D.batch.str[1] == "F", "family", "random")
rng = np.random.default_rng(136)
def boot(df, col, n=4000):
    groups = {b: [g[col].values.astype(float) for _, g in d.groupby("fam")] for b, d in df.groupby("batch")}
    est = df[col].astype(float).mean(); bs = np.empty(n)
    for t in range(n):
        tot = cnt = 0.0
        for b, gl in groups.items():
            for i in rng.integers(0, len(gl), len(gl)): tot += gl[i].sum(); cnt += len(gl[i])
        bs[t] = tot / cnt
    return float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
D["U_both"] = D.reach_both.astype(float); D["U_train"] = D.reach_train.astype(float)
D["U_both_c3"] = D.U_both * (D.wclass == "C3"); D["U_both_dbmiss"] = D.U_both * (D.wclass != "C3")
for k_ in (10, 25, 100, 10 ** 9): D[f"U_both_B{k_ if k_ < 10 ** 9 else 'all'}"] = ((D.truth_rank_fz_both > 0) & (D.truth_rank_fz_both <= k_)).astype(float)   # descriptive budgets
out = dict(pi=a.pi, batches=a.batches, n=len(D))
for name, df in (("pooled", D), ("family", D[D.kind == "family"]), ("random", D[D.kind == "random"])):
    if not len(df): continue
    out[name] = {c: boot(df, c) for c in ("U_both", "U_train", "U_both_c3", "U_both_dbmiss", "U_both_B10", "U_both_B25", "U_both_B100", "U_both_Ball")}
    out[name]["h_by_class"] = {c: dict(n=int((df.wclass == c).sum()), prod_both=float(df[df.wclass == c].truth_prod_both.mean()) if (df.wclass == c).any() else None,
                                       reach_both=float(df[df.wclass == c].reach_both.mean()) if (df.wclass == c).any() else None,
                                       reach_train=float(df[df.wclass == c].reach_train.mean()) if (df.wclass == c).any() else None) for c in ("C1", "C2", "C3")}
    rk = df[df.truth_rank_fz_both > 0].truth_rank_fz_both
    out[name]["truth_fz_rank_among_products"] = dict(n=int(len(rk)), le1=int((rk <= 1).sum()), le3=int((rk <= 3).sum()), le10=int((rk <= 10).sum()), le50=int((rk <= 50).sum()))
dec = None
if a.decide:
    if a.pi != 30 or sorted(a.batches) != sorted(["dF1", "dF2", "dF3", "dR1", "dR2", "dR3"]): stop("the registered decision uses pi 30 and the six design batches")
    U, lo, hi = out["pooled"]["U_both"]
    dec = "INVEST" if U >= 0.04 else ("LIMITED" if U >= 0.02 else ("STOP" if hi < 0.02 else "UNDETERMINED"))
    out["decision"] = dec
L = [f"# W135 stage 1 reading (pi3 = {a.pi / 100:.1f}; batches {', '.join(a.batches)}; arm both = train + peer parents, B = 50)", ""]
for name in ("pooled", "family", "random"):
    if name not in out: continue
    o = out[name]; L.append(f"## {name}")
    for c in ("U_both", "U_train", "U_both_c3", "U_both_dbmiss", "U_both_B10", "U_both_B25", "U_both_B100", "U_both_Ball"): L.append(f"- {c}: {o[c][0]:+.4f} [{o[c][1]:+.4f}, {o[c][2]:+.4f}]")
    for c, v in o["h_by_class"].items(): L.append(f"- {c}: n {v['n']}, truth generated {v['prod_both']}, reach (both / train) {v['reach_both']} / {v['reach_train']}")
    L.append(f"- truth f.z rank among pre-selectable products: {o['truth_fz_rank_among_products']}"); L.append("")
if dec: L.append(f"**Decision (registered): {dec}**")
tag = a.tag or f"p{a.pi}"
open(os.path.join(ROOT, "experiments/w135", f"stage1_{tag}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(out, reader_sha256=sha(os.path.abspath(__file__))), open(os.path.join(ROOT, "experiments/w135", f"stage1_{tag}.json"), "w"), indent=1); print("\n".join(L))
