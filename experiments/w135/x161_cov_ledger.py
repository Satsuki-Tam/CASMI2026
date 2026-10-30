"""161 decision (Codex 161 Q5): drop-stage ledger of the development C1 / C2 truths that are in neither U2 nor the E window (dev only; e refused).
Per query, from the saved B1 world tables: b1_molecules (truth_in_window / truth_in_shortlist / truth_in_short_c2, window and shortlist sizes),
the full-window official keys (gen/gen_<b>_window_okeys.parquet) and the candidate table b1_features (is_truth rows: in_short_c2 and the view's
source eligibility in_tier | in_coconut | in_train_c2). Stage of loss:
  S0 not in the B1 window (neither the raw flag nor the window's official keys);  S1 in the window, not in the shortlist;
  S2 in the shortlist but not in P's view (in_short_c2 and source-eligible);      S3 in P's view but not in P's top 25 (should be empty: rP = 0).
Descriptive. Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x161_cov_ledger.py"""
import json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FH2 = os.path.join(ROOT, "experiments/w135/fh2_1"); V2 = os.path.join(ROOT, "experiments/w135/v2_1"); WD = os.path.join(ROOT, "experiments/w135/worlds")
DEV = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
rows = []
for w in DEV:
    b = w.split("_p")[0]
    U2 = pd.read_parquet(os.path.join(FH2, f"U2_{w}.parquet"), columns=["molecule", "y"]); Q2 = pd.read_parquet(os.path.join(FH2, f"Q2_{w}.parquet"), columns=["molecule", "wclass", "pi", "truth"])
    L = pd.read_csv(os.path.join(V2, w, f"ewin_molecules_{b}.csv"), usecols=["molecule", "truth_in_ewin"], dtype={"molecule": str}).set_index("molecule")
    M = pd.read_csv(os.path.join(WD, w, f"b1_molecules_{b}.csv"), dtype={"molecule": str}).set_index("molecule")
    Wk = pd.read_parquet(os.path.join(WD, w, "gen", f"gen_{b}_window_okeys.parquet")); Wk["molecule"] = Wk.molecule.astype(str); wk = Wk.groupby("molecule").official_key.apply(lambda s: set(s.astype(str))).to_dict()
    F = pd.read_parquet(os.path.join(WD, w, f"b1_features_{b}.parquet"), columns=["molecule", "official_key", "is_truth", "in_short_c2", "in_tier", "in_coconut", "in_train_c2"])
    F["molecule"] = F.molecule.astype(str); Ft = F[F.is_truth.astype(bool)]
    for D in (U2, Q2): D["molecule"] = D.molecule.astype(str)
    hit = set(U2[U2.y == 1].molecule)
    for m, wc, pi, t in Q2[["molecule", "wclass", "pi", "truth"]].itertuples(index=False):
        if wc not in ("C1", "C2") or m in hit or bool(L.loc[m, "truth_in_ewin"]): continue
        mm = M.loc[m]; ft = Ft[Ft.molecule == m]
        in_win = bool(mm.truth_in_window) or (str(t) in wk.get(m, set()))
        in_short = bool(mm.truth_in_shortlist)
        in_view = bool(len(ft) and (ft.in_short_c2.astype(bool) & (ft.in_tier | ft.in_coconut | ft.in_train_c2).astype(bool)).any())
        stage = "S0_not_in_window" if not in_win else ("S1_window_not_shortlist" if not in_short else ("S2_shortlist_not_view" if not in_view else "S3_view_not_top25"))
        rows.append(dict(world=w, molecule=m, wclass=wc, pi=int(pi), primary=(int(pi) == 30 and b[1] in "FR"), stage=stage, raw_in_window=bool(mm.truth_in_window),
                         okey_in_window=str(t) in wk.get(m, set()), in_short_c2_flag=bool(mm.truth_in_short_c2), n_window=(int(mm.n_window_structures) if pd.notna(mm.n_window_structures) else -1), n_short=(int(mm.n_shortlist) if pd.notna(mm.n_shortlist) else -1),
                         truth_rows_in_features=int(len(ft)), adducts=str(mm.adducts), n_query=int(mm.n_query)))
D = pd.DataFrame(rows)
for name, m in (("PRIMARY pi0.3 F/R", D.primary), ("pi0 all", D.pi == 0)):
    d = D[m]
    print(f"{name}: {len(d)} C1/C2 truths outside U2 and the E window")
    print("   by stage x class:", d.groupby(["stage", "wclass"]).size().to_dict())
    print("   raw flag in window", int(d.raw_in_window.sum()), "| official key in window", int(d.okey_in_window.sum()), "| truth rows in the candidate table", int((d.truth_rows_in_features > 0).sum()))
    print("   median window size", float(d.n_window.median()), "| median shortlist size", float(d.n_short.median()), "| window size missing", int((d.n_window < 0).sum()))
D.to_csv(os.path.join(ROOT, "experiments/w135/x161_cov_ledger.csv"), index=False)
