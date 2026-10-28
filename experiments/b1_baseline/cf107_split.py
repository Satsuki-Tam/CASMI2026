"""107 v2 (after Codex 107): 2-fold cross-fitting split of the four used fold-safe development tables by identity group (seed 1070 + table index;
labels not used), with every identity group of a PROTECTED evaluation set excluded from all additional fits (kept in the evaluation denominators).
Protected sets: the panel (panel_np250), dev2 / locked2 (eval_set2/v2, locked_eval2/v2), and the unopened confirmation sets (np096_conf093,
np102_d0conf, c1cost098). Asserts: no missing identity group; a group belongs to exactly one table and one fold; the split rows equal the selection CSVs.
Writes diag/cf107/<tag>_A_fit.csv, <tag>_B_fit.csv, <tag>_all_fit.csv (fit rows = fold rows minus protected groups) and diag/cf107/split.csv
(tag, set, molecule, identity_group, cf, fit_ok). Usage: python -X utf8 cf107_split.py"""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "diag", "cf107"); os.makedirs(OUT, exist_ok=True)
CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv"}
PROTECTED = ["panel_np250/p1_molecules.csv", "eval_set2/v2/p2_molecules.csv", "locked_eval2/v2/p2_molecules.csv", "np096_conf093/p2_molecules.csv",
             "np102_d0conf/p2_molecules.csv", "c1cost098/p2_molecules.csv"]
prot = {}
for p in PROTECTED:
    d = pd.read_csv(os.path.join(HERE, p)); assert d.identity_group.notna().all(), p
    for g in d.identity_group.astype(int): prot.setdefault(int(g), []).append(p)
rows, seen = [], {}
for k, (tag, csv) in enumerate(CSV.items()):
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str)
    assert ev.identity_group.notna().all() and not ev.duplicated(["set", "molecule"]).any(), tag
    groups = sorted(int(g) for g in ev.identity_group.unique()); rng = np.random.default_rng(1070 + k); perm = rng.permutation(len(groups))
    fold = {g: ("A" if perm[i] % 2 == 0 else "B") for i, g in enumerate(groups)}
    for g in groups: assert g not in seen, f"identity group {g} in {seen.get(g)} and {tag}"; seen[g] = tag
    ev["cf"] = ev.identity_group.astype(int).map(fold); ev["fit_ok"] = ~ev.identity_group.astype(int).isin(prot)
    for f in ("A", "B"): ev[(ev.cf == f) & ev.fit_ok].drop(columns=["cf", "fit_ok"]).to_csv(os.path.join(OUT, f"{tag}_{f}_fit.csv"), index=False)
    ev[ev.fit_ok].drop(columns=["cf", "fit_ok"]).to_csv(os.path.join(OUT, f"{tag}_all_fit.csv"), index=False)
    excl = ev[~ev.fit_ok]
    rows.append(ev[["set", "molecule", "identity_group", "cf", "fit_ok"]].assign(tag=tag))
    print(tag, ev.cf.value_counts().to_dict(), "groups", len(groups), "| protected groups excluded from fits:", [(int(g), m, prot[int(g)]) for g, m in zip(excl.identity_group, excl.molecule)])
S = pd.concat(rows, ignore_index=True); assert not S.duplicated(["tag", "set", "molecule"]).any()
S.to_csv(os.path.join(OUT, "split.csv"), index=False); print("split rows", len(S), "fit_ok", int(S.fit_ok.sum()))
