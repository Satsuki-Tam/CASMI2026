"""Codex 124 (queue after ENG_B / pre-rank2_B): DIAGNOSTIC probe kernels of the CURRENT working baseline v8w7a (Public 0.394, submission
57716320, kernel hayatetaf/casmi26-b1-fpnet-v8w7a v1, unchanged) with the SAME appended extraction cell as kernels/make_e0_probe.py (055/049
definition: final list restricted to one provenance group, T-priority, order kept, no refill, empty -> CCO). The cell text is taken from
make_e0_probe.py with ast (byte-identical extraction), not re-typed. B = the current B-path difference vs E0_B 0.259 (the old 0.204 was the
0.379 version); T = the current control for the T pair. Not method candidates. Build only; push / commit run / submit need the user's permission.
Usage: python -X utf8 kernels/make_b1_v8w7a_probe.py   (writes kernels/b1-probe-bv8w7a and kernels/b1-probe-tv8w7a)
"""
import ast, copy, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
tree = ast.parse(open(os.path.join(HERE, "make_e0_probe.py"), encoding="utf-8").read())
CELL = next(n.value.value for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "CELL" for t in n.targets))
assert "PROBE_GROUP = '__GROUP__'" in CELL and "_sub = _pd.read_csv('submission.csv')" in CELL
SRC_DIR, SRC_NB = "b1-fpnet-v8w7a", "casmi26-b1-fpnet-v8w7a.ipynb"
for name, g in (("casmi26-b1-probe-bv8w7a", "B"), ("casmi26-b1-probe-tv8w7a", "T")):
    nb = json.load(open(os.path.join(HERE, SRC_DIR, SRC_NB), encoding="utf-8"))
    meta = json.load(open(os.path.join(HERE, SRC_DIR, "kernel-metadata.json"), encoding="utf-8"))
    out_dir = os.path.join(HERE, name.replace("casmi26-", "")); os.makedirs(out_dir, exist_ok=True)
    nb2 = copy.deepcopy(nb)
    nb2["cells"].append(dict(cell_type="markdown", metadata={}, source=[f"## DIAGNOSTIC probe {g} (Codex 049/124): the v8w7a final list restricted to provenance group {g}; not a method candidate."]))
    nb2["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=CELL.replace("__GROUP__", g)))
    json.dump(nb2, open(os.path.join(out_dir, f"{name}.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb"), open(os.path.join(out_dir, "kernel-metadata.json"), "w", encoding="utf-8"), indent=2)
    print("wrote", out_dir, "from", SRC_DIR, "group", g)
