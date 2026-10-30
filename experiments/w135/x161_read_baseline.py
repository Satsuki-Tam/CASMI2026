"""161: descriptive reading of the v2 FH-PEB baseline on the DEVELOPMENT units (160 decision; never e). Read-only on the workspace: imports
src/aux_reader.py (verified predictions, P / F / PE references) and src/metrics.py. The registered gate numbers come from aux_reader itself;
this script adds, on the SAME population S for every number (Codex 160):
  headroom_U2(S) = mean 1[truth in U2] - mean RR(F), split into g1 truth in F's top 25 / g2 truth in U2 but not in F's top 25 / g3 truth not in U2,
  with the mean RR of F and of the experiment inside each group;
  the counterfactual 'experiment restricted to the PE eligibility' (slots with in_P or in_E25 kept, the rest not submitted; same model, descriptive);
  rank-1 changes vs F, and how often the experiment puts a B-only product (not in_P, not in_E25) at rank 1 and how often that product is the truth.
Usage: python -X utf8 experiments/w135/x161_read_baseline.py --ws C:/kaggle/competitions/casmi-harness-v2 --exp baseline-11 [--pe]"""
import argparse, glob, importlib.util, json, os, sys
import numpy as np, pandas as pd


def top_order(s, valid):
    v = np.flatnonzero(valid & (s > -1e8)); return v[np.lexsort((v, -s[v]))][:25]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ws", required=True); ap.add_argument("--exp", default="baseline-11"); ap.add_argument("--pe", action="store_true"); a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.ws, "src"))
    spec = importlib.util.spec_from_file_location("aux_x161", os.path.join(a.ws, "src", "aux_reader.py")); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
    with np.load(os.path.join(a.ws, "data/folds/validation.npz"), allow_pickle=False) as Z: V = {k: Z[k] for k in Z.files}
    meta = {k[6:]: v for k, v in V.items() if k.startswith("meta__")}
    y, keys, valid = V["y"], V["meta__cand_keys"], V["meta__cand_valid"]; N = len(y)
    pos = {u: i for i, u in enumerate(V["ids"])}
    # PE eligibility per slot from the pinned development tables
    pe = np.zeros_like(valid); bonly = np.zeros_like(valid)
    for pu in glob.glob(os.path.join(a.ws, "data/raw/w135_u2_dev_v1", "U_*.parquet")):
        U = pd.read_parquet(pu, columns=["uid", "key", "in_P", "in_E25"])
        for u, g in U.groupby("uid"):
            i = pos[u]; ks = list(keys[i]); el = dict(zip(g.key.astype(str), ((g.in_P == 1) | (g.in_E25 == 1)).values))
            for j, k in enumerate(ks):
                if valid[i, j] and k in el: pe[i, j] = el[k]; bonly[i, j] = not el[k]
    preds = {"F": R.predictions_of("F", V), "P": R.predictions_of("P", V), a.exp: R.predictions_of(a.exp, V)}
    if a.pe: preds["PE"] = R.predictions_of("PE", V)
    cf = preds[a.exp].copy(); cf[~pe] = -1e9; preds[a.exp + "|PE-only"] = cf
    rr = {k: R.reciprocal_ranks(y, p, meta) for k, p in preds.items()}
    inU2 = np.array([bool((valid[i] & (keys[i] == y[i])).any()) for i in range(N)])
    top = {k: [top_order(p[i], valid[i]) for i in range(N)] for k, p in preds.items()}
    inF25 = np.array([y[i] in set(keys[i][top["F"][i]]) for i in range(N)])
    first = {k: np.array([t[0] if len(t) else -1 for t in v]) for k, v in top.items()}
    prim = V["meta__primary"].astype(bool); pi = V["meta__pi"]; wc = V["meta__wclass"]
    pops = [("PRIMARY pi0.3 F/R", prim), ("pi0 all", pi == 0), ("pi0.6", pi == 60)] + [(f"pi0.3 {c}", prim & (wc == c)) for c in ("C1", "C2", "C3")]
    out = dict(experiment=a.exp, populations=[])
    for name, m in pops:
        g1 = m & inF25; g2 = m & inU2 & ~inF25; g3 = m & ~inU2
        row = dict(population=name, n=int(m.sum()), reach_U2=float(inU2[m].mean()), mrr={k: float(v[m].mean()) for k, v in rr.items()},
                   headroom_vs_F=float(inU2[m].mean() - rr["F"][m].mean()),
                   groups={gn: dict(n=int(g.sum()), **{k: float(rr[k][g].mean()) if g.any() else None for k in rr}) for gn, g in (("g1_truth_in_F25", g1), ("g2_in_U2_not_F25", g2), ("g3_not_in_U2", g3))})
        e1 = first[a.exp][m]; f1 = first["F"][m]; idx = np.flatnonzero(m)
        hitE = rr[a.exp][m] == 1.0; hitF = rr["F"][m] == 1.0
        b1 = np.array([e >= 0 and bonly[i, e] for i, e in zip(idx, e1)])
        row.update(new_rank1_vs_F=int((hitE & ~hitF).sum()), lost_rank1_vs_F=int((~hitE & hitF).sum()),
                   b_only_at_rank1=int(b1.sum()), b_only_at_rank1_truth=int((b1 & hitE).sum()))
        out["populations"].append(row)
        print(f"{name:20s} n {row['n']:5d} reach {row['reach_U2']:.4f} | " + " ".join(f"{k} {v:.4f}" for k, v in row["mrr"].items()) +
              f" | headroom vs F {row['headroom_vs_F']:.4f} | rank-1 new {row['new_rank1_vs_F']} lost {row['lost_rank1_vs_F']} | B-only at 1: {row['b_only_at_rank1']} (truth {row['b_only_at_rank1_truth']})")
        for gn, gd in row["groups"].items():
            print(f"    {gn:18s} n {gd['n']:5d} " + " ".join(f"{k} {gd[k]:.4f}" for k in rr if gd[k] is not None))
    od = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x161"); os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, f"read_{a.exp}.json"), "w"), indent=1); print("saved", os.path.join(od, f"read_{a.exp}.json"))


if __name__ == "__main__":
    main()
