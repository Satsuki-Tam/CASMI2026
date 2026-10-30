"""146 exploratory (Codex 146 Q4 (b); NOT a registration, nothing here selects F or its constants): where does the fusion's gain and cost come from?
Same groups, P lists, E2 model and tables as e2_eval_v3 (reader v3). Lists (alpha 0.5, K 10 as F):
  Fpe  = RRF(P, pe)                        source re-weighting alone (pe = P's own order restricted to the view's E window)
  Fc1  = RRF(P, E2 order restricted to P's top-25 E-window candidates)   E2's ordering on the common candidates, same candidates as Fpe
  Fc2  = RRF(P, E2 full-window ranks, candidates = P top 25 only)        + the full-window rank scale
  F    = registered fusion (candidates P top 25 | E2 top 25)            + E2-only candidates
  Fpp  = position-preserving F: the positions that E-window candidates hold in P's top 25 are refilled by the E-window candidates (P's E-window
         candidates and E2-only candidates) in F order; every non-E candidate keeps its P position (no slot moves across the source boundary)
  Fpp1 = Fpp but E2-only candidates may not enter (common candidates re-ordered inside the E slots only)
Strata: C2 A + old B split by fixed membership (E-source / E-outside), B_D, the C1 layers. Molecule-level paired means and bootstrap 95% CI.
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/x146_slot_decomp.py"""
import os, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(1, os.path.join(ROOT, "experiments", "b1_baseline"))
from e2_common import FEATS, view_frame, rank_lists
from e2_engine import fuse_rrf
import e2_eval_v3 as R3


def pos_preserve(p, e_window, fused, allow_new=True):
    slots = [i for i, k in enumerate(p) if k in e_window]
    pool = [k for k in fused if (k in e_window) and (allow_new or k in p)]
    out = list(p)
    for i, k in zip(slots, pool): out[i] = k
    return out[:25]


def main():
    t0 = time.time(); m = lgb.Booster(model_file=os.path.join(ROOT, "experiments/e2/model_v1/e2_lgb.txt")); B = os.path.join(ROOT, "experiments/b1_baseline")
    G = pd.read_csv(os.path.join(ROOT, "experiments/e2/eval_v3/e2_eval_groups.csv")); G["molecule"] = G.molecule.astype(str)
    meta = {(r.tag, r.set, r.view, r.molecule): r for r in G.itertuples(index=False)}
    rows = []
    for tag, (d, csv, sets, run) in R3.TAGS.items():
        T = pd.read_parquet(os.path.join(B, "diag", f"top102_{tag}.parquet")); T["molecule"] = T.molecule.astype(str)
        ev = pd.read_csv(os.path.join(B, d, csv)); ev["molecule"] = ev.molecule.astype(str); truth = dict(zip(ev.molecule, ev.scorer_key.astype(str)))
        for s in sets:
            E = pd.read_parquet(os.path.join(ROOT, "experiments/e2/ewin", d, f"ewin_{s}.parquet")); F = pd.read_parquet(os.path.join(ROOT, "experiments/e2/ewin", d, f"e2f_{s}.parquet"))
            E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str)
            for v in ("c1", "c2"):
                X = view_frame(E, F, v); Rk = rank_lists(X, m.predict(X[FEATS])) if len(X) else X
                EL = {g: grp.official_key.astype(str).tolist() for g, grp in Rk.groupby("molecule", sort=False)} if len(Rk) else {}
                for x, g in T[(T.set == s) & (T.view == v)].groupby("molecule", sort=False):
                    key = (tag, s, v, x)
                    if key not in meta: continue
                    p = g.sort_values("rank").okey.astype(str).tolist()[:25]; el = EL.get(x, []); er = {k: i + 1 for i, k in enumerate(el)}; ew = set(el); t = truth[x]
                    pe = [k for k in p if k in ew]; per = {k: i + 1 for i, k in enumerate(pe)}
                    com = [k for k in el if k in set(p)]; cr = {k: i + 1 for i, k in enumerate(com)}
                    Ff = fuse_rrf(p, er, el[:25], 0.5)
                    L = dict(P=p, Fpe=fuse_rrf(p, per, pe, 0.5), Fc1=fuse_rrf(p, cr, [], 0.5),
                             Fc2=fuse_rrf(p, er, [], 0.5), F=Ff, Fpp=pos_preserve(p, ew, Ff, True), Fpp1=pos_preserve(p, ew, Ff, False))
                    r_ = meta[key]
                    rows.append(dict(tag=tag, set=s, view=v, molecule=x, t_esrc=bool(r_.t_esrc), panel_clean=bool(r_.panel_clean), **{k: R3.rr(l, t) for k, l in L.items()}))
            print(f"  {tag} {s} ({time.time()-t0:.0f}s)", flush=True)
    D = pd.DataFrame(rows); D.to_csv(os.path.join(ROOT, "experiments/e2/x146_slot_decomp.csv"), index=False)
    CA = R3.CELLS_A; CB = R3.CELLS_B; CBD = R3.CELLS_BD; sel = lambda cells, vw: D[(D.view == vw) & D[["tag", "set"]].apply(tuple, axis=1).isin(cells)]
    LAY = [("C2 A + old B, E-source", sel(CA + CB, "c2").query("t_esrc")), ("C2 A + old B, E-outside", sel(CA + CB, "c2").query("not t_esrc")), ("C2 A (053 NP)", sel(CA, "c2")),
           ("C2 B_D", sel(CBD, "c2")), ("C1 G", sel([("f1dev", "G_tims_crosslib"), ("f2dev", "G_tims_crosslib")], "c1")), ("C1 053 NP", sel(CA, "c1")),
           ("C1 f1/f2 NP", sel(CB, "c1")), ("C1 panel clean", D[(D.tag == "panel") & (D.view == "c1") & D.panel_clean])]
    rng = np.random.default_rng(146)
    def ci(x):
        x = np.asarray(x, float); b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(2000)]; return f"{x.mean():+.4f} [{np.percentile(b, 2.5):+.4f}, {np.percentile(b, 97.5):+.4f}]"
    out = ["# 146 exploratory: fusion gain / cost decomposition (not a registration)", "", "| layer | n | P | Fpe - P | Fc1 - Fpe (E2 order, common) | Fc2 - Fc1 (full-window ranks) | F - Fc2 (E2-only candidates) | F - P | Fpp - P (position-preserving) | Fpp1 - P |", "|---|---:|---:|---|---|---|---|---|---|---|"]
    for lab, Z in LAY:
        if not len(Z): continue
        out.append(f"| {lab} | {len(Z)} | {Z.P.mean():.4f} | {ci(Z.Fpe - Z.P)} | {ci(Z.Fc1 - Z.Fpe)} | {ci(Z.Fc2 - Z.Fc1)} | {ci(Z.F - Z.Fc2)} | {ci(Z.F - Z.P)} | {ci(Z.Fpp - Z.P)} | {ci(Z.Fpp1 - Z.P)} |")
    open(os.path.join(ROOT, "experiments/e2/x146_slot_decomp.md"), "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out)); print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
