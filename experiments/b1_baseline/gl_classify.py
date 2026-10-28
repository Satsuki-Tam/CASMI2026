"""GLACIER null classification shared by gl_share.py and gl_audit.py (Codex 114). Mirrors gl_runner.py (data/external/glacier, sha in the audit):
  covered query spectrum = gl_runner.is_covered: mode == 1 or str(mode).lower() in ('positive', 'pos', '+', '1'), and adduct in ([M+H]+, [M+Na]+);
  accepted structure     = gl_runner.canon + smiles_ok: RDKit parse, every atom in ms_pred chem_utils.VALID_ELEMENTS, RemoveHs, <= 100 atoms,
                           MolToSmiles, canonical re-parse with > 0 atoms.
classify(item, smiles, value) -> 'finite' | 'null_uncovered' (no covered query spectrum in the molecule) | 'null_rejected' (structure rejected by
the rules above) | 'failure' (missing / non-finite / any other null, incl. an unexpected exception in the check itself).
Run with the runner's environment (.venv-ice, RDKit 2025.03) so the structure rules use the same RDKit."""
import math
COV = ("[M+H]+", "[M+Na]+")
VALID_ELEMENTS = ("C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se", "Fe", "Co", "As", "Na", "K")   # ms_pred/common/chem_utils.py
_ACC = {}


def is_covered(sp):
    md = sp.get("mode")
    pos = (md == 1) or (isinstance(md, str) and md.lower() in ("positive", "pos", "+", "1"))
    return bool(pos and sp.get("adduct") in COV)


def molecule_covered(item):
    return any(is_covered(sp) for sp in item.get("spectra") or [])


def accepted(smi):
    """True / False by the runner's structure rules; None if the check itself raised (never a scheduled null)."""
    if smi in _ACC: return _ACC[smi]
    try:
        from rdkit import Chem, RDLogger
        RDLogger.DisableLog("rdApp.*")
        if not isinstance(smi, str) or not smi: r = False
        else:
            mol = Chem.MolFromSmiles(smi)
            if mol is None: r = False
            else:
                valid = {Chem.Atom(e).GetAtomicNum() for e in VALID_ELEMENTS}
                if any(a.GetAtomicNum() not in valid for a in mol.GetAtoms()): r = False
                else:
                    m2 = Chem.RemoveHs(mol)
                    if m2.GetNumAtoms() > 100: r = False
                    else:
                        mc = Chem.MolFromSmiles(Chem.MolToSmiles(m2)); r = mc is not None and mc.GetNumAtoms() > 0
    except Exception:
        r = None
    _ACC[smi] = r
    return r


def is_finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def classify(item, smi, present, value):
    if not present: return "failure"
    if value is not None: return "finite" if is_finite(value) else "failure"
    if not molecule_covered(item): return "null_uncovered"
    acc = accepted(smi)
    if acc is False: return "null_rejected"
    return "failure"
