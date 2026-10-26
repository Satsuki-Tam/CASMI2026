"""Stage 2 for a change made INSIDE another configuration (e.g. twin-first on the full_eval order), with stage-1 weights from calib_public2 --dump_w.

D_t = mean paired (variant - base) over the molecules of proxy type t, both columns taken from the same per-molecule table of the configuration
(same FPNet, same shortlist: the regime where the calibration applies). Hybrid mode takes class-1 types from table A (e.g. full_eval: identity
seen, query unseen = hidden class 1) and class-2 types from table B (fold-0: identity unseen = hidden class 2).
Usage: python -X utf8 calib_within.py --w diag/W.npy --c1 fe --c2 m2x --tables gf2 --vars twin1_t0.7 ... --out diag/x.md
"""
import argparse, numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--w", nargs="+", required=True); ap.add_argument("--c1", default="fe"); ap.add_argument("--c2", default="m2x")
ap.add_argument("--tables", default="gf2"); ap.add_argument("--base", default="main"); ap.add_argument("--vars", nargs="+", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
W = np.concatenate([np.load(f) for f in a.w])


def load(cfg):
    out = []
    for part in ("panel", "p2dev", "devAB"):
        try: R = pd.read_csv(f"diag/{a.tables}_{cfg}_{part}.csv")
        except FileNotFoundError: continue
        R["molecule"] = R["molecule"].astype(str); out.append(R)
    R = pd.concat(out, ignore_index=True)
    return R.fillna({c: 0.0 for c in R.columns if c not in ("set", "view", "molecule", "truth_group", "gl_cover_ok")})


TYPES = [   # identical selectors to calib_public2.TYPES (order matters: weights columns)
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
assert W.shape[1] == len(TYPES) + 1
T1, T2 = load(a.c1), load(a.c2)
L = [f"# Within-configuration stage 2 (weights: {len(W)} accepted draws from {a.w}; class 1 from {a.c1}, class 2 from {a.c2}; base = {a.base})", "",
     "| variant | predicted Public delta vs base, mean [5%, 95%] | per-type deltas (n) |", "|---|---|---|"]
for v in a.vars:
    D, info = [], []
    for nm, cls, sel in TYPES:
        T = T1 if cls == "1" else T2
        g = T[sel(T)]
        d = float((g[v] - g[a.base]).mean()) if len(g) else 0.0
        D.append(d); info.append(f"{nm} {d:+.3f} ({len(g)})")
    p_ = W @ np.array(D + [0.0])
    L.append(f"| {v} | {p_.mean():+.4f} [{np.percentile(p_, 5):+.4f}, {np.percentile(p_, 95):+.4f}] | " + "; ".join(info) + " |")
open(a.out, "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))
