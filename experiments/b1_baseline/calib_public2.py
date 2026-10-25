"""Two-stage Public-calibrated prediction (Codex 026 Q3): a consistency check between local proxy strata and Public observations.

Stage 1 (weights): the hidden Public set is approximated by a mixture of local proxy types (class-1 views, class-2 views split by the truth's
candidate group, and a component that scores 0 under every configuration). Dirichlet draws of the weights are kept when the fold-0
configurations that were actually submitted (M2x main 0.354, its insurance list 0.336, the pool / Pc probes) are reproduced within tolerance.
Only fold-0 tables enter stage 1 (same FPNet as every submitted fold-0 configuration).
Stage 2 (prediction): for another configuration X, the Public delta is predicted as sum_t w_t * D_t(X), where D_t(X) = mean paired RR
difference X - M2x over the VALID molecules of type t (identity unseen by X's FPNet for class 2; query unseen for class 1). Cells that cannot
be measured are imputed from a named similar type and flagged; a sensitivity row sets imputed cells to 0.
Class 1 under the fold-0 FPNet is about q_seen seen; the seen part has no fold-0 measurement, so for a new FPNet the class-1 delta is
(1 - q_seen) * D_unseen + q_seen * D_seen, with D_seen unmeasured (0 in the main row, sensitivity rows +-).
Usage: python -X utf8 calib_public2.py --obs main=0.354 insurance=0.336 [pool=.. pc=..] [--check fe_main=..]
"""
import argparse
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--obs", nargs="+", required=True)
ap.add_argument("--check", nargs="*", default=[])
ap.add_argument("--tol", type=float, default=0.015)
ap.add_argument("--tol_level", type=float, default=0.03)
ap.add_argument("--q_seen", type=float, default=0.8)
ap.add_argument("--draws", type=int, default=1000000)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--out", default="diag/calib_public2.md")
a = ap.parse_args()
OBS = {k: float(v) for k, v in (s.split("=") for s in a.obs)}
CHK = {k: float(v) for k, v in (s.split("=") for s in a.check)}
FILT = ["main", "insurance", "pool", "pc", "train", "coconut_only", "nontrain", "pcd0.5", "pcd1", "pcd2", "pcd4"]
key = ["set", "view", "molecule"]


def load(names):
    out = []
    for f in names:
        R = pd.read_csv(f"diag/gf_{f}.csv")
        R["molecule"] = R["molecule"].astype(str)
        out.append(R.fillna({k: 0.0 for k in FILT if k in R.columns}))
    return pd.concat(out, ignore_index=True)


F0 = load(["m2x_panel", "m2x_p2dev", "m2x_devAB"])                 # fold-0 tables (submitted configurations)
RKO = load(["rk_v4b_panel", "rk_v4b_p2dev", "rk_v4b_devAB"])      # full_rk + rank_v4b
RKN = load(["rk_rkfx_panel", "rk_rkfx_p2dev", "rk_rkfx_devAB"])   # full_rk + rank_rk_fx
FEO = load(["fe_v4b_panel", "fe_v4b_p2dev"])                       # full_eval + rank_v4b (= submitted 57630996)
FEN = load(["fe_rkfx_panel", "fe_rkfx_p2dev"])                     # full_eval + rank_rk_fx
ex = pd.read_csv("../fpnet_full/full_rk/query_identity_exposure.csv")
W7_SEEN_RK = set(ex[ex.exposure == "c1_seen"].molecule.astype(str))

