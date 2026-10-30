"""143/144 E2 step 4: development evaluation of E2 alone and of its fusion with P (v8w7a main order, top 25 per (set, view, molecule):
experiments/b1_baseline/diag/top102_<tag>.parquet, gen_eval2fd --dump_top), registered in reports/agent_review/144_prereg_e2.md before
any E2 number was read. Paired: exactly P's (set, view, molecule) groups; E2 = e2_lgb.txt on the view window of the same molecule.
Lists (fixed constants): P; E2 (E window only); rrf_w (w in 0.5, 1): candidates = P top 25 | E2 top 25, s = 1/(10 + r_P) + w/(10 + r_E)
(r_E = E2 rank in the whole view window, missing terms 0; ties -> P rank, E2 rank, key); hedge = P with E2's top 1 put at position 2 when it
is not in P's top 2; rrf_w_h = the same insertion on rrf_w. Strata: T = C1 groups (G_tims_crosslib and panel C1 non-clean excluded);
B = C2 groups whose truth is a COCONUT structure (E table flag; absent from the E table -> not COCONUT); R = the other C2 groups
(G excluded). Projection PD = 0.148 r_T + 0.220 r_B + 0.026 r_R, r_g = sum RR(list) / sum RR(P) - 1 over the pooled groups of g;
95% interval by resampling molecules inside each (tag, set, view) cell (2000 draws, seed 144).
Outputs: <out>/e2_eval_groups.csv (one row per group: RR of every list, stratum, E2 diagnostics), <out>/e2_eval_summary.md / .json."""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
from e2_common import FEATS, view_frame, rank_lists
S5 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]; S3 = ["NP_H", "NP_X", "NP_N"]
TAGS = {"np053f1dev": ("np053_f1dev", "p2_molecules.csv", S3), "np053f2dev": ("np053_f2dev", "p2_molecules.csv", S3),
        "f1dev": ("eval_set_f1", "p2_molecules.csv", S5), "f2dev": ("eval_set_f2", "p2_molecules.csv", S5), "panel": ("panel_np250", "p1_molecules.csv", ["P_np250"])}
LISTS = ["P", "E2", "rrf0.5", "rrf1", "hedge", "rrf0.5_h", "rrf1_h"]
W = dict(T=0.148, B=0.220, R=0.026); K = 10.0


def rrf(p, e_rank, e_top, w):
    pr = {k: i + 1 for i, k in enumerate(p)}; cand = list(dict.fromkeys(list(p) + list(e_top)))
    s = lambda k: (1.0 / (K + pr[k]) if k in pr else 0.0) + (w / (K + e_rank[k]) if k in e_rank else 0.0)
    return sorted(cand, key=lambda k: (-s(k), pr.get(k, 99), e_rank.get(k, 1e9), k))[:25]


def hedge(L, e1):
    if e1 is None or e1 in L[:2] or not L: return L[:25]
    return ([L[0], e1] + [k for k in L[1:] if k != e1])[:25]


