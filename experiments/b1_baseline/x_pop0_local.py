"""pop0 local cost (116 / 124 / 125): DESCRIPTIVE reading of diag/rpop0_<tag>.csv (gen_eval2fd --v7f --parents 0 --pop_ws 0.5,0 with rank_v8w7a),
written before any of these rows existed. Not a gate and not a method selection: it states what the pop0 diagnostic kernel (fixed-rule prior
coefficient 0 on both paths of the frozen v8w7a) costs or gains on the development layers, as Codex 116 asks before such a probe is proposed.
Checks (STOP): pw0.5 == main on every row (the evaluator's variant path reproduces P); main equal to diag/r102_<tag>.csv (f1dev, np053f1dev,
f2dev, np053f2dev) or diag/r111_base_c1bankdev.csv (bank) on the shared rows, with no missing rows; RR values finite in [0, 1].
Reported per fold (fold 1 = f1dev / np053f1dev / c1bankdev, fold 2 = f2dev / np053f2dev; the panel separately), d = pw0 - main:
  primary layout of 111 (1/4 NP_H C2 + 1/4 NP_N C2 + 1/2 D C2), old B (C/D/E/F C2 equal), G C1, NP C1 (NP_H / NP_N C1 equal), c1dev pooled C1,
  panel C2 and panel C1 clean; 95% identity-bootstrap intervals (4000, seed 20261029); rows changed up / down per cell.
Usage (Spark, experiments/b1_baseline): python -X utf8 x_pop0_local.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12; rng = np.random.default_rng(20261029)
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
R = {}
for tag in ("f1dev", "np053f1dev", "c1bankdev", "f2dev", "np053f2dev", "panel"):
    x = pd.read_csv(os.path.join(HERE, f"diag/rpop0_{tag}.csv")); x["molecule"] = x.molecule.astype(str)
    for c in ("main", "pw0.5", "pw0.0"):
        v = x[c].values.astype(float); assert np.isfinite(v).all() and (v >= -TOL).all() and (v <= 1 + TOL).all(), (tag, c)
    assert (np.abs(x["pw0.5"].values - x["main"].values) <= TOL).all(), (tag, "pw0.5 != main", int((np.abs(x["pw0.5"].values - x["main"].values) > TOL).sum()))
    ref = {"c1bankdev": "diag/r111_base_c1bankdev.csv", "panel": None}.get(tag, f"diag/r102_{tag}.csv")
    if ref and os.path.exists(os.path.join(HERE, ref)):
        y = pd.read_csv(os.path.join(HERE, ref), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
        k = ["set", "view", "molecule"]; m = x[k + ["main"]].merge(y, on=k, how="outer", suffixes=("", "_ref"), indicator=True)
        assert (m._merge == "both").all(), (tag, "rows differ from", ref, m._merge.value_counts().to_dict())
        assert (np.abs(m.main.values - m.main_ref.values) <= TOL).all(), (tag, "main differs from", ref)
        print(f"{tag}: main == {ref} on all {len(m)} rows; pw0.5 == main")
    else:
        print(f"{tag}: no reference file ({ref}); pw0.5 == main on all {len(x)} rows")
    R[tag] = x
def cell(tag, sets, view, filt=None):
    x = R[tag]; x = x[x.set.isin(sets) & (x.view == view)]
    if filt is not None: x = x[x.molecule.isin(filt)]
    return x
def boot(parts):   # parts: list of (weight, frame); identities resampled within each part
    est = sum(w * (f["pw0.0"].values - f["main"].values).mean() for w, f in parts)
    bs = np.zeros(NB)
    for w, f in parts:
        d = f["pw0.0"].values - f["main"].values; idx = rng.integers(0, len(d), size=(NB, len(d))); bs += w * d[idx].mean(1)
    return est, np.quantile(bs, 0.025), np.quantile(bs, 0.975)
L = ["# pop0 local cost (descriptive; fixed-rule prior coefficient 0 vs 0.5 on the frozen v8w7a, stored tables)", "",
     "| fold | quantity | n | main | pop0 | d = pop0 - main [95%] | rows up / down |", "|---|---|---:|---:|---:|---|---|"]
def row(fold, name, parts):
    n = sum(len(f) for _, f in parts); est, lo, hi = boot(parts)
    mm = sum(w * f["main"].mean() for w, f in parts); pp = sum(w * f["pw0.0"].mean() for w, f in parts)
    up = sum(int((f["pw0.0"].values - f["main"].values > TOL).sum()) for _, f in parts); dn = sum(int((f["pw0.0"].values - f["main"].values < -TOL).sum()) for _, f in parts)
    L.append(f"| {fold} | {name} | {n} | {mm:.4f} | {pp:.4f} | {est:+.4f} [{lo:+.4f}, {hi:+.4f}] | {up} / {dn} |")
for fold, dev, np_ in (("1", "f1dev", "np053f1dev"), ("2", "f2dev", "np053f2dev")):
    row(fold, "primary (1/4 NP_H C2 + 1/4 NP_N C2 + 1/2 D C2)", [(0.25, cell(np_, ["NP_H"], "c2")), (0.25, cell(np_, ["NP_N"], "c2")), (0.5, cell(dev, ["D_np_single"], "c2"))])
    for s in ("NP_H", "NP_N", "NP_X"): row(fold, f"{s} C2", [(1.0, cell(np_, [s], "c2"))])
    for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"): row(fold, f"{s} C2", [(1.0, cell(dev, [s], "c2"))])
    row(fold, "old B (C/D/E/F C2 equal)", [(0.25, cell(dev, [s], "c2")) for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered")])
    row(fold, "G C1", [(1.0, cell(dev, ["G_tims_crosslib"], "c1"))])
    row(fold, "NP C1 (NP_H / NP_N equal)", [(0.5, cell(np_, ["NP_H"], "c1")), (0.5, cell(np_, ["NP_N"], "c1"))])
    if fold == "1":
        b = R["c1bankdev"]; row(fold, "c1dev bank C1 pooled", [(1.0, b[b.view == "c1"])])
row("panel", "panel C2", [(1.0, cell("panel", ["P_np250"], "c2"))])
row("panel", "panel C1 clean", [(1.0, cell("panel", ["P_np250"], "c1", CLEAN))])
L += ["", "Reading: descriptive only (Codex 116 contract for a pop0 probe): the local cost / gain of the fixed-rule prior coefficient 0 on the frozen v8w7a.",
      "It does not select a coefficient, does not estimate hidden class ratios, and is not a method candidate."]
out = chr(10).join(L) + chr(10); open(os.path.join(HERE, "diag/x_pop0_local.md"), "w", encoding="utf-8").write(out); print(out)
