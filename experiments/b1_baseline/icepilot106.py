"""106 (iii) ICEBERG pilot, step 1: for the SAME fixed subset as the GL pilot (diag/glpilot106/subset.csv), ICEBERG runner inputs restricted to the
candidates of same-formula groups determined from the CANDIDATE structures (RDKit formula of each shortlist candidate of the run table, union of the
views; groups with >= 2 candidates). No label is used. Spectra are those of the GL runner input (b1_runner_<set>_in.json).
Output: diag/icepilot106/in_<tag>_<set>.json. Usage: python -X utf8 icepilot106.py"""
import json, os
from collections import defaultdict
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "diag", "icepilot106"); os.makedirs(OUT, exist_ok=True)
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
SUB = pd.read_csv(os.path.join(HERE, "diag", "glpilot106", "subset.csv")); SUB["molecule"] = SUB.molecule.astype(str)
FORM = {}
def formula(smi):
    if smi not in FORM:
        m = Chem.MolFromSmiles(smi); FORM[smi] = CalcMolFormula(m) if m is not None else None
    return FORM[smi]
for (tag, s), sub in SUB.groupby(["tag", "set"]):
    run = os.path.join(HERE, RUN_OF[tag]); keep = set(sub.molecule)
    items = {str(it["mid"]): it for it in json.load(open(os.path.join(run, f"b1_runner_{s}_in.json"))) if str(it.get("mid")) in keep}
    out, n_c, n_g = [], 0, 0
    for mid, it in sorted(items.items()):
        groups = defaultdict(list)
        for c in it.get("cands") or []:
            f = formula(c)
            if f: groups[f].append(c)
        cands = [c for f, cs in groups.items() if len(cs) >= 2 for c in cs]
        n_g += sum(1 for cs in groups.values() if len(cs) >= 2); n_c += len(cands)
        if cands: out.append(dict(it, cands=cands))
    json.dump(out, open(os.path.join(OUT, f"in_{tag}_{s}.json"), "w"))
    print(f"{tag} {s}: {len(out)} molecules, {n_g} same-formula groups, {n_c} candidates")
