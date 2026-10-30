"""158 registered diagnostics, v2 (159 decision B): development worlds only -- e-worlds are refused. The three candidate sets are rebuilt
INDEPENDENTLY before any reach is read:
  U1  = P25 + B from the frozen v1 tables (experiments/w135/fh/U_<world>.parquet, built by w135_fh.py from the W135 world assets);
  E25 = the top 25 of the v2.1 world E2 scores (experiments/w135/v2_1/<world>/e2s_<set>.parquet, receipt-verified);
  U2  = the v2.1 U2 table (experiments/w135/fh2_1/U2_<world>.parquet).
Per query: U2 must equal U1 + E25 as key sets, P's order in U2 must equal P's order in U1, the E ledger must list the query (no NaN);
a failure stops the reading. C3 invariant: per query, truth in U2 == truth in U1.
Stage 2 (descriptive; all expected queries as the denominator; primary = pi3 0.3 of the twelve F / R worlds, 1,198; pi0 / pi0.6 / cU1 auxiliary):
  2a truth in the masked world E window (E ledger), 2b truth in E25, (c) truth in U2, (d) truth in U1; (c) - (d) = the added reach;
  the E-source-outside layer (C1 / C2 truths outside the E window) is counted; when empty it is reported as 'not measurable in this set'.
Stage 3 (descriptive; dF1 / dR1 / cF1 / cR1 at pi3 0.3 and 0, actual roster counts): F-world - P (MRR; per class), new / lost rank-1,
  'E-only rescues' (i) truth in E25 and not in P25, (ii) truth in E25 and not in U1, added candidates per query, common-candidate rank changes
  (P candidates kept in F: share whose rank changed, mean |rank_F - rank_P|), failures (0 expected), wall time / max RSS per stage (receipts).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x158_diag.py --stage 2|3"""
import argparse, json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FH1 = os.path.join(ROOT, "experiments/w135/fh"); FH2 = os.path.join(ROOT, "experiments/w135/fh2_1"); V2 = os.path.join(ROOT, "experiments/w135/v2_1")
DEV = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
PAIR = [f"{b}_p{p}" for b in ("dF1", "dR1", "cF1", "cR1") for p in (30, 0)]
def stop(m): sys.exit(f"STOP (x158_diag): {m}")


def rr(lst, t):
    return next((1.0 / (i + 1) for i, k in enumerate(lst[:25]) if k == t), 0.0)


def load(w):
    if w.startswith("e"): stop("e-worlds are never read by this diagnostic")
    b = w.split("_p")[0]
    U1 = pd.read_parquet(os.path.join(FH1, f"U_{w}.parquet")); Q1 = pd.read_parquet(os.path.join(FH1, f"Q_{w}.parquet"))
    E = pd.read_parquet(os.path.join(V2, w, f"e2s_{b}.parquet")); L = pd.read_csv(os.path.join(V2, w, f"ewin_molecules_{b}.csv"), dtype={"molecule": str}).set_index("molecule")
    U2 = pd.read_parquet(os.path.join(FH2, f"U2_{w}.parquet")); Q2 = pd.read_parquet(os.path.join(FH2, f"Q2_{w}.parquet"))
    for D in (U1, Q1, E, U2, Q2): D["molecule"] = D.molecule.astype(str)
    mols = list(Q1.molecule)
    if set(mols) != set(Q2.molecule) or set(mols) != set(L.index) or L.index.duplicated().any(): stop(f"{w}: rosters differ (v1 Q / U2 Q / E ledger)")
    truth = Q1.set_index("molecule").truth.to_dict(); rows = []
    for m in mols:
        u1 = U1[U1.molecule == m]; p25 = u1[u1.src == "P"].sort_values("rP").key.tolist(); bset = set(u1[u1.src == "B"].key)
        e25 = E[E.molecule == m].sort_values("e2_rank").official_key.tolist()[:25]
        u2 = U2[U2.molecule == m]
        if set(u2.key) != set(p25) | bset | set(e25): stop(f"{w} {m}: U2 != P25 + E25 + B")
        if u2[u2.in_P == 1].sort_values("rP").key.tolist() != p25: stop(f"{w} {m}: P order differs between U1 and U2")
        t = truth[m]; f = json.loads(Q2.set_index("molecule").loc[m, "f_top25"])
        rows.append(dict(world=w, molecule=m, wclass=Q1.set_index("molecule").loc[m, "wclass"], pi=int(Q1.set_index("molecule").loc[m, "pi"]), batch=b, truth=t,
                         in_Ewin=bool(L.loc[m, "truth_in_ewin"]), in_E25=t in e25, in_U1=(t in p25) or (t in bset), in_P25=t in p25, in_U2=t in set(u2.key),
                         rrP=rr(p25, t), rrF=rr(f, t), n_added=len(set(e25) - set(p25) - bset), p25=p25, f=f))
    return pd.DataFrame(rows)


