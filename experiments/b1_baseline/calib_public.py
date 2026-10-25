"""Public-calibrated mixture of local strata (approximate Bayesian computation over mixture weights).

The hidden test is modelled as a mixture of local "types" (class-1 views, class-2 views split by the truth's candidate group, absent/class 3).
Every type has exact per-variant RR means from frozen tables (group_filter_eval.py outputs; the registered evaluator's formulas, parity-checked).
Mixture weights w ~ Dirichlet(alpha); a draw is kept when the predicted Public values of the submitted variants are all within tolerance of the
observed ones. Reported: acceptance, posterior class shares, and the posterior predictive of other variants (e.g. a later submission, used as an
out-of-sample check). Class 1 under the fold-0 FPNet is treated as q_seen seen (full_rk-table values) + (1 - q_seen) unseen (fold-0 values);
the hard dev2 class-1 layers have no seen version (held out everywhere) and keep unseen values (flagged).
Usage: python -X utf8 calib_public.py --obs main=0.354 insurance=0.336 pool=0.37 pc=0.05 [--check fe_main=0.36] [--q_seen 0.8]
"""
import argparse
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--obs", nargs="+", required=True, help="VARIANT=public value, e.g. main=0.354 insurance=0.336 pool=0.37 pc=0.05")
ap.add_argument("--check", nargs="*", default=[], help="VARIANT=public value used only as an out-of-sample check")
ap.add_argument("--tol", type=float, default=0.015, help="tolerance on differences to main")
ap.add_argument("--tol_level", type=float, default=0.03, help="tolerance on the level of main")
ap.add_argument("--q_seen", type=float, default=0.8)
ap.add_argument("--draws", type=int, default=2000000)
ap.add_argument("--alpha", type=float, default=1.0)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--out", default="diag/calib_public.md")
a = ap.parse_args()
OBS = {k: float(v) for k, v in (s.split("=") for s in a.obs)}
CHK = {k: float(v) for k, v in (s.split("=") for s in a.check)}
V = ["main", "insurance", "pool", "pc", "train", "coconut_only", "fe_main", "rk_old_main", "rk_new_main"]
FILT = ["main", "insurance", "pool", "pc", "train", "coconut_only", "nontrain"]


def load(f):
    R = pd.read_csv(f"diag/gf_{f}.csv")
    R["molecule"] = R["molecule"].astype(str)
    return R.fillna({k: 0.0 for k in FILT})


m2x = pd.concat([load("m2x_panel"), load("m2x_p2dev"), load("m2x_devAB")], ignore_index=True)
rkv = pd.concat([load("rk_v4b_panel"), load("rk_v4b_p2dev"), load("rk_v4b_devAB")], ignore_index=True)
rkn = pd.concat([load("rk_rkfx_panel"), load("rk_rkfx_p2dev"), load("rk_rkfx_devAB")], ignore_index=True)


