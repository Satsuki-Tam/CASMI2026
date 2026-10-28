"""106 GL-summary pilot, step 3 (exploratory; written before the detail run). Inputs: diag/glpilot106/detail_<tag>_<set>.csv (gl_runner_detail.py),
diag/glpilot106/subset.csv, the run tables + GL JSON (reproduction), diag/top102_<tag>.parquet (main top 25 with scores), diag/r102_<tag>.csv (main RR).
Fixed before the run:
  per candidate over its covered spectra with a prediction: gl_mean = mean sim (must reproduce gl_ex_mean of the run's GL JSON, |diff| <= 1e-6, else STOP),
  net = mean(expl_obs) - mean(unexpl_pred) (explained observed weight minus unexplained predicted weight, paired as Codex 106 asked), n_spec.
  (1) GL-alone discrimination inside the view list (view_frame): rank by gl_mean vs by GL2 = z(gl_mean) + z(net) (equal weights; candidates without a
      prediction last, ties by official key). MRR@25, rescue / loss counts.
  (2) connection to the main list: re-rank the main top 25 by z(main score) + 0.5 z(net) (z inside the top 25; missing net -> 0) vs the main order.
Views: C2 rows of NP_H / NP_N / C / D (GL-covered queries only matter), C1 rows of G and panel. Paired bootstrap (rows), 4,000 replicates, seed 106.
Usage: python -X utf8 x106_glpilot.py"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, "diag", "glpilot106"); NB = 4000
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
SUB = pd.read_csv(os.path.join(P, "subset.csv")); SUB["molecule"] = SUB.molecule.astype(str)


def zl(x):
    x = np.asarray(x, float); ok = np.isfinite(x)
    if ok.sum() < 2 or np.nanstd(x[ok]) == 0: return np.where(ok, 0.0, np.nan)
    return (x - np.nanmean(x[ok])) / np.nanstd(x[ok])


def trank(score, tr, keys):
    if not tr.any(): return 0
    s = np.where(np.isfinite(score), score, -np.inf); o = np.lexsort((np.asarray(keys), -s)); pos = np.empty(len(s), int); pos[o] = np.arange(1, len(s) + 1)
    return int(pos[tr].min())


rr = lambda r: (1.0 / r) if 1 <= r <= 25 else 0.0
rows = []; NOISE = []
for (tag, s), sub in SUB.groupby(["tag", "set"]):
    run = os.path.join(HERE, RUN_OF[tag]); dp = os.path.join(P, f"detail_{tag}_{s}.csv")
    if not os.path.exists(dp): sys.exit(f"STOP: missing {dp}")
    Dd = pd.read_csv(dp); Dd["mid"] = Dd.mid.astype(str)
    agg = Dd.groupby(["mid", "smiles"]).agg(gl_mean=("sim", "mean"), expl=("expl_obs", "mean"), unexpl=("unexpl_pred", "mean"), n_spec=("sim", "size")).reset_index()
    agg["net"] = agg.expl - agg.unexpl
    # amended before any result (17:12): the detail must reproduce THIS rerun's gl_ex_mean exactly; the stored run differs by GLACIER batch-composition noise
    rer = json.load(open(os.path.join(P, f"out_{tag}_{s}.json"))); gl = json.load(open(os.path.join(run, "work", f"gl_{s}.json")))
    chk = [abs(float(rer[m][sm]) - g) for m, sm, g in zip(agg.mid, agg.smiles, agg.gl_mean) if (rer.get(m) or {}).get(sm) is not None]
    if len(agg) and (not chk or max(chk) > 1e-9): sys.exit(f"STOP: detail mean does not reproduce this rerun for {tag} {s} (max diff {max(chk) if chk else 'n/a'})")
    st = np.array([abs(float(gl[m][sm]) - g) for m, sm, g in zip(agg.mid, agg.smiles, agg.gl_mean) if (gl.get(m) or {}).get(sm) is not None])
    NOISE.append(f"| {tag} {s} | {len(st)} | {(st > 1e-6).mean():.3f} | {np.percentile(st, 99):.5f} | {st.max():.5f} |" if len(st) else f"| {tag} {s} | 0 (no covered spectrum) | - | - | - |")
    A = {(m, sm): (g, n) for m, sm, g, n in zip(agg.mid, agg.smiles, agg.gl_mean, agg.net)}
    F = pd.read_parquet(os.path.join(run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
    M = pd.read_csv(os.path.join(run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    TP = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); TP["molecule"] = TP.molecule.astype(str)
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R = R.set_index(["set", "view", "molecule"])
    for mid in sub.molecule:
        g0 = F[F.molecule == mid]
        for view in ("c2", "c1"):
            if view == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
            keep = g0[f"in_short_{view}"].values.astype(bool)
            if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
            g = g0[keep]; tr = g.is_truth.values.astype(bool); keys = g.official_key.astype(str).values
            gm = np.array([A.get((mid, sm), (np.nan, np.nan))[0] for sm in g.smiles], float); nt = np.array([A.get((mid, sm), (np.nan, np.nan))[1] for sm in g.smiles], float)
            gl2 = zl(gm) + np.nan_to_num(zl(nt), nan=0.0); gl2 = np.where(np.isfinite(gm), gl2, np.nan)
            main = float(R.loc[(s, view, mid), "main"]) if (s, view, mid) in R.index else 0.0
            tp = TP[(TP.set == s) & (TP.view == view) & (TP.molecule == mid)].sort_values("rank")
            if len(tp):
                smap = dict(zip(g.smiles.astype(str), nt)); ntp = np.array([smap.get(str(x), np.nan) for x in tp.smiles], float)
                sc = zl(tp.score.values.astype(float)) + 0.5 * np.nan_to_num(zl(ntp), nan=0.0)
                o = np.lexsort((tp["rank"].values, -sc)); truth_pos = [k for k, i in enumerate(o) if bool(tp.is_truth.values[i])]
                conn = 1.0 / (truth_pos[0] + 1) if truth_pos else 0.0
            else: conn = main
            rows.append(dict(tag=tag, set=s, view=view, molecule=mid, covered=bool(np.isfinite(gm).any()), main=main, conn=conn,
                             gl_mean=rr(trank(gm, tr, keys)) if np.isfinite(gm).any() else 0.0, gl2=rr(trank(gl2, tr, keys)) if np.isfinite(gm).any() else 0.0))
X = pd.DataFrame(rows); X.to_csv(os.path.join(P, "x106_rows.csv"), index=False)
rng = np.random.default_rng(106)
def ci(d):
    d = np.asarray(d, float); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(NB)]; return f"{d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}]"
LAY = {"C2 NP_H/NP_N (053)": (X.view == "c2") & X.set.isin(["NP_H", "NP_N"]), "C2 C/D (f1/f2)": (X.view == "c2") & X.set.isin(["C_np_crosslib", "D_np_single"]),
       "C1 G (f1/f2)": (X.view == "c1") & (X.set == "G_tims_crosslib"), "C1 panel": (X.view == "c1") & (X.set == "P_np250")}
L = ["# 106 GL-summary pilot (exploratory; fixed before the run)", "", "| layer | rows (GL covered) | GL-alone gl_mean | GL-alone GL2 | GL2 - gl_mean | rescued / lost | main | main+0.5 z(net) - main | rescued / lost |", "|---|---|---:|---:|---|---|---:|---|---|"]
for lab, m in LAY.items():
    d = X[m]; c = d[d.covered]
    if not len(d): continue
    dg = c.gl2 - c.gl_mean; dc = d.conn - d.main
    L.append(f"| {lab} | {len(d)} ({len(c)}) | {c.gl_mean.mean():.4f} | {c.gl2.mean():.4f} | {ci(dg) if len(c) else '-'} | {int((dg > 1e-12).sum())} / {int((dg < -1e-12).sum())} | {d.main.mean():.4f} | {ci(dc)} | {int((dc > 1e-12).sum())} / {int((dc < -1e-12).sum())} |")
L += ["", "GLACIER rerun vs the stored GL JSON (batch-composition noise; the detail reproduces the rerun exactly):", "", "| input | candidates | share diff > 1e-6 | p99 | max |", "|---|---:|---:|---:|---:|"] + NOISE
open(os.path.join(P, "x106_glpilot.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
