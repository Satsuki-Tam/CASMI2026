"""128 v2 (Codex 128): the ONE definition of a candidate's neutral molecular formula, shared by the evaluator (gen_eval2fd --wf) and the MIST
scorer (experiments/mist/mist_score.py). None = the candidate is never grouped and keeps its position: unparsable SMILES, net formal charge != 0,
or any isotope label. Otherwise RDKit CalcMolFormula of the representative SMILES (no neutralisation, no isotope stripping)."""
from functools import lru_cache
from rdkit import Chem, RDLogger
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")


@lru_cache(maxsize=None)
def neutral_formula(smi):
    m = Chem.MolFromSmiles(smi) if smi else None
    if m is None or Chem.GetFormalCharge(m) != 0 or any(a.GetIsotope() for a in m.GetAtoms()):
        return None
    return CalcMolFormula(m)
