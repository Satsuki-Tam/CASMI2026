"""093 reading (093_prereg_pe.md): V = e086_v7f_* main, V+E = its ea0.5w1, V+P = e093_v8w7a_* main, V+P+E = its ea0.5w1 (same gen_eval2pv, tables, queries).
Primary PE - P on 053 NP C2 (NP_H / NP_N equal within a fold, folds equal; = the 076/080 aggregate); next-stage condition: >= +0.005 and lower > 0 and
non-inferiority (L >= -0.01) of PE - P on 053 NP C1, panel C1 clean, G C1 (f1/f2). Also PE - E, the identity interaction I = PE - P - E + V, C2 rows with PE < P."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
TAGS = ["np053f1dev", "np053f2dev", "panel", "f1dev", "f2dev"]
PV, PP = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("e086_v7f_", "e093_v8w7a_")   # Spark rerun: e093s_v7a_ e093s_v8w7a_
def load(t):
    a = pd.read_csv(os.path.join(HERE, f"diag/{PV}{t}.csv")); b = pd.read_csv(os.path.join(HERE, f"diag/{PP}{t}.csv"))
    x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_v", "_p")); assert len(x) == len(a) == len(b), (t, len(a), len(b), len(x))
    x["molecule"] = x.molecule.astype(str)
    return pd.DataFrame(dict(set=x.set, view=x.view, molecule=x.molecule, V=x.main_v, VE=x["ea0.5w1_v"], VP=x.main_p, VPE=x["ea0.5w1_p"]))
D = {t: load(t) for t in TAGS}
def stat(frames, a, b):
    pts, bts = [], []
    for df, strata in frames:
        gs = [(df[df.set == s][b] - df[df.set == s][a]).values for s in strata] if strata else [(df[b] - df[a]).values]
        gs = [g for g in gs if len(g)]
        pts.append(np.mean([g.mean() for g in gs]))
        bts.append(np.array([np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in gs]) for _ in range(NB)]))
    return float(np.mean(pts)), np.percentile(np.mean(np.vstack(bts), axis=0), [2.5, 97.5])
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo >= -e else "undetermined")
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
c2 = lambda t: D[t][D[t].view == "c2"]; c1 = lambda t: D[t][D[t].view == "c1"]
NP053 = [(c2("np053f1dev"), ["NP_H", "NP_N"]), (c2("np053f2dev"), ["NP_H", "NP_N"])]
NP053C1 = [(c1("np053f1dev"), ["NP_H", "NP_N"]), (c1("np053f2dev"), ["NP_H", "NP_N"])]
PAN = [(c1("panel")[lambda d: d.molecule.isin(CLEAN)], None)]
G = [(c1(t)[lambda d: d.set == "G_tims_crosslib"], None) for t in ("f1dev", "f2dev")]
NPF = [(c2(t), ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")]
NPFC1 = [(c1(t), ["C_np_crosslib", "E_np_negonly", "F_np_uncovered"]) for t in ("f1dev", "f2dev")]
L = ["# 093 reading: V / V+P / V+E / V+P+E (v7f main, EA theta 0.5 w 1)", "", "| aggregate | P - V | E - V | PE - P (primary) | PE - E | PE - V |", "|---|---|---|---|---|---|"]
res = {}
for nm, fr in (("053 NP C2 (H,N) primary", NP053), ("053 NP C1", NP053C1), ("panel C1 clean", PAN), ("G C1 (f1,f2)", G), ("f1/f2 NP C2 C-F", NPF), ("f1/f2 NP C1 C/E/F", NPFC1)):
    r = {k: stat(fr, a, b) for k, (a, b) in dict(PV=("V", "VP"), EV=("V", "VE"), PEP=("VP", "VPE"), PEE=("VE", "VPE"), PEV=("V", "VPE")).items()}
    res[nm] = r; L.append(f"| {nm} | {fmt(*r['PV'])} | {fmt(*r['EV'])} | {fmt(*r['PEP'])} ({st(*r['PEP'][1])}) | {fmt(*r['PEE'])} | {fmt(*r['PEV'])} |")
p, ci = res["053 NP C2 (H,N) primary"]["PEP"]
ok = p >= 0.005 and ci[0] > 0 and all(res[k]["PEP"][1][0] >= -0.01 for k in ("053 NP C1", "panel C1 clean", "G C1 (f1,f2)"))
X = pd.concat([D[t].assign(tag=t) for t in TAGS]); X["I"] = X.VPE - X.VP - X.VE + X.V
neg = X[(X.view == "c2") & (X.VPE < X.VP - 1e-12)]
L += ["", f"- **next stage (new confirmation set): {'GO' if ok else 'NO'}** (PE - P primary {fmt(p, ci)})",
      f"- identity interaction I = PE - P - E + V: C2 mean {X[X.view == 'c2'].I.mean():+.4f}, C1 mean {X[X.view == 'c1'].I.mean():+.4f}",
      f"- C2 rows with PE < P (EA must not penalise a C2 truth on a fixed list): {len(neg)}"]
open(os.path.join(HERE, "diag/x093_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
