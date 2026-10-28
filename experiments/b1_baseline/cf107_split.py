"""107: 2-fold cross-fitting split of the four used fold-safe development tables by identity group (seed 1070, per table; labels not used).
Writes diag/cf107/<tag>_A.csv and _B.csv (subsets of the selection CSV, all sets) and diag/cf107/split.csv (tag, set, molecule, identity_group, fold).
Usage: python -X utf8 cf107_split.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "diag", "cf107"); os.makedirs(OUT, exist_ok=True)
CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv"}
rows = []
for k, (tag, csv) in enumerate(CSV.items()):
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str)
    groups = sorted(ev.identity_group.unique().tolist()); rng = np.random.default_rng(1070 + k); perm = rng.permutation(len(groups))
    fold = {g: ("A" if perm[i] % 2 == 0 else "B") for i, g in enumerate(groups)}
    ev["cf"] = ev.identity_group.map(fold)
    for f in ("A", "B"): ev[ev.cf == f].drop(columns=["cf"]).to_csv(os.path.join(OUT, f"{tag}_{f}.csv"), index=False)
    rows.append(ev[["set", "molecule", "identity_group", "cf"]].assign(tag=tag))
    print(tag, ev.cf.value_counts().to_dict(), "groups", len(groups))
S = pd.concat(rows); assert not S.duplicated(["tag", "molecule"]).any(); S.to_csv(os.path.join(OUT, "split.csv"), index=False)
