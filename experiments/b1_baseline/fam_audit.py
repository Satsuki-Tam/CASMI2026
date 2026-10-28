"""Evidence-family complementarity audit (descriptive; run only AFTER the registered 102 reading). For every development (set, view, molecule):
the truth's rank inside the view list (the evaluator's view_frame) under single evidences -- FPNet f.z, GLACIER, popularity, library similarity of the
view, the fixed rule S = z(fp) + 2 z(gl) + 0.5 pop -- next to the main list (v8w7a, rP from diag/r102_<tag>.csv) and the E-lite lists (r_rank_e1b /
r_rank_e1r). Per layer: MRR@25 of each list, Spearman correlation of log ranks with the main list (rows where both rank the truth), pair-oracle
MRR max(RR_main, RR_x), and the counts 'x has the truth at rank 1 while the main list does not' / the reverse. Literature: tools of one family have
truth-rank correlations 0.45-0.83, different families 0.03-0.3 (CASMI 2016/2017 recomputation, research_notes/CASMI 2026 順位融合と注釈伝播).
Usage: python -X utf8 fam_audit.py   (reads the same tags as x102_summary.py)"""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))


def zl(x):
    x = np.asarray(x, float); ok = np.isfinite(x)
    if ok.sum() < 2 or np.nanstd(x) == 0: return np.zeros(len(x))
    out = (x - np.nanmean(x)) / np.nanstd(x); out[~ok] = np.nanmin(out[ok]); return out


def trank(score, tr, tie=None):
    """rank (1 = best) of the best-ranked truth row under score desc, ties broken by `tie` desc then row order; 0 if no truth row."""
    if not tr.any(): return 0
    s = np.nan_to_num(np.asarray(score, float), nan=-1e18); t2 = np.zeros(len(s)) if tie is None else np.nan_to_num(np.asarray(tie, float), nan=-1e18)
    order = np.lexsort((np.arange(len(s)), -t2, -s)); pos = np.empty(len(s), int); pos[order] = np.arange(1, len(s) + 1)
    return int(pos[tr].min())


rows = []
for tag, run in RUN_OF.items():
    rp = os.path.join(HERE, f"diag/r102_{tag}.csv")
    if not os.path.exists(rp): continue
    R = pd.read_csv(rp); R["molecule"] = R.molecule.astype(str); R = R.set_index(["set", "view", "molecule"])
    for f in sorted(os.listdir(os.path.join(HERE, run))):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(HERE, run, f)); F["molecule"] = F.molecule.astype(str)
        M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        pth = os.path.join(HERE, run, "work", f"gl_{s}.json")
        try: ok = json.load(open(pth + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        gl = json.load(open(pth)) if ok else {}
        for mid, g0 in F.groupby("molecule", sort=False):
            for view in ("c2", "c1"):
                if view == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]
                if (s, view, mid) not in R.index: continue
                r = R.loc[(s, view, mid)]; tr = g.is_truth.values.astype(bool)
                fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{view}"].values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                S = zl(fp) + 2 * zl(glv) + 0.5 * pop
                rows.append(dict(tag=tag, set=s, view=view, molecule=mid, n=len(g), rP=int(np.nan_to_num(r.rP)), r_e1b=int(np.nan_to_num(r.r_rank_e1b)), r_e1r=int(np.nan_to_num(r.r_rank_e1r)),
                                 r_fp=trank(fp, tr), r_gl=trank(glv, tr, fp) if np.isfinite(glv).any() else 0, r_pop=trank(pop, tr, fp), r_lib=trank(lib, tr, fp), r_S=trank(S, tr, fp)))
A = pd.DataFrame(rows); A.to_csv(os.path.join(HERE, "diag/fam_audit.csv"), index=False)
rr = lambda r: np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
LAY = {"A 053 NP C2 (H/N)": lambda d: d.tag.str.startswith("np053") & (d.view == "c2") & d.set.isin(["NP_H", "NP_N"]),
       "B_D f1/f2 D C2": lambda d: d.tag.isin(["f1dev", "f2dev"]) & (d.view == "c2") & (d.set == "D_np_single"),
       "old B f1/f2 NP C2": lambda d: d.tag.isin(["f1dev", "f2dev"]) & (d.view == "c2") & d.set.isin(NP),
       "G C1": lambda d: d.tag.isin(["f1dev", "f2dev"]) & (d.view == "c1") & (d.set == "G_tims_crosslib"),
       "panel C1 clean": lambda d: (d.tag == "panel") & (d.view == "c1") & d.molecule.isin(CLEAN),
       "panel C2": lambda d: (d.tag == "panel") & (d.view == "c2")}
L = ["# evidence-family complementarity audit (descriptive; truth rank inside the view list)", "",
     "| layer | n | list | MRR@25 | Spearman log-rank vs main | pair-oracle MRR | x rank-1 & main not | main rank-1 & x not |", "|---|---:|---|---:|---:|---:|---:|---:|"]
for lab, f in LAY.items():
    d = A[f(A)]
    if not len(d): continue
    for c in ("rP", "r_e1b", "r_e1r", "r_S", "r_fp", "r_gl", "r_pop", "r_lib"):
        both = d[(d.rP > 0) & (d[c] > 0)]
        rho = float(pd.Series(np.log(both.rP.values)).corr(pd.Series(np.log(both[c].values)), method="spearman")) if len(both) > 5 and c != "rP" else float("nan")
        L.append(f"| {lab} | {len(d)} | {c} | {rr(d[c].values).mean():.4f} | {rho:.3f} | {np.maximum(rr(d.rP.values), rr(d[c].values)).mean():.4f} | {int(((d[c] == 1) & (d.rP != 1)).sum())} | {int(((d.rP == 1) & (d[c] != 1)).sum())} |")
open(os.path.join(HERE, "diag/fam_audit.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
