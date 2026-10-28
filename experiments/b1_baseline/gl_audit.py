"""Codex 112: GLACIER output audit, a STOP gate before any comparison is read. For every expected (molecule, candidate) of the runner input:
  scheduled null = the molecule has no covered query spectrum (positive mode and adduct [M+H]+ / [M+Na]+, gl_runner's rule), or the candidate is
                   rejected by the runner's canonicalisation (RDKit parse failure, an element outside GLACIER's VALID_ELEMENTS, > 100 heavy atoms after
                   RemoveHs, empty);
  failure        = a missing molecule / candidate key in the output, a non-finite number, or a null that is not scheduled (prediction failed,
                   budget, crash).
Writes <out>.audit.json; exit 1 if any failure. Usage: python gl_audit.py RUN/b1_runner_S_in.json RUN/work/gl_S.json [more pairs ...]"""
import json, math, sys
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")
COV = ("[M+H]+", "[M+Na]+")
VALID = {"C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se", "Fe", "Co", "As", "Na", "K"}   # ms_pred chem_utils.VALID_ELEMENTS (gl_runner canon)
args = sys.argv[1:]
if not args or len(args) % 2: sys.exit("usage: gl_audit.py IN OUT [IN OUT ...]")
bad_total = 0
for inp, outp in zip(args[0::2], args[1::2]):
    items = json.load(open(inp)); out = json.load(open(outp)); c = dict(molecules=len(items), candidates=0, finite=0, null_uncovered=0, null_rejected=0, failure=0)
    fails = []
    for it in items:
        m = it["mid"]; covered = any((str(sp.get("mode")) in ("positive", "1", "+1", "1.0")) and sp.get("adduct") in COV for sp in it.get("spectra", []))
        d = out.get(m)
        for s in it["cands"]:
            c["candidates"] += 1
            if d is None or s not in d: c["failure"] += 1; fails.append((m, s, "missing")); continue
            v = d[s]
            if v is not None:
                if isinstance(v, (int, float)) and math.isfinite(float(v)): c["finite"] += 1
                else: c["failure"] += 1; fails.append((m, s, f"non-finite {v}"))
                continue
            if not covered: c["null_uncovered"] += 1; continue
            mol = Chem.MolFromSmiles(s) if s else None
            if mol is None or mol.GetNumAtoms() == 0 or any(x.GetSymbol() not in VALID for x in mol.GetAtoms()) or Chem.RemoveHs(mol).GetNumAtoms() > 100: c["null_rejected"] += 1; continue
            c["failure"] += 1; fails.append((m, s, "null"))
    c["examples"] = fails[:5]; json.dump(c, open(outp + ".audit.json", "w"), indent=1)
    print(("PASS" if c["failure"] == 0 else "FAIL"), outp, json.dumps({k: v for k, v in c.items() if k != "examples"}), flush=True)
    bad_total += c["failure"]
sys.exit(1 if bad_total else 0)
