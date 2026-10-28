# Are solution SMILES stereo-stripped like train normalized_smiles?
topic 744556 | by **Yohann Roux** (https://www.kaggle.com/yohannroux) | posted 2026-09-30 | votes 1 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/744556

Hi, a quick question for the organizers: are the reference SMILES in the hidden test set written without stereochemistry, like normalized_smiles in train.parquet?

I ask because the metric's key (InChIKey14 after RDKit tautomer canonicalization) can differ for the same molecule depending on whether stereochemistry is written or not. Minimal example with RDKit 2026.03.3:

from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

te = rdMolStandardize.TautomerEnumerator()
key = lambda s: Chem.MolToInchiKey(te.Canonicalize(Chem.MolFromSmiles(s)))[:14]

with_stereo = "C=C1C[C@@H](OC(=O)[C@@]2(C)O[C@H]2C)[C@H]2C(=C)C(=O)O[C@@H]2[C@H]2C(C)=CC(=O)[C@@H]12"
without     = "C=C1CC(OC(=O)C2(C)OC2C)C2C(=C)C(=O)OC2C2C(C)=CC(=O)C12"
print(key(with_stereo), key(without))  # KOJSSZPTECJRNW SRMRLHNLDDQJLJ

Both SMILES share the same standard InChIKey first block (DBYQNZJJUBKANY), but get different metric keys. So a correct structure could be scored as wrong depending on how it is written. Could you confirm how the solution SMILES are normalized, or whether several spellings are accepted in such cases?

Thanks!

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-09-30, votes 0)
  Great point!  Yes, solutions are stereo-stripped before canonicalization.
