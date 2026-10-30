"""161 (Codex 160 Q3): coverage decomposition on the DEVELOPMENT worlds only (e-worlds are refused). Per query, from the v2.1 tables:
  in_U2   truth in U2 (U2 row with y = 1);
  shortlist  truth NOT in U2 but in the masked world E window (E ledger truth_in_ewin) -> the E rank of the truth (26-50 / 51-100 / >100)
             and whether the truth is in B (cannot be: then it would be in U2) -- a shortlist (top-25) problem;
  outside    truth in neither U2 nor the E window -> a window / source / generation problem (C3 by construction lands here unless B has it);
             split by the truth's rank in P's FULL candidate list (W135 P.parquet rP, 0 = absent): 26-50 / 51-100 / >100 / absent from P.
Reported per population (primary pi0.3 F/R 1,198; pi0; pi0.3 by class) with counts and shares. Descriptive; no model is read.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x161_coverage.py"""
import json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FH2 = os.path.join(ROOT, "experiments/w135/fh2_1"); V2 = os.path.join(ROOT, "experiments/w135/v2_1")
DEV = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
rows = []
for w in DEV:
    if w.startswith("e"): sys.exit("STOP: e-worlds are never read")
    b = w.split("_p")[0]
    U2 = pd.read_parquet(os.path.join(FH2, f"U2_{w}.parquet"), columns=["molecule", "key", "y"]); Q2 = pd.read_parquet(os.path.join(FH2, f"Q2_{w}.parquet"), columns=["molecule", "wclass", "pi", "truth"])
    E = pd.read_parquet(os.path.join(V2, w, f"e2s_{b}.parquet"), columns=["molecule", "official_key", "e2_rank"])
    L = pd.read_csv(os.path.join(V2, w, f"ewin_molecules_{b}.csv"), usecols=["molecule", "truth_in_ewin"], dtype={"molecule": str}).set_index("molecule")
    PW = pd.read_parquet(os.path.join(ROOT, "experiments/w135/worlds", w, "P.parquet"), columns=["molecule", "rP"]); PW["molecule"] = PW.molecule.astype(str); prk = dict(zip(PW.molecule, PW.rP.astype(int)))
    for D in (U2, Q2, E): D["molecule"] = D.molecule.astype(str)
    hit = set(U2[U2.y == 1].molecule)
    for m, wc, pi, t in Q2[["molecule", "wclass", "pi", "truth"]].itertuples(index=False):
        er = E[(E.molecule == m) & (E.official_key.astype(str) == str(t))].e2_rank
        rows.append(dict(world=w, batch=b, molecule=m, wclass=wc, pi=int(pi), in_U2=m in hit, in_Ewin=bool(L.loc[m, "truth_in_ewin"]), e_rank=int(er.iloc[0]) if len(er) else -1, p_rank=int(prk.get(m, 0))))
D = pd.DataFrame(rows)
D["primary"] = (D.pi == 30) & D.batch.str[1].isin(["F", "R"])
D["group"] = np.where(D.in_U2, "in_U2", np.where(D.in_Ewin, "shortlist", "outside"))
out = {}
pops = [("PRIMARY pi0.3 F/R", D.primary), ("pi0 all", D.pi == 0)] + [(f"pi0.3 {c}", D.primary & (D.wclass == c)) for c in ("C1", "C2", "C3")] + [(f"pi0 {c}", (D.pi == 0) & (D.wclass == c)) for c in ("C1", "C2")]
for name, m in pops:
    d = D[m]; n = len(d); c = d.group.value_counts().to_dict(); s = d[d.group == "shortlist"]
    bins = dict(r26_50=int(((s.e_rank >= 26) & (s.e_rank <= 50)).sum()), r51_100=int(((s.e_rank >= 51) & (s.e_rank <= 100)).sum()), r101plus=int((s.e_rank > 100).sum()), unscored=int((s.e_rank < 0).sum()))
    o = d[d.group == "outside"]; pb = dict(p26_50=int(((o.p_rank >= 26) & (o.p_rank <= 50)).sum()), p51_100=int(((o.p_rank >= 51) & (o.p_rank <= 100)).sum()), p101plus=int((o.p_rank > 100).sum()), p_absent=int((o.p_rank == 0).sum()), p_le25=int(((o.p_rank >= 1) & (o.p_rank <= 25)).sum()))
    out[name] = dict(n=n, **{k: int(c.get(k, 0)) for k in ("in_U2", "shortlist", "outside")}, shortlist_e_rank=bins, outside_p_rank=pb)
    print(f"{name:20s} n {n:5d} | in U2 {c.get('in_U2', 0):5d} ({c.get('in_U2', 0) / n:.3f}) | shortlist (in E window, not in U2) {c.get('shortlist', 0):4d} ({c.get('shortlist', 0) / n:.3f}) "
          f"E rank 26-50 {bins['r26_50']} / 51-100 {bins['r51_100']} / >100 {bins['r101plus']} | outside both {c.get('outside', 0):4d} ({c.get('outside', 0) / n:.3f}): "
          f"P full rank 26-50 {pb['p26_50']} / 51-100 {pb['p51_100']} / >100 {pb['p101plus']} / absent {pb['p_absent']} (<=25 {pb['p_le25']})")
json.dump(out, open(os.path.join(ROOT, "experiments/w135/x161_coverage.json"), "w"), indent=1)
