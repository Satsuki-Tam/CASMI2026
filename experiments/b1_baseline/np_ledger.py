"""Loss ledger of the registered main output on unseen class-2 / class-1 type molecules (where is the MRR lost, and which single signal
would have ranked the truth first). Reads a run's tables + GLACIER output and the main-output RR per molecule from a gen_eval2 CSV.
Usage: python -X utf8 np_ledger.py --run run_f1dev --sets C_np_crosslib D_np_single ... --rr diag/px050_f1dev_base.csv --out diag/ledger_f1dev
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--rr", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--views", default="c1,c2"); a = ap.parse_args()
RR = pd.read_csv(os.path.join(HERE, a.rr)); RR["molecule"] = RR.molecule.astype(str); RRd = {(r.set, r.view, r.molecule): float(r.main) for r in RR.itertuples(index=False)}
def rank_of(v, i):
    v = np.asarray(v, float); x = v[i]
    if not np.isfinite(x): return np.nan
    return 1 + int(np.sum(np.where(np.isfinite(v), v, -np.inf) > x))
def zz(x):
    x = np.asarray(x, float); ok = np.isfinite(x); o = np.full(len(x), np.nan)
    if ok.sum() >= 2 and x[ok].std() > 0: o[ok] = (x[ok] - x[ok].mean()) / x[ok].std()
    elif ok.any(): o[ok] = 0.0
    o[~ok] = np.nanmin(o) if np.isfinite(o).any() else 0.0
    return o
rows = []
for s in a.sets:
    F = pd.read_parquet(os.path.join(HERE, a.run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
    M = pd.read_csv(os.path.join(HERE, a.run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    gl, _, _ = E.runner(os.path.join(HERE, a.run), s, "gl"); gl = gl or {}
    for mid in M.index:
        for v in a.views.split(","):
            if v == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
            key = (s, v, mid)
            if key not in RRd: continue
            g = E.view_frame(F, M, mid, v); tr = g.is_truth.values.astype(bool) if len(g) else np.zeros(0, bool)
            rr = RRd[key]; d = dict(set=s, view=v, molecule=mid, rr=rr, main_rank=(round(1 / rr) if rr > 0 else np.nan), n_cand=len(g),
                                     truth_in_window=bool(M.loc[mid, "truth_in_window"]), reach_ext=bool(M.loc[mid, "reach_external_b1"]), truth_in_list=bool(tr.any()))
            if tr.any():
                i = int(np.flatnonzero(tr)[0])
                fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{v}"].values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                has_gl = np.isfinite(glv).sum() >= max(2, 0.5 * len(g))
                S = zz(fp) + (2 * zz(glv) if has_gl else 0) + 0.5 * pop
                d.update(has_gl=has_gl, r_fp=rank_of(fp, i), r_gl=(rank_of(glv, i) if has_gl else np.nan), r_pop=rank_of(pop, i), r_lib=rank_of(lib, i), r_S=rank_of(S, i),
                         r_fpgl=(rank_of(zz(fp) + zz(glv), i) if has_gl else np.nan),
                         t_coco=bool(g.in_coconut.values[i]), t_tier=bool(g.in_tier.values[i]), t_pop=float(pop[i]), t_lib=float(lib[i]), lib_max=float(np.nanmax(lib)),
                         t_np=float(g["np"].values[i]) if "np" in g.columns else np.nan, t_lotus=float(g.lotus_refs.values[i]) if "lotus_refs" in g.columns else np.nan,
                         n_same_mass=int(len(g)))
            rows.append(d)
R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
L = [f"# loss ledger: {a.run} ({', '.join(a.sets)})", "", "| set | view | n | MRR | not in list | rank 1 | 2-5 | 6-25 | >25 (in list) | top-1 by FP / GL / pop / lib / S / FP+GL (in list) | median rank FP / GL / S (in list) | truth COCONUT / tier-only |",
     "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
for (s, v), g in R.groupby(["set", "view"], sort=False):
    n = len(g); il = g[g.truth_in_list]; mr = g.main_rank
    t1 = lambda c: f"{(il[c] == 1).mean():.2f}" if c in il and il[c].notna().any() else "-"
    med = lambda c: f"{il[c].median():.0f}" if c in il and il[c].notna().any() else "-"
    L.append(f"| {s} | {v} | {n} | {g.rr.mean():.3f} | {(~g.truth_in_list).mean():.2f} | {(mr == 1).mean():.2f} | {((mr >= 2) & (mr <= 5)).mean():.2f} | {((mr >= 6) & (mr <= 25)).mean():.2f} | {(g.truth_in_list & mr.isna()).mean():.2f} | "
             f"{t1('r_fp')} / {t1('r_gl')} / {t1('r_pop')} / {t1('r_lib')} / {t1('r_S')} / {t1('r_fpgl')} | {med('r_fp')} / {med('r_gl')} / {med('r_S')} | "
             f"{(il.t_coco.mean() if len(il) else 0):.2f} / {((il.t_tier & ~il.t_coco).mean() if len(il) else 0):.2f} |")
open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
