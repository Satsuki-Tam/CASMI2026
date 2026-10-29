"""127 learning curve reading (127_prereg_lc.md; descriptive, a planning input, written before any result). Inputs: diag/rlc127_<model>_<tag>.csv
from ONE gen_eval2fd (reviewed version) pass per tag with the models v8w7a (= frac 1.0, reproduced byte for byte by rank_lc127_full) and
rank_lc127_f05s1 / f05s2 / f025s1 / f025s2. Checks (STOP): the same (set, view, molecule) rows for every model of a tag, unique; v8w7a's main
equal to diag/r102_<tag>.csv on every row (one-to-one); RR finite in [0, 1]; every reported cell non-empty.
Per model and fold: primary = 1/4 NP_H C2 + 1/4 NP_N C2 + 1/2 D C2 (np053f<k>dev, f<k>dev), old B (C/D/E/F C2 equal), G C1, NP C1 (NP_H / NP_N C1
equal); the two-fold mean; difference vs v8w7a with a paired identity bootstrap (4000, seed 20261029) on the two-fold mean primary.
P(f) = seed mean of the two-fold mean primary. Reading (fixed): P(1.0) - P(0.5) >= +0.010 and P(0.5) - P(0.25) >= +0.010 -> data-limited at the
current scale; P(1.0) - P(0.5) < +0.005 -> close to saturation; otherwise undetermined.
Usage (Spark, experiments/b1_baseline): python -X utf8 x_lc127.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12; rng = np.random.default_rng(20261029)
MODELS = {"v8w7a": 1.0, "rank_lc127_f05s1": 0.5, "rank_lc127_f05s2": 0.5, "rank_lc127_f025s1": 0.25, "rank_lc127_f025s2": 0.25}
TAGS = ("f1dev", "np053f1dev", "f2dev", "np053f2dev"); K = ["set", "view", "molecule"]
D = {}
for t in TAGS:
    ref = pd.read_csv(os.path.join(HERE, f"diag/r102_{t}.csv"), usecols=K + ["main"]); ref["molecule"] = ref.molecule.astype(str); assert not ref.duplicated(K).any()
    keys0 = None
    for m in MODELS:
        x = pd.read_csv(os.path.join(HERE, f"diag/rlc127_{m}_{t}.csv"), usecols=K + ["main"]); x["molecule"] = x.molecule.astype(str)
        assert not x.duplicated(K).any(), (m, t, "duplicates"); v = x.main.values.astype(float); assert np.isfinite(v).all() and (v >= -TOL).all() and (v <= 1 + TOL).all(), (m, t)
        x = x.sort_values(K).reset_index(drop=True); kk = x[K].astype(str).agg("|".join, axis=1).tolist()
        if keys0 is None: keys0 = kk
        assert kk == keys0, (m, t, "row sets differ between models")
        if m == "v8w7a":
            mm = x.merge(ref, on=K, how="outer", suffixes=("", "_ref"), indicator=True, validate="one_to_one")
            assert (mm._merge == "both").all() and (np.abs(mm.main - mm.main_ref) <= TOL).all(), (t, "v8w7a main differs from r102")
        D[(m, t)] = x
    print(f"{t}: {len(keys0)} rows, all models aligned; v8w7a == r102")
def cell(m, t, sets, view):
    x = D[(m, t)]; x = x[x.set.isin(sets) & (x.view == view)]; assert len(x) > 0, (m, t, sets, view); return x.main.values.astype(float)
def comp(m, k):
    dev, np_ = f"f{k}dev", f"np053f{k}dev"
    return dict(primary=[(0.25, cell(m, np_, ["NP_H"], "c2")), (0.25, cell(m, np_, ["NP_N"], "c2")), (0.5, cell(m, dev, ["D_np_single"], "c2"))],
                oldB=[(0.25, cell(m, dev, [s], "c2")) for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered")],
                GC1=[(1.0, cell(m, dev, ["G_tims_crosslib"], "c1"))], NPC1=[(0.5, cell(m, np_, ["NP_H"], "c1")), (0.5, cell(m, np_, ["NP_N"], "c1"))])
val = lambda parts: sum(w * a.mean() for w, a in parts)
L = ["# 127 learning curve of the ranker (descriptive; v8w7a recipe, fit fraction x seed)", "",
     "| model | frac | primary f1 | primary f2 | primary mean | d vs v8w7a [95%] | old B mean | G C1 mean | NP C1 mean |", "|---|---:|---:|---:|---:|---|---:|---:|---:|"]
P = {}
for m, f in MODELS.items():
    c = {k: comp(m, k) for k in (1, 2)}; base = {k: comp("v8w7a", k) for k in (1, 2)}
    pm = 0.5 * (val(c[1]["primary"]) + val(c[2]["primary"])); P.setdefault(f, []).append(pm)
    bs = np.zeros(NB)
    for k in (1, 2):
        for (w, a), (_, b) in zip(c[k]["primary"], base[k]["primary"]):
            d = a - b; bs += 0.5 * w * d[rng.integers(0, len(d), size=(NB, len(d)))].mean(1)
    dd = pm - 0.5 * (val(base[1]["primary"]) + val(base[2]["primary"]))
    L.append(f"| {m} | {f} | {val(c[1]['primary']):.4f} | {val(c[2]['primary']):.4f} | {pm:.4f} | {dd:+.4f} [{np.quantile(bs, 0.025):+.4f}, {np.quantile(bs, 0.975):+.4f}] | "
             f"{0.5 * (val(c[1]['oldB']) + val(c[2]['oldB'])):.4f} | {0.5 * (val(c[1]['GC1']) + val(c[2]['GC1'])):.4f} | {0.5 * (val(c[1]['NPC1']) + val(c[2]['NPC1'])):.4f} |")
Pf = {f: float(np.mean(v)) for f, v in P.items()}
s1, s2 = Pf[1.0] - Pf[0.5], Pf[0.5] - Pf[0.25]
verdict = "data-limited at the current scale" if (s1 >= 0.010 and s2 >= 0.010) else ("close to saturation" if s1 < 0.005 else "undetermined")
L += ["", f"P(0.25) {Pf[0.25]:.4f}, P(0.5) {Pf[0.5]:.4f}, P(1.0) {Pf[1.0]:.4f} -> P(1.0) - P(0.5) {s1:+.4f}, P(0.5) - P(0.25) {s2:+.4f}", "",
      f"**Reading (fixed in 127_prereg_lc.md): {verdict}.** Limits: 600 rounds fixed (small fractions may overfit -> slope on the high side); the fit mix shrinks proportionally (no new kinds of groups); f1/f2 dev are reused development sets."]
out = chr(10).join(L) + chr(10); open(os.path.join(HERE, "diag/x_lc127.md"), "w", encoding="utf-8").write(out); print(out)
