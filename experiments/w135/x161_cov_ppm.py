"""161 (Codex 161 Q5, step 4): for the S0 truths of the coverage ledger (not in the B1 window), the precursor error: the truth's neutral mass
(batch CSV 'mass') vs the query's neutral mass per adduct (b1_common.neutral_mass, median over the query spectra of that adduct -- the B1
window rule, +-10 ppm). Reports the minimum |ppm| over the adducts and the query library, against a control: the in-window C1 / C2 truths of
the same worlds. Development worlds only. Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x161_cov_ppm.py"""
import json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_common import neutral_mass
WD = os.path.join(ROOT, "experiments/w135/worlds")
L = pd.read_csv(os.path.join(ROOT, "experiments/w135/x161_cov_ledger.csv"), dtype={"molecule": str})
rows = []
for w in sorted(set(L.world)) + []:
    pass
DEV = sorted(set(L.world))
for w in DEV:
    b = w.split("_p")[0]
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv"), dtype={"molecule": str}).set_index("molecule")
    run = {d["mid"]: d for d in json.load(open(os.path.join(WD, w, "prod_runner_in.json")))}
    M = pd.read_csv(os.path.join(WD, w, f"b1_molecules_{b}.csv"), dtype={"molecule": str}).set_index("molecule")
    s0 = set(L[(L.world == w)].molecule)
    for m in bt.index:
        if bt.loc[m, f"wclass_p{w.split('_p')[1]}"] not in ("C1", "C2"): continue
        tm = float(bt.loc[m, "mass"]); by = {}
        for s in run[m]["spectra"]:
            nm = neutral_mass(float(s["prec"]), s["adduct"])
            if nm is not None and np.isfinite(nm): by.setdefault(s["adduct"], []).append(nm)
        ppm = min([abs((np.median(v) - tm) / tm * 1e6) for v in by.values()], default=np.nan)
        rows.append(dict(world=w, molecule=m, s0=m in s0, lib=str(bt.loc[m, "lib"]), ppm=ppm, adducts=";".join(sorted(by)), truth_in_window=bool(M.loc[m, "truth_in_window"])))
D = pd.DataFrame(rows)
for nm, d in (("S0 (not in window)", D[D.s0]), ("control: C1/C2 truth in window", D[~D.s0 & D.truth_in_window])):
    p = d.ppm
    print(f"{nm}: n {len(d)} | min|ppm| median {p.median():.1f}, >10 ppm {int((p > 10).sum())} ({(p > 10).mean():.2f}), >50 ppm {int((p > 50).sum())}, NaN {int(p.isna().sum())}")
    print("    library:", d.lib.value_counts().head(6).to_dict())
D.to_csv(os.path.join(ROOT, "experiments/w135/x161_cov_ppm.csv"), index=False)