def fe_rr():   # full_eval main (M2x_fe blend21) per molecule from the registered evaluator outputs
    out = []
    for d, sets in (("fe_eval_panel", ["P_np250"]), ("fe_eval_p2dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
                    ("fe_eval_devAB", ["A_timstof", "B_nplib"])):
        for s in sets:
            for v in ("c1", "c2"):
                try:
                    p = pd.read_csv(f"{d}/pred_{s}_{v}_M2x_fe_blend21.csv", usecols=["molecule_id", "rr"])
                except FileNotFoundError:
                    continue
                out.append(p.rename(columns={"molecule_id": "molecule", "rr": "fe_main"}).assign(set=s, view=v))
    f = pd.concat(out, ignore_index=True)
    f["molecule"] = f["molecule"].astype(str)
    return f


key = ["set", "view", "molecule"]
base = m2x.merge(fe_rr(), on=key, how="left")
base = base.merge(rkv[key + ["main"]].rename(columns={"main": "rk_old_main"}), on=key, how="left")
base = base.merge(rkn[key + ["main"]].rename(columns={"main": "rk_new_main"}), on=key, how="left")
seen = rkv   # class-1 'seen' values for the M2x-family variants: the same rank_v4b on the full_rk tables (identity seen, query unseen)


def tmean(D, mask, cols):
    s = D[mask]
    return {c: float(s[c].mean()) for c in cols if c in s.columns}, int(mask.sum())


TYPES = []


def add(name, cls, mask_fn, seen_ok):
    vals, n = tmean(base, mask_fn(base), V)
    if seen_ok:
        sv, _ = tmean(seen, mask_fn(seen), ["main", "insurance", "pool", "pc", "train", "coconut_only"])
        for k in sv:
            vals[k] = a.q_seen * sv[k] + (1 - a.q_seen) * vals[k]
    TYPES.append(dict(name=name, cls=cls, n=n, seen_mix=seen_ok, **{k: vals.get(k, np.nan) for k in V}))


def c1(D):
    return (D.view == "c1") & (D.truth_group == "train")


def c2(D, g):
    return (D.view == "c2") & (D.truth_group == g)


add("C1 panel (Enveda timsTOF NP)", "1", lambda D: c1(D) & (D.set == "P_np250"), True)
add("C1 hard NP (dev2 C/E/F/G)", "1", lambda D: c1(D) & D.set.isin(["C_np_crosslib", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]), False)
add("C1 W7 NP libraries", "1", lambda D: c1(D) & (D.set == "B_nplib"), True)
add("C2 COCONUT panel", "2c", lambda D: c2(D, "coconut_only") & (D.set == "P_np250"), False)
add("C2 COCONUT hard NP (dev2)", "2c", lambda D: c2(D, "coconut_only") & D.set.isin(["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]), False)
add("C2 COCONUT W7 NP", "2c", lambda D: c2(D, "coconut_only") & (D.set == "B_nplib"), False)
add("C2 PubChem-only hard NP (dev2)", "2p", lambda D: c2(D, "pc") & D.set.isin(["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]), False)
add("C2 PubChem-only W7 timsTOF synthetic", "2p", lambda D: c2(D, "pc") & (D.set == "A_timstof"), False)
add("C2 PubChem-only W7 NP", "2p", lambda D: c2(D, "pc") & (D.set == "B_nplib"), False)
TYPES.append(dict(name="absent / class 3", cls="3", n=0, seen_mix=False, **{k: 0.0 for k in V}))
T = pd.DataFrame(TYPES)
K = len(T)
rng = np.random.default_rng(a.seed)
W = rng.dirichlet(np.full(K, a.alpha), size=a.draws)
pred = {v: W @ T[v].fillna(0.0).to_numpy() for v in V}
ok = np.abs(pred["main"] - OBS["main"]) <= a.tol_level
for k, val in OBS.items():
    if k != "main":
        ok &= np.abs((pred[k] - pred["main"]) - (val - OBS["main"])) <= a.tol
Wa = W[ok]
L = [f"# Public-calibrated mixture (ABC): {a.draws:,} Dirichlet({a.alpha}) draws, accepted {int(ok.sum()):,}", "",
     f"observed {OBS} | check {CHK} | tol diff {a.tol}, level {a.tol_level} | class-1 seen share {a.q_seen}", "",
     "| type | class | n local | " + " | ".join(V) + " | posterior weight mean [5%, 95%] |", "|---|---|---:|" + "---:|" * len(V) + "---|"]
for i, r in T.iterrows():
    q = np.percentile(Wa[:, i], [5, 95]) if len(Wa) else [np.nan, np.nan]
    m = Wa[:, i].mean() if len(Wa) else np.nan
    cells = " | ".join(f"{r[v]:.3f}" if pd.notna(r[v]) else "-" for v in V)
    L.append(f"| {r['name']}{' (seen mix)' if r['seen_mix'] else ''} | {r['cls']} | {r['n']} | {cells} | {m:.3f} [{q[0]:.3f}, {q[1]:.3f}] |")
if len(Wa):
    L += ["", "| class share | posterior mean [5%, 95%] |", "|---|---|"]
    for cl in ("1", "2c", "2p", "3"):
        s_ = Wa[:, (T.cls == cl).to_numpy()].sum(1)
        L.append(f"| {cl} | {s_.mean():.3f} [{np.percentile(s_, 5):.3f}, {np.percentile(s_, 95):.3f}] |")
    L += ["", "| variant | posterior predictive Public mean [5%, 95%] | delta vs main mean [5%, 95%] | observed / check |", "|---|---|---|---|"]
    for v in V:
        p_ = pred[v][ok]
        d_ = p_ - pred["main"][ok]
        L.append(f"| {v} | {np.nanmean(p_):.3f} [{np.nanpercentile(p_, 5):.3f}, {np.nanpercentile(p_, 95):.3f}] | "
                 f"{np.nanmean(d_):+.3f} [{np.nanpercentile(d_, 5):+.3f}, {np.nanpercentile(d_, 95):+.3f}] | {OBS.get(v, CHK.get(v, ''))} |")
open(a.out, "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
