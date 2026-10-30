"""158 registered diagnostics (158_prereg_v2_diag.md + 158_decision.md item 8): development worlds only -- e-worlds are refused.
Stage 2 (descriptive, all expected queries as the denominator; primary = pi3 0.3 of the twelve F / R worlds, 1,198; cU1 / pi0 auxiliary):
  2a truth in the masked world E window (E ledger), 2b truth in E2's top 25, (c) truth in U2, (d) truth in U1 = P25 + B; (c) - (d) = the
  added reach. C3 invariant: per query U2 reach == U1 reach (a difference stops the reading: mask / candidate-merge inconsistency).
Stage 3 (descriptive; dF1 / dR1 / cF1 / cR1 at pi3 0.3 and 0, the actual roster counts): F-world - P (MRR; per class), new / lost rank-1,
  'E-only rescues' (i) truth in E25 and not in P25, (ii) truth in E25 and not in P25 + B, added candidates per query, common-candidate rank
  changes (P rank vs F rank of the P candidates kept in F), wall time and max RSS per stage (v2.1 receipts), failures.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x158_diag.py --stage 2|3"""
import argparse, json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FH2 = os.path.join(ROOT, "experiments/w135/fh2_1"); V2 = os.path.join(ROOT, "experiments/w135/v2_1")
DEV = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
PAIR = [f"{b}_p{p}" for b in ("dF1", "dR1", "cF1", "cR1") for p in (30, 0)]


def rr(lst, t):
    lst = json.loads(lst) if isinstance(lst, str) else lst
    return next((1.0 / (i + 1) for i, k in enumerate(lst[:25]) if k == t), 0.0)


def load(w):
    if w.startswith("e"): sys.exit("STOP: e-worlds are never read by this diagnostic")
    U = pd.read_parquet(os.path.join(FH2, f"U2_{w}.parquet")); Q = pd.read_parquet(os.path.join(FH2, f"Q2_{w}.parquet"))
    b = w.split("_p")[0]; L = pd.read_csv(os.path.join(V2, w, f"ewin_molecules_{b}.csv"), dtype={"molecule": str}).set_index("molecule")
    U["molecule"] = U.molecule.astype(str); Q["molecule"] = Q.molecule.astype(str)
    t = U[U.y == 1].set_index("molecule")
    Q["in_Ewin"] = Q.molecule.map(L.truth_in_ewin).astype(bool)
    Q["in_E25"] = Q.molecule.map(t.in_E25).fillna(0).astype(bool)
    Q["in_U2"] = Q.molecule.isin(t.index)
    Q["in_U1"] = Q.molecule.map((t.in_P == 1) | (t.in_B == 1)).fillna(False).astype(bool)
    Q["in_P25"] = Q.molecule.map(t.in_P).fillna(0).astype(bool)
    return U, Q


def stage2():
    rows = []
    for w in DEV:
        U, Q = load(w); Q["world"] = w; rows.append(Q)
    D = pd.concat(rows, ignore_index=True)
    c3 = D[D.wclass == "C3"]
    if (c3.in_U2 != c3.in_U1).any(): sys.exit(f"STOP: C3 invariant broken in {int((c3.in_U2 != c3.in_U1).sum())} queries (U2 reach != U1 reach)")
    def tab(name, g):
        return f"{name:34s} n {len(g):5d} | 2a E window {g.in_Ewin.mean():.3f} | 2b E25 {g.in_E25.mean():.3f} | U2 {g.in_U2.mean():.3f} | U1 {g.in_U1.mean():.3f} | added {g.in_U2.mean() - g.in_U1.mean():+.3f}"
    prim = D[(D.pi == 30) & (D.batch != "cU1")]
    out = [tab("PRIMARY pi0.3 F/R", prim)] + [tab(f"  pi0.3 {c}", prim[prim.wclass == c]) for c in ("C1", "C2", "C3")] + \
          [tab("pi0 (aux)", D[D.pi == 0]), tab("pi0.6 (aux)", D[D.pi == 60]), tab("cU1_p30 (aux)", D[D.batch == "cU1"])]
    print("\n".join(out)); print("C3 invariant (U2 reach == U1 reach per query): OK")
    return dict(lines=out)


def stage3():
    out = []; S = []
    for w in PAIR:
        U, Q = load(w)
        P_lists = {m: g.sort_values("rP").key.tolist() for m, g in U[U.in_P == 1].groupby("molecule")}
        Q["rrP"] = [rr(P_lists.get(m, []), t) for m, t in zip(Q.molecule, Q.truth)]
        Q["rrF"] = [rr(f, t) for f, t in zip(Q.f_top25, Q.truth)]
        Q["E_only_i"] = Q.in_E25 & ~Q.in_P25; Q["E_only_ii"] = Q.in_E25 & ~Q.in_U1
        Q["n_added"] = Q.n_u2 - Q.molecule.map(U[(U.in_P == 1) | (U.in_B == 1)].groupby("molecule").size()).fillna(0)
        rc = json.load(open(os.path.join(V2, w, "receipt.json")))
        S.append(dict(world=w, timing=rc["timing"]))
        Q["world"] = w; out.append(Q)
    D = pd.concat(out, ignore_index=True)
    lines = []
    for nm, g in (("pi0.3 (4 worlds)", D[D.pi == 30]), ("pi0 (4 worlds)", D[D.pi == 0])):
        lines.append(f"{nm:18s} n {len(g)} | P {g.rrP.mean():.4f} F-world {g.rrF.mean():.4f} diff {g.rrF.mean() - g.rrP.mean():+.4f} | new rank-1 {int(((g.rrF == 1) & (g.rrP < 1)).sum())} "
                     f"lost rank-1 {int(((g.rrP == 1) & (g.rrF < 1)).sum())} | E-only (i) {int(g.E_only_i.sum())} (ii) {int(g.E_only_ii.sum())} | added cand / query {g.n_added.mean():.1f}")
        for c in ("C1", "C2", "C3"):
            h = g[g.wclass == c]
            if len(h): lines.append(f"    {c} n {len(h)}: P {h.rrP.mean():.4f} F {h.rrF.mean():.4f} diff {h.rrF.mean() - h.rrP.mean():+.4f}")
    print("\n".join(lines)); print("timing / max RSS per stage:", json.dumps(S)[:1500])
    return dict(lines=lines, timing=S)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True, choices=["2", "3"]); a = ap.parse_args()
    res = stage2() if a.stage == "2" else stage3()
    json.dump(res, open(os.path.join(ROOT, f"experiments/w135/x158_stage{a.stage}.json"), "w"), indent=1)
