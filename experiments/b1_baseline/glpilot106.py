"""106 GL-summary pilot, step 1: fixed-seed stratified subset of already-used development molecules -> GLACIER runner inputs (subset of the runs'
b1_runner_<set>_in.json; candidates and spectra unchanged) -> diag/glpilot106/in_<tag>_<set>.json + the subset list. No labels are used for the selection
(set membership only). Strata (seed 1060): np053f1dev / np053f2dev NP_H 40 + NP_N 20 each; f1dev / f2dev C 30, D 30, G 30 each; panel 40.
Usage: python -X utf8 glpilot106.py"""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "diag", "glpilot106"); os.makedirs(OUT, exist_ok=True)
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
TAKE = {("np053f1dev", "NP_H"): 40, ("np053f1dev", "NP_N"): 20, ("np053f2dev", "NP_H"): 40, ("np053f2dev", "NP_N"): 20,
        ("f1dev", "C_np_crosslib"): 30, ("f1dev", "D_np_single"): 30, ("f1dev", "G_tims_crosslib"): 30,
        ("f2dev", "C_np_crosslib"): 30, ("f2dev", "D_np_single"): 30, ("f2dev", "G_tims_crosslib"): 30, ("panel", "P_np250"): 40}
rng = np.random.default_rng(1060); rows = []
for (tag, s), n in TAKE.items():
    run = os.path.join(HERE, RUN_OF[tag]); M = pd.read_csv(os.path.join(run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str)
    mols = sorted(M.molecule.tolist()); pick = sorted(rng.choice(len(mols), size=min(n, len(mols)), replace=False).tolist())
    keep = {mols[i] for i in pick}
    items = [it for it in json.load(open(os.path.join(run, f"b1_runner_{s}_in.json"))) if str(it.get("mid")) in keep]
    json.dump(items, open(os.path.join(OUT, f"in_{tag}_{s}.json"), "w"))
    rows += [dict(tag=tag, set=s, molecule=m) for m in sorted(keep)]
    print(f"{tag} {s}: {len(keep)} molecules, {sum(len(it.get('cands') or []) for it in items)} candidates")
pd.DataFrame(rows).to_csv(os.path.join(OUT, "subset.csv"), index=False); print("subset", len(rows))
