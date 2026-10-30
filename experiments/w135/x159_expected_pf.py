"""159 decision D (round trip, step 1 on Spark): the expected P and F lists of every development query, built INDEPENDENTLY of the U2 builder:
P = the frozen v1 table's P rows by rank (experiments/w135/fh/U_<world>.parquet); F = the submitted pipeline's branches applied to P and the
v2.1 world E2 scores (P empty -> empty; E empty -> P; else e2_engine.fuse_rrf(P, full-window E2 ranks, E2 top 25, 0.5)). Keys only, no label.
Writes experiments/w135/x159_expected_pf.json = {world: {molecule: {"P": [...], "F": [...]}}}.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x159_expected_pf.py"""
import json, os, sys
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/e2")); sys.path.insert(1, os.path.join(ROOT, "experiments/b1_baseline"))
import e2_engine as E2M
DEV = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
out = {}
for w in DEV:
    b = w.split("_p")[0]
    U = pd.read_parquet(os.path.join(ROOT, "experiments/w135/fh", f"U_{w}.parquet"), columns=["molecule", "key", "src", "rP"]); U["molecule"] = U.molecule.astype(str)
    Q = pd.read_parquet(os.path.join(ROOT, "experiments/w135/fh", f"Q_{w}.parquet"), columns=["molecule"]); Q["molecule"] = Q.molecule.astype(str)
    E = pd.read_parquet(os.path.join(ROOT, "experiments/w135/v2_1", w, f"e2s_{b}.parquet"), columns=["molecule", "official_key", "e2_rank"]); E["molecule"] = E.molecule.astype(str)
    d = {}
    for m in Q.molecule:
        p = U[(U.molecule == m) & (U.src == "P")].sort_values("rP").key.astype(str).tolist()
        e = E[E.molecule == m].sort_values("e2_rank"); er = dict(zip(e.official_key.astype(str), e.e2_rank.astype(int))); e25 = e.official_key.astype(str).tolist()[:25]
        f = [] if not p else (list(p) if not e25 else E2M.fuse_rrf(p, er, e25, 0.5))
        d[m] = dict(P=p, F=f)
    out[w] = d
json.dump(out, open(os.path.join(ROOT, "experiments/w135/x159_expected_pf.json"), "w"))
print(f"expected P / F lists for {sum(len(v) for v in out.values())} development queries")
