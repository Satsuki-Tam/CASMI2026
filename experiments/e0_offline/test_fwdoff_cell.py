"""Offline test of the forward-off REBUILD cell of kernels/e0-probe-fwdoffb (before any push): for each finished E0 offline run, rebuild
PREFUSION_LISTS / ENG from e004_candidate_inputs.json, take metric_identity / safe_extend (cell 16) and metric_fusion (cell 18) by ast,
run the appended cell's text in a scratch copy of the run's four input files, and report its parity counts (asserts inside the cell).
Usage (Spark): python -X utf8 experiments/e0_offline/test_fwdoff_cell.py <scratch dir> <run> [<run> ...]"""
import ast, json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
def defs(path, names):
    t = ast.parse(open(path, encoding="utf-8").read()); keep = [n for n in t.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    keep += [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name in names]
    keep += [n for n in t.body if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "_tautomer_canonicalizer" for x in n.targets)]
    return compile(ast.Module(body=keep, type_ignores=[]), path, "exec")
nb = json.load(open(os.path.join(REPO, "kernels/e0-probe-fwdoffb/casmi26-e0-probe-fwdoffb.ipynb"), encoding="utf-8"))
cell = nb["cells"][-2]["source"]; cell = "".join(cell) if isinstance(cell, list) else cell
assert cell.startswith("# ==== DIAGNOSTIC PROBE (101 (c))")
scratch = sys.argv[1]
for run in sys.argv[2:]:
    w = os.path.join(HERE, "runs", run, "work"); d = os.path.join(scratch, run); os.makedirs(d, exist_ok=True)
    for f in ("submission_reference.csv", "submission_e006_control.csv", "experiment_audit_factorial.csv", "e004_verification.json"):
        shutil.copy(os.path.join(w, f), d)
    inp = json.load(open(os.path.join(w, "e004_candidate_inputs.json")))
    ns = dict(ALPHA=0.6, KRR=3.0, PREFUSION_LISTS={str(k): v for k, v in inp["prefusion"].items()}, ENG={str(k): v for k, v in inp["engine2"].items()})
    exec(defs(os.path.join(HERE, "cells/16.py"), {"canonicalize_smiles_to_ik14", "heavy_atom_composition", "metric_identity", "safe_extend"}), ns)
    exec(defs(os.path.join(HERE, "cells/18.py"), {"metric_fusion"}), ns)
    cwd = os.getcwd(); os.chdir(d)
    try:
        exec(compile(cell, "fwdoff_cell", "exec"), ns)
    finally:
        os.chdir(cwd)
    print("RUN", run, "ok")