def rr(L, t):
    L = L[:25]; return 1.0 / (L.index(t) + 1) if t in L else 0.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ewin", default="experiments/e2/ewin"); ap.add_argument("--top", default="experiments/b1_baseline/diag"); ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(); P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p); out = P_(a.out); os.makedirs(out, exist_ok=True); t0 = time.time()
    m = lgb.Booster(model_file=P_(a.model)); assert m.feature_name() == FEATS, "STOP: model features differ from e2_common.FEATS"
    clean = set(pd.read_csv(P_("experiments/fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
    rows = []
    for tag, (d, csv, sets) in TAGS.items():
        T = pd.read_parquet(f"{P_(a.top)}/top102_{tag}.parquet"); T["molecule"] = T.molecule.astype(str)
        ev = pd.read_csv(P_(f"experiments/b1_baseline/{d}/{csv}")); truth = dict(zip(ev.molecule.astype(str), ev.scorer_key.astype(str)))
        for s in sets:
            E = pd.read_parquet(P_(f"{a.ewin}/{d}/ewin_{s}.parquet")); F = pd.read_parquet(P_(f"{a.ewin}/{d}/e2f_{s}.parquet"))
            E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str)
            coco = {(r.molecule, r.official_key) for r in E[E.in_coconut].itertuples(index=False)}
            for v in ("c1", "c2"):
                Pv = T[(T.set == s) & (T.view == v)].sort_values(["molecule", "rank"])
                if not len(Pv): continue
                X = view_frame(E, F, v); R = rank_lists(X, m.predict(X[FEATS])) if len(X) else X
                EL = {g: grp.official_key.astype(str).tolist() for g, grp in R.groupby("molecule", sort=False)} if len(R) else {}
                for mid, grp in Pv.groupby("molecule", sort=False):
                    t = truth[mid]; p = grp.okey.astype(str).tolist()[:25]; el = EL.get(mid, []); er = {k: i + 1 for i, k in enumerate(el)}; e1 = el[0] if el else None
                    L = dict(P=p, E2=el[:25]); L["rrf0.5"] = rrf(p, er, el[:25], 0.5); L["rrf1"] = rrf(p, er, el[:25], 1.0)
                    L["hedge"] = hedge(p, e1); L["rrf0.5_h"] = hedge(L["rrf0.5"], e1); L["rrf1_h"] = hedge(L["rrf1"], e1)
                    if s == "G_tims_crosslib" or (tag == "panel" and v == "c1" and mid not in clean): st = "X"
                    elif v == "c1": st = "T"
                    else: st = "B" if (mid, t) in coco else "R"
                    rows.append(dict(tag=tag, set=s, view=v, molecule=mid, stratum=st, truth_in_e=t in er, e2_truth_rank=er.get(t, np.nan), n_e=len(el),
                                     p_truth_rank=(p.index(t) + 1) if t in p else np.nan, **{f"rr_{l}": rr(L[l], t) for l in LISTS}))
            print(f"  {tag} {s} ({time.time()-t0:.0f}s)", flush=True)
    G = pd.DataFrame(rows); G.to_csv(f"{out}/e2_eval_groups.csv", index=False)
    cells = [g for _, g in G.groupby(["tag", "set", "view"])]; rng = np.random.default_rng(144)

    def proj(D):
        o = {}
        for l in LISTS:
            r = {st: D.loc[D.stratum == st, f"rr_{l}"].sum() / max(D.loc[D.stratum == st, "rr_P"].sum(), 1e-12) - 1.0 for st in W}
            o[l] = dict(PD=sum(W[st] * r[st] for st in W), **{f"r_{st}": r[st] for st in W})
        return o
    point = proj(G); boots = []
    for _ in range(a.boot):
        D = pd.concat([c.iloc[rng.integers(0, len(c), len(c))] for c in cells], ignore_index=True); boots.append(proj(D))
    summ = {}
    for l in LISTS:
        summ[l] = {k: dict(point=point[l][k], lo=float(np.percentile([b[l][k] for b in boots], 2.5)), hi=float(np.percentile([b[l][k] for b in boots], 97.5))) for k in point[l]}
    agg = dict(n=("molecule", "size"), truth_in_e=("truth_in_e", "mean"), **{l: (f"rr_{l}", "mean") for l in LISTS})
    cellt = G.groupby(["tag", "set", "view", "stratum"]).agg(**agg).reset_index(); strt = G.groupby("stratum").agg(**agg).reset_index()
    G2 = G.assign(p_ok=G.rr_P == 1, e_ok=G.rr_E2 == 1)
    comp = G2.groupby("stratum").apply(lambda x: pd.Series(dict(both=int((x.p_ok & x.e_ok).sum()), p_only=int((x.p_ok & ~x.e_ok).sum()), e_only=int((~x.p_ok & x.e_ok).sum()),
                                                                neither=int((~x.p_ok & ~x.e_ok).sum())))).reset_index()
    with open(f"{out}/e2_eval_summary.md", "w", encoding="utf-8") as f:
        f.write(f"# 144 E2 development evaluation ({time.strftime('%Y-%m-%d %H:%M')}; model {a.model})\n\n")
        f.write("## Projection PD (0.148 r_T + 0.220 r_B + 0.026 r_R)\n\n| list | PD [95%] | r_T | r_B | r_R |\n|---|---|---|---|---|\n")
        for l in LISTS:
            s_ = summ[l]; cols = [f"{s_['r_' + st]['point']:+.3f} [{s_['r_' + st]['lo']:+.3f}, {s_['r_' + st]['hi']:+.3f}]" for st in W]
            f.write(f"| {l} | {s_['PD']['point']:+.4f} [{s_['PD']['lo']:+.4f}, {s_['PD']['hi']:+.4f}] | " + " | ".join(cols) + " |\n")
        f.write("\n## Strata (mean RR)\n\n" + strt.round(4).to_markdown(index=False) + "\n\n## Rank-1 complementarity (P right / E2 right)\n\n" + comp.to_markdown(index=False))
        f.write("\n\n## Cells (mean RR)\n\n" + cellt.round(4).to_markdown(index=False) + "\n")
    json.dump(dict(summary=summ, n=len(G), seconds=round(time.time() - t0)), open(f"{out}/e2_eval_summary.json", "w"), indent=1)
    print(open(f"{out}/e2_eval_summary.md", encoding="utf-8").read()); print("E2_EVAL_DONE")


if __name__ == "__main__":
    main()