TYPES = [   # name, class, selector on (set, view, truth_group)
    ("C1 panel", "1", lambda D: (D.view == "c1") & (D.truth_group == "train") & (D.set == "P_np250")),
    ("C1 hard NP dev2", "1", lambda D: (D.view == "c1") & (D.truth_group == "train") & D.set.isin(["C_np_crosslib", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"])),
    ("C1 W7 NP", "1", lambda D: (D.view == "c1") & (D.truth_group == "train") & (D.set == "B_nplib")),
    ("C2 COCONUT panel", "2c", lambda D: (D.view == "c2") & (D.truth_group == "coconut_only") & (D.set == "P_np250")),
    ("C2 COCONUT dev2", "2c", lambda D: (D.view == "c2") & (D.truth_group == "coconut_only") & D.set.isin(["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"])),
    ("C2 COCONUT W7 NP", "2c", lambda D: (D.view == "c2") & (D.truth_group == "coconut_only") & (D.set == "B_nplib")),
    ("C2 PubChem-only dev2", "2p", lambda D: (D.view == "c2") & (D.truth_group == "pc") & D.set.isin(["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"])),
    ("C2 PubChem-only W7 timsTOF", "2p", lambda D: (D.view == "c2") & (D.truth_group == "pc") & (D.set == "A_timstof")),
    ("C2 PubChem-only W7 NP", "2p", lambda D: (D.view == "c2") & (D.truth_group == "pc") & (D.set == "B_nplib")),
]
NAMES = [t[0] for t in TYPES] + ["zero under every configuration"]
K = len(NAMES)

# ---------------- stage 1: weights from the fold-0 observables
S1 = {v: np.array([F0[sel(F0)][v].mean() for _, _, sel in TYPES] + [0.0]) for v in ("main", "insurance", "pool", "pc", "pcd0.5", "pcd1", "pcd2", "pcd4")}
NT = np.array([int(sel(F0).sum()) for _, _, sel in TYPES] + [0])
rng = np.random.default_rng(a.seed)
Wd = rng.dirichlet(np.ones(K), size=a.draws)
pred1 = {v: Wd @ S1[v] for v in S1}
ok = np.abs(pred1["main"] - OBS["main"]) <= a.tol_level
for k_, val in OBS.items():
    if k_ != "main":
        ok &= np.abs((pred1[k_] - pred1["main"]) - (val - OBS["main"])) <= a.tol
W = Wd[ok]


# ---------------- stage 2: per-type paired deltas on valid molecules
def paired(X, xcol, sel_fn, extra=None):
    j = F0[key + ["truth_group", "main"]].merge(X[key + [xcol]].rename(columns={xcol: "x"}), on=key)
    m = sel_fn(j)
    if extra is not None:
        m &= extra(j)
    return float((j[m].x - j[m].main).mean()) if m.sum() else np.nan, int(m.sum())


def deltas(X, xcol, valid, impute, class1_seen_unmeasured):
    D, flags = [], []
    for i, (nm, cls, sel) in enumerate(TYPES):
        if nm in valid:
            d, n = paired(X, xcol, sel, valid[nm] if callable(valid[nm]) else None)
            if class1_seen_unmeasured and cls == "1":
                d = (1 - a.q_seen) * d   # seen part (q_seen) unmeasured -> 0 in the main row
                flags.append(f"{nm}: (1-q_seen) x measured (n {n}), seen part 0")
            else:
                flags.append(f"{nm}: measured (n {n})")
            D.append(d)
        else:
            D.append(np.nan); flags.append(f"{nm}: imputed from {impute.get(nm)}")
    D = np.array(D + [0.0])
    for i, nm in enumerate(NAMES[:-1]):
        if np.isnan(D[i]):
            src = impute[nm]
            D[i] = D[NAMES.index(src)]
    imputed = np.array([nm not in valid for nm in NAMES[:-1]] + [False])
    return D, imputed, flags


ALL = {nm: True for nm in NAMES[:-1]}
unseen_w7_rk = lambda j: ~j.molecule.isin(W7_SEEN_RK)
VAR = {}
# fold-0 tables: Pc demotion (same FPNet and ranker as the submitted main)
for w in ("pcd0.5", "pcd1", "pcd2", "pcd4", "pool", "pc", "insurance"):
    VAR[w] = deltas(F0.rename(columns={w: "_x"}), "_x", ALL, {}, False)
fe_valid = {"C1 panel": True, "C1 hard NP dev2": True, "C2 COCONUT dev2": True, "C2 PubChem-only dev2": True}
fe_imp = {"C1 W7 NP": "C1 panel", "C2 COCONUT panel": "C2 COCONUT dev2", "C2 COCONUT W7 NP": "C2 COCONUT dev2",
          "C2 PubChem-only W7 timsTOF": "C2 PubChem-only dev2", "C2 PubChem-only W7 NP": "C2 PubChem-only dev2"}
VAR["fe_main (full_eval + rank_v4b, submitted)"] = deltas(FEO, "main", fe_valid, fe_imp, True)
VAR["fe_new (full_eval + rank_rk_fx)"] = deltas(FEN, "main", fe_valid, fe_imp, True)
rk_valid = {"C1 panel": True, "C1 hard NP dev2": True, "C1 W7 NP": True, "C2 COCONUT dev2": True, "C2 PubChem-only dev2": True,
            "C2 COCONUT W7 NP": unseen_w7_rk, "C2 PubChem-only W7 timsTOF": unseen_w7_rk, "C2 PubChem-only W7 NP": unseen_w7_rk}
rk_imp = {"C2 COCONUT panel": "C2 COCONUT dev2"}
VAR["rk_old (full_rk + rank_v4b)"] = deltas(RKO, "main", rk_valid, rk_imp, True)
VAR["rk_new (full_rk + rank_rk_fx)"] = deltas(RKN, "main", rk_valid, rk_imp, True)

L = [f"# Two-stage Public-calibrated prediction: {a.draws:,} draws, accepted {len(W):,}", "",
     f"observed (stage 1, fold-0 configurations) {OBS} | check {CHK} | tol diff {a.tol}, level {a.tol_level} | q_seen {a.q_seen}", "",
     "| type | n local | fold-0 main | insurance | pool | pc | pcd0.5 | pcd1 | pcd2 | posterior weight mean [5%, 95%] |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
for i, nm in enumerate(NAMES):
    q = np.percentile(W[:, i], [5, 95]) if len(W) else [np.nan, np.nan]
    L.append(f"| {nm} | {NT[i]} | " + " | ".join(f"{S1[v][i]:.3f}" for v in ("main", "insurance", "pool", "pc", "pcd0.5", "pcd1", "pcd2")) +
             f" | {W[:, i].mean() if len(W) else np.nan:.3f} [{q[0]:.3f}, {q[1]:.3f}] |")
if len(W):
    L += ["", "| class share (proxy weights, not the hidden class composition) | mean [5%, 95%] |", "|---|---|"]
    for cl, idx in (("class-1 proxies", [0, 1, 2]), ("class-2 COCONUT-truth proxies", [3, 4, 5]), ("class-2 PubChem-only-truth proxies", [6, 7, 8]), ("zero under every configuration", [9])):
        s_ = W[:, idx].sum(1)
        L.append(f"| {cl} | {s_.mean():.3f} [{np.percentile(s_, 5):.3f}, {np.percentile(s_, 95):.3f}] |")
    L += ["", "| configuration | predicted Public delta vs 0.354 mean [5%, 95%] | imputed cells -> 0 | check |", "|---|---|---|---|"]
    for nm, (D, imp, flags) in VAR.items():
        p_ = W @ D
        D0 = np.where(imp, 0.0, D)
        p0 = W @ D0
        chk = CHK.get(nm.split(" ")[0], "")
        L.append(f"| {nm} | {p_.mean():+.4f} [{np.percentile(p_, 5):+.4f}, {np.percentile(p_, 95):+.4f}] | {p0.mean():+.4f} | {chk} |")
    L += ["", "Per-type deltas used in stage 2:", ""]
    for nm, (D, imp, flags) in VAR.items():
        L.append(f"- {nm}: " + "; ".join(f"{NAMES[i]} {D[i]:+.3f}{' (imp)' if imp[i] else ''}" for i in range(K - 1)))
        L.append("  - " + " | ".join(flags))
open(a.out, "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
