"""034 selection rule for the analog channel (fixed in reports/agent_review/034_prereg_analog.md before the tables were computed).

Class-2 layers (13): full_eval dev2 C2 C/D/E/F/G, fold-0 dev2 C2 C/D/E/F/G, fold-0 panel C2 clean, fold-0 W7 A C2, fold-0 W7 B C2.
Constraints: every class-2 layer delta >= -0.02 (point); panel C1 clean (full_eval) delta >= -0.01.
Objective: equal-weight mean delta over the 13 class-2 layers. Candidates: the variants listed in the prereg.
Then, for the selected variant only: the confirmation tables (fresh sets, fold-0) with paired bootstrap 95% intervals per layer.
Usage: python -X utf8 analog_select.py [--confirm diag/gf3_conf3_m2x.csv diag/gf3_conffit_m2x.csv] --out diag/analog_select.md
"""
import argparse
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--prefix", default="gf4"); ap.add_argument("--confirm", nargs="*", default=[]); ap.add_argument("--out", default="diag/analog_select.md")
ap.add_argument("--audit_csv", default="../fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv")
a = ap.parse_args()
CANDS = ["anaw0.5", "anaw1", "anamt0.5", "anamt1", "anamt2", "anaxw0.5", "anaxw1", "anamtx0.5", "anamtx1", "anamtx2"]
grp = pd.read_csv(a.audit_csv).set_index("molecule").audit_group


def load(cfg, parts):
    T = pd.concat([pd.read_csv(f"diag/{a.prefix}_{cfg}_{p}.csv") for p in parts], ignore_index=True); T["molecule"] = T.molecule.astype(str)
    for c in ["main"] + CANDS: T[c] = T[c].fillna(0.0)
    return T


FE, F0 = load("fe", ("panel", "p2dev")), load("m2x", ("panel", "p2dev", "devAB"))
clean = lambda T: T.molecule.map(grp).eq("clean_nearest_lt_0.90")
LAYERS = [(f"fe dev2 {s[0]} C2", FE, (FE.set == s) & (FE.view == "c2")) for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib")] + \
         [(f"f0 dev2 {s[0]} C2", F0, (F0.set == s) & (F0.view == "c2")) for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib")] + \
         [("f0 panel C2 clean", F0, (F0.set == "P_np250") & (F0.view == "c2") & clean(F0)), ("f0 W7 A C2", F0, (F0.set == "A_timstof") & (F0.view == "c2")),
          ("f0 W7 B C2", F0, (F0.set == "B_nplib") & (F0.view == "c2"))]
C1 = ("fe panel C1 clean", FE, (FE.set == "P_np250") & (FE.view == "c1") & clean(FE))
SIDE = [("fe panel C1 uncertain", FE, (FE.set == "P_np250") & (FE.view == "c1") & FE.molecule.map(grp).eq("uncertain_nearest_ge_0.90")),
        ("f0 panel C1 clean (unseen)", F0, (F0.set == "P_np250") & (F0.view == "c1") & clean(F0)), ("f0 W7 B C1", F0, (F0.set == "B_nplib") & (F0.view == "c1"))] + \
       [(f"fe dev2 {s[0]} C1 (unseen stress)", FE, (FE.set == s) & (FE.view == "c1")) for s in ("C_np_crosslib", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib")]
d = lambda T, sel, v: float((T[sel][v] - T[sel]["main"]).mean())
rows = []
for v in CANDS:
    ds = [d(T, sel, v) for _, T, sel in LAYERS]; c1 = d(C1[1], C1[2], v)
    rows.append(dict(variant=v, objective=np.mean(ds), min_c2_layer=min(ds), worst=LAYERS[int(np.argmin(ds))][0], panel_c1_clean=c1, passes=bool(min(ds) >= -0.02 and c1 >= -0.01)))
R = pd.DataFrame(rows).sort_values("objective", ascending=False)
ok = R[R.passes]
sel_v = ok.iloc[0]["variant"] if len(ok) else None
L = ["# 034 analog selection (rule fixed before the tables)", "", R.round(4).to_string(index=False), "", f"**selected: {sel_v}**", ""]
if sel_v:
    L += ["| layer | n | main | delta |", "|---|---:|---:|---:|"] + [f"| {nm} | {int(sel.sum())} | {T[sel]['main'].mean():.3f} | {d(T, sel, sel_v):+.4f} |" for nm, T, sel in LAYERS + [C1] + SIDE]
    if a.confirm:
        rng = np.random.default_rng(0)
        Cf = pd.concat([pd.read_csv(f) for f in a.confirm], ignore_index=True)
        Cf[sel_v] = Cf[sel_v].fillna(0.0); Cf["main"] = Cf["main"].fillna(0.0)
        L += ["", f"## Confirmation (fresh sets, fold-0 tables): {a.confirm}", "", "| layer | n | main | delta [95% paired bootstrap] |", "|---|---:|---:|---|"]
        for (s, v), g in Cf.groupby(["set", "view"]):
            x = (g[sel_v] - g["main"]).to_numpy(); bs = [rng.choice(x, len(x)).mean() for _ in range(4000)]
            L.append(f"| {s} {v.upper()} | {len(g)} | {g['main'].mean():.3f} | {x.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}] |")
        c2 = Cf[Cf.view == "c2"]; x = (c2[sel_v] - c2["main"]).to_numpy(); bs = [rng.choice(x, len(x)).mean() for _ in range(4000)]
        L.append(f"| all C2 (pooled) | {len(c2)} | {c2['main'].mean():.3f} | {x.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}] |")
open(a.out, "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))