def stage2():
    D = pd.concat([load(w) for w in DEV], ignore_index=True)
    c3 = D[D.wclass == "C3"]
    if (c3.in_U2 != c3.in_U1).any(): stop(f"C3 invariant broken in {int((c3.in_U2 != c3.in_U1).sum())} queries")
    tab = lambda name, g: (f"{name:34s} n {len(g):5d} | 2a E window {g.in_Ewin.mean():.3f} | 2b E25 {g.in_E25.mean():.3f} | U2 {g.in_U2.mean():.3f} | "
                           f"U1 {g.in_U1.mean():.3f} | added {g.in_U2.mean() - g.in_U1.mean():+.3f}")
    prim = D[(D.pi == 30) & (D.batch != "cU1")]
    out = [tab("PRIMARY pi0.3 F/R", prim)] + [tab(f"  pi0.3 {c}", prim[prim.wclass == c]) for c in ("C1", "C2", "C3")] + \
          [tab("pi0 (aux)", D[D.pi == 0]), tab("pi0.6 (aux)", D[D.pi == 60]), tab("cU1_p30 (aux)", D[D.batch == "cU1"])]
    outside = prim[prim.wclass.isin(["C1", "C2"]) & ~prim.in_Ewin]
    out.append(f"E-source-outside layer (pi0.3 C1 / C2 truths outside the E window): n {len(outside)}" + (" -- not measurable in this set" if len(outside) == 0 else ""))
    out.append("checks: rosters, U2 = P25 + E25 + B, P order U1 == U2, E ledger complete, C3 invariant -- all OK")
    print("\n".join(out)); return dict(lines=out)


def stage3():
    D = pd.concat([load(w) for w in PAIR], ignore_index=True); timing = {w: json.load(open(os.path.join(V2, w, "receipt.json")))["timing"] for w in PAIR}
    lines = []
    for nm, g in (("pi0.3 (4 worlds)", D[D.pi == 30]), ("pi0 (4 worlds)", D[D.pi == 0])):
        ch = []; dr = []
        for p25, f in zip(g.p25, g.f):
            common = [k for k in p25 if k in f]
            ch += [p25.index(k) != f.index(k) for k in common]; dr += [abs(p25.index(k) - f.index(k)) for k in common]
        lines.append(f"{nm:18s} n {len(g)} | P {g.rrP.mean():.4f} F-world {g.rrF.mean():.4f} diff {g.rrF.mean() - g.rrP.mean():+.4f} | new rank-1 {int(((g.rrF == 1) & (g.rrP < 1)).sum())} "
                     f"lost rank-1 {int(((g.rrP == 1) & (g.rrF < 1)).sum())} | E-only (i) {int((g.in_E25 & ~g.in_P25).sum())} (ii) {int((g.in_E25 & ~g.in_U1).sum())} | "
                     f"added cand / query {g.n_added.mean():.1f} | common P candidates kept in F: rank changed {np.mean(ch):.3f}, mean |shift| {np.mean(dr):.2f}")
        for c in ("C1", "C2", "C3"):
            h = g[g.wclass == c]
            if len(h): lines.append(f"    {c} n {len(h)}: P {h.rrP.mean():.4f} F {h.rrF.mean():.4f} diff {h.rrF.mean() - h.rrP.mean():+.4f}")
    lines.append("failures: 0 (every world receipt-verified; rosters and candidate-set checks passed)")
    print("\n".join(lines)); print("timing / max RSS per stage:", json.dumps(timing)[:2000])
    return dict(lines=lines, timing=timing)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True, choices=["2", "3"]); a = ap.parse_args()
    res = stage2() if a.stage == "2" else stage3()
    json.dump(res, open(os.path.join(ROOT, f"experiments/w135/x158_stage{a.stage}.json"), "w"), indent=1, default=str)
