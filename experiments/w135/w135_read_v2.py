"""W135 stage 1 reader v2 (136_decision.md; Codex 136 Q3 / Q5 -- written before any reach number). Reads the full-mode w135_gen_v2.py tables
of the six design worlds at one pi3 and computes the registered numbers.
Checks (STOP, exit 1): the world manifests (every file hash); each generation meta (world manifest hash, output hash, registered arguments:
budget 50, n_train 10, n_peer 10, the class column); one row per batch molecule (no missing, extra or duplicate (set, molecule)); oracle
prerequisites for every reached query (P's main RR 0, rP 0 or > 25, the truth not in P's top 25, the truth in the stored B list, its f.z rank
<= B) and reach <=> 0 < truth f.z rank <= B; B lists unique and <= 50; no C3 truth in P's top 25, in the world window official keys or located
'top25' / 'in_window'; finite main / rP; U = U_C3 + U_DBmiss with the full-query denominator.
Numbers: U (arm both = train + peer parents; the gain of the oracle that inserts the truth at rank 1 when it is in B and keeps P otherwise --
an upper bound of the allowed action, not a policy's gain), U_C3 / U_DBmiss, arm train, budgets 10 / 25 / 100 / all, reach by class at the
generation and the pre-selection stage, the truth's f.z rank, parent sources of the reached truths.
Intervals: PRIMARY (exploratory, three independent units) = the three (dFj, dRj) pairs resampled with replacement, every query of a pair kept,
50:50 design mean, 4,000, seed 136; AUXILIARY = families resampled within each batch (conditional on the fixed peer environment of a batch).
Decision (registered; pi3 = 0.3, the six design batches, arm both, B = 50; LIMITED = 0.02 <= U < 0.04):
  U >= 0.04 -> INVEST (one small selector training, separate registration); 0.02 <= U < 0.04 -> LIMITED; U < 0.02 and pair upper < 0.02 ->
  STOP (an engineering stop of investment in THIS frozen generation configuration, not a proof that the population bound is below 0.02);
  U < 0.02 and pair upper >= 0.02 -> UNDETERMINED (no investment now; any re-test is a separate registration with new batches; no extension).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_read_v2.py --pi 30 [--decide]"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--pi", type=int, required=True); ap.add_argument("--decide", action="store_true"); ap.add_argument("--table", default="gen_full_v2"); a = ap.parse_args()
PAIRS = [("dF1", "dR1"), ("dF2", "dR2"), ("dF3", "dR3")]; BATCHES = [b for p in PAIRS for b in p]; BUD = 50
def stop(m): sys.exit(f"STOP (w135_read_v2): {m}")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
rows = []
for b in BATCHES:
    W = os.path.join(ROOT, "experiments/w135/worlds", f"{b}_p{a.pi}"); f = os.path.join(W, a.table + ".parquet"); fm = os.path.join(W, a.table + ".meta.json")
    if not (os.path.exists(f) and os.path.exists(fm)): stop(f"{b}: generation table / meta missing")
    for ln in open(os.path.join(W, "manifest.txt")):
        h, p = ln.split()
        if sha(os.path.join(ROOT, p)) != h: stop(f"{p} differs from the world manifest")
    mt = json.load(open(fm)); ar = mt["args"]
    if mt["world_manifest_sha256"] != sha(os.path.join(W, "manifest.txt")) or mt["output_sha256"] != sha(f): stop(f"{b}: generation meta does not match")
    if (ar["budget"], ar["n_train"], ar["n_peer"], ar["wclass_col"], ar["set"], bool(ar["speed_only"])) != (BUD, 10, 10, f"wclass_p{a.pi}", b, False): stop(f"{b}: arguments differ from the registration {ar}")
    G = pd.read_parquet(f); G["molecule"] = G.molecule.astype(str)
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str)
    if G.duplicated(["set", "molecule"]).any() or set(G.molecule) != set(bt.molecule) or len(G) != len(bt) or (G.set != b).any(): stop(f"{b}: rows are not one per batch molecule")
    G = G.merge(bt[["molecule", "fam", f"wclass_p{a.pi}"]], on="molecule", how="left", validate="one_to_one")
    if (G.wclass != G[f"wclass_p{a.pi}"]).any(): stop(f"{b}: class mismatch")
    if not (np.isfinite(G.main.astype(float)).all() and np.isfinite(G.rP.astype(float)).all()): stop(f"{b}: non-finite main / rP")
    for arm in ("both", "train"):
        rk = G[f"truth_rank_fz_{arm}"].astype(int); re_ = G[f"reach_{arm}"].astype(bool)
        if (re_ != ((rk > 0) & (rk <= BUD))).any(): stop(f"{b} {arm}: reach inconsistent with the f.z rank")
        if (G[f"n_pre_{arm}"] > BUD).any(): stop(f"{b} {arm}: B longer than {BUD}")
        for r in G[re_].itertuples(index=False):
            Bl = json.loads(getattr(r, f"B_{arm}")); tk = str(bt.set_index("molecule").loc[r.molecule, "scorer_key"])
            if r.main != 0 or not (r.rP == 0 or r.rP > 25) or r.truth_in_top25 or tk not in Bl or len(set(Bl)) != len(Bl) or len(Bl) > BUD: stop(f"{b} {arm} {r.molecule}: oracle prerequisite fails")
    c3 = G.wclass == "C3"
    if (G[c3].truth_in_top25 | G[c3].truth_in_window_okey | G[c3].truth_loc_both.isin(["top25", "in_window"]) | G[c3].truth_loc_train.isin(["top25", "in_window"])).any(): stop(f"{b}: a C3 truth is in the world DB / P")
    G["batch"] = b; rows.append(G)
D = pd.concat(rows, ignore_index=True)
D["U_both"] = D.reach_both.astype(float); D["U_train"] = D.reach_train.astype(float)
D["U_both_c3"] = D.U_both * (D.wclass == "C3"); D["U_both_dbmiss"] = D.U_both * (D.wclass != "C3")
for k_ in (10, 25, 100, 10 ** 9): D[f"U_both_B{k_ if k_ < 10 ** 9 else 'all'}"] = ((D.truth_rank_fz_both > 0) & (D.truth_rank_fz_both <= k_)).astype(float)
if abs(D.U_both.mean() - D.U_both_c3.mean() - D.U_both_dbmiss.mean()) > 1e-12: stop("U != U_C3 + U_DBmiss")
COLS = ["U_both", "U_train", "U_both_c3", "U_both_dbmiss", "U_both_B10", "U_both_B25", "U_both_B100", "U_both_Ball"]
rng = np.random.default_rng(136)
def pair_boot(col, n=4000):
    pm = np.array([0.5 * D[D.batch == f_][col].mean() + 0.5 * D[D.batch == r_][col].mean() for f_, r_ in PAIRS])
    bs = np.array([pm[rng.integers(0, len(pm), len(pm))].mean() for _ in range(n)]); return float(pm.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
def fam_boot(df, col, n=4000):
    groups = {b: [g[col].values.astype(float) for _, g in d.groupby("fam")] for b, d in df.groupby("batch")}; bs = np.empty(n)
    for t in range(n):
        tot = cnt = 0.0
        for b, gl in groups.items():
            for i in rng.integers(0, len(gl), len(gl)): tot += gl[i].sum(); cnt += len(gl[i])
        bs[t] = tot / cnt
    return float(df[col].astype(float).mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
out = dict(pi=a.pi, n=len(D), batches=BATCHES, primary_pair={c: pair_boot(c) for c in COLS}, auxiliary_family={c: fam_boot(D, c) for c in ("U_both", "U_train", "U_both_c3")},
           by_type={t: {c: float(D[D.batch.str[1] == t[0].upper()][c].mean()) for c in COLS} for t in ("family", "random")},
           by_batch={b: {c: float(D[D.batch == b][c].mean()) for c in ("U_both", "U_train", "U_both_c3", "U_both_dbmiss")} for b in BATCHES},
           by_class={c: dict(n=int((D.wclass == c).sum()), truth_generated_both=float(D[D.wclass == c].truth_prod_both.mean()), reach_both=float(D[D.wclass == c].reach_both.mean()),
                             reach_train=float(D[D.wclass == c].reach_train.mean())) for c in ("C1", "C2", "C3")},
           truth_fz_rank_both=dict(zip(["le1", "le3", "le10", "le25", "le50", "le100", "any"], [int(((D.truth_rank_fz_both > 0) & (D.truth_rank_fz_both <= k)).sum()) for k in (1, 3, 10, 25, 50, 100, 10 ** 9)])),
           reached_sources_both=D[D.reach_both.astype(bool)].truth_srcs_both.value_counts().to_dict(),
           parents=dict(train_median=float(D.n_train.median()), both_median=float(D.n_both.median()), peer_struct_median=float(D.n_peer_struct.median())))
dec = None
if a.decide:
    if a.pi != 30: stop("the registered decision uses pi 30")
    U, lo, hi = out["primary_pair"]["U_both"]
    dec = "INVEST" if U >= 0.04 else ("LIMITED" if U >= 0.02 else ("STOP" if hi < 0.02 else "UNDETERMINED")); out["decision"] = dec
L = [f"# W135 stage 1 (reader v2): pi3 = {a.pi / 100:.1f}, design batches {', '.join(BATCHES)}, arm both = train + peer parents, B = {BUD}", "",
     "## U (primary interval: the three (dF, dR) pairs, exploratory; auxiliary: families within batches)"]
for c in COLS:
    v = out["primary_pair"][c]; L.append(f"- {c}: {v[0]:+.4f} [{v[1]:+.4f}, {v[2]:+.4f}]" + (f" | family-bootstrap [{out['auxiliary_family'][c][1]:+.4f}, {out['auxiliary_family'][c][2]:+.4f}]" if c in out["auxiliary_family"] else ""))
L += ["", f"- by type: {json.dumps({t: {k: round(v, 4) for k, v in d.items()} for t, d in out['by_type'].items()})}", f"- by batch: {json.dumps({b: {k: round(v, 4) for k, v in d.items()} for b, d in out['by_batch'].items()})}",
      f"- by class: {json.dumps(out['by_class'])}", f"- truth f.z rank (arm both, pre-selectable products): {out['truth_fz_rank_both']}", f"- reached truths by parent source: {out['reached_sources_both']}", f"- parents: {out['parents']}"]
if dec: L += ["", f"**Decision (registered): {dec}**"]
open(os.path.join(ROOT, "experiments/w135", f"stage1_v2_p{a.pi}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(out, reader_sha256=sha(os.path.abspath(__file__))), open(os.path.join(ROOT, "experiments/w135", f"stage1_v2_p{a.pi}.json"), "w"), indent=1); print("\n".join(L))
