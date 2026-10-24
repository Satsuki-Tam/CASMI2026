"""Local reproduction of the official CASMI 2026 scorer (MRR@25).

Adapted from the Kaggle metric notebook `metric/casmi-mean-reciprocal-rank`
(see reference/kernels/metric_casmi-mean-reciprocal-rank/). The only change is that RDKit is
imported directly instead of being installed from the offline wheel.

Identity used by the scorer:  strip stereo -> RDKit TautomerEnumerator().Canonicalize -> InChIKey[:14]
RDKit must be 2026.03.3 (pinned in the venv) or keys may differ from the official ones.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import rdkit
from rdkit import Chem, RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize

EXPECTED_RDKIT_VERSION = "2026.03.3"
RDLogger.DisableLog("rdApp.*")
if rdkit.__version__ != EXPECTED_RDKIT_VERSION:
    warnings.warn(
        f"RDKit version mismatch: official scorer={EXPECTED_RDKIT_VERSION}, local={rdkit.__version__}. "
        "Canonicalization may differ.",
        UserWarning,
    )
_tautomer_canonicalizer = rdMolStandardize.TautomerEnumerator()


class ParticipantVisibleError(Exception):
    pass


class HostVisibleError(Exception):
    pass


def canonicalize_smiles_to_ik14(smiles: str) -> str | None:
    """SMILES -> scorer identity key (tautomer-canonical InChIKey14), or None if unparsable."""
    if not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        Chem.RemoveStereochemistry(mol)
        canonical_mol = _tautomer_canonicalizer.Canonicalize(mol)
        return Chem.MolToInchiKey(canonical_mol)[:14]
    except (ValueError, RuntimeError, TypeError):
        return None


def heavy_atom_composition(smiles: str):
    """Heavy-atom element counts as a hashable key (cheap gate before canonicalization)."""
    mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    if mol is None:
        return None
    counts: dict[str, int] = {}
    for atom in mol.GetAtoms():
        sym = atom.GetSymbol()
        if sym != "H":
            counts[sym] = counts.get(sym, 0) + 1
    return tuple(sorted(counts.items()))


def score(solution: pd.DataFrame, submission: pd.DataFrame, row_id_column_name: str = "molecule_id",
          max_rank: int = 25) -> float:
    """Official MRR@max_rank. `solution` has columns molecule_id, smiles (comma-separated accepted answers).

    >>> sol = pd.DataFrame({'molecule_id': ['m_1', 'm_2'], 'smiles': ['CCO', 'c1ccccc1']})
    >>> score(sol, pd.DataFrame({'molecule_id': ['m_1', 'm_2'], 'smiles': ['CCO;CC(=O)O', 'CC(=O)O;c1ccccc1']}))
    0.75
    >>> score(sol, pd.DataFrame({'molecule_id': ['m_1', 'm_2'], 'smiles': ['CC(=O)O', 'c1ccccc1;c1ccccc1;c1ccccc1']}))
    0.5
    >>> score(pd.DataFrame({'molecule_id': ['m_1'], 'smiles': ['C[C@H](N)C(=O)O']}),
    ...       pd.DataFrame({'molecule_id': ['m_1'], 'smiles': ['CC(N)C(=O)O']}))
    1.0
    >>> score(pd.DataFrame({'molecule_id': ['m_1'], 'smiles': ['C=C(C)C1CCC2CCC(=O)C=C2C1']}),
    ...       pd.DataFrame({'molecule_id': ['m_1'], 'smiles': ['C=C(C)[C@@H]1CCC2CCC(=O)C=C2C1']}))
    1.0
    """
    if not isinstance(max_rank, (int, np.integer)) or max_rank < 1:
        raise ValueError(f"max_rank must be a positive integer, got {max_rank!r}")
    required = ["molecule_id", "smiles"]
    if not all(c in submission.columns for c in required):
        raise ParticipantVisibleError(f"Missing columns: {required}")
    if len(submission) == 0:
        raise ParticipantVisibleError("Submission is empty")
    if submission[required].isna().any().any():
        raise ParticipantVisibleError("NaN in required columns")
    if "smiles" not in solution.columns:
        raise ParticipantVisibleError("Solution missing smiles column")
    if submission["molecule_id"].duplicated().any():
        raise ParticipantVisibleError("Each molecule_id must appear exactly once")

    guesses_by_molecule = {}
    for molecule_id, raw_guesses in zip(submission["molecule_id"], submission["smiles"]):
        parsed = [c.strip() for c in str(raw_guesses).split(";")]
        parsed = [c for c in parsed if c]
        if not parsed:
            raise ParticipantVisibleError(f"No guesses for molecule_id {molecule_id}")
        if len(parsed) > max_rank:
            raise ParticipantVisibleError(
                f"At most {max_rank} semicolon-separated guesses per molecule_id, got {len(parsed)} for {molecule_id}")
        guesses_by_molecule[molecule_id] = parsed

    gate_keys = {s: heavy_atom_composition(s) for guesses in guesses_by_molecule.values() for s in guesses}

    unknown_ids = set(submission["molecule_id"]) - set(solution["molecule_id"])
    if unknown_ids:
        print(f"Unknown molecule_ids: {sorted(unknown_ids)[:5]}{'...' if len(unknown_ids) > 5 else ''}")

    sol_dict = {}
    for _, row in solution.iterrows():
        molecule_id = row["molecule_id"]
        accept_smiles = row["smiles"] if isinstance(row["smiles"], str) else ""
        candidates = [s for s in accept_smiles.split(",") if s]
        if not candidates:
            raise HostVisibleError(f"Solution has no answer SMILES for molecule_id {molecule_id}")
        accept_ik14s = {k for k in map(canonicalize_smiles_to_ik14, candidates) if k}
        accept_keys = {k for k in map(heavy_atom_composition, candidates) if k}
        if not accept_ik14s or not accept_keys:
            raise HostVisibleError(f"Solution SMILES for molecule_id {molecule_id} could not be parsed: {accept_smiles!r}")
        sol_dict[molecule_id] = (accept_ik14s, accept_keys)

    canon_cache: dict[str, str | None] = {}

    def canon(smiles):
        if smiles not in canon_cache:
            canon_cache[smiles] = canonicalize_smiles_to_ik14(smiles)
        return canon_cache[smiles]

    scores = []
    for mol_id, (acceptable, accept_keys) in sol_dict.items():
        rr = 0.0
        for rank, guess in enumerate(guesses_by_molecule.get(mol_id, []), 1):
            if gate_keys[guess] not in accept_keys:
                continue
            if canon(guess) in acceptable:
                rr = 1.0 / rank
                break
        scores.append(rr)
    return float(np.mean(scores))


def per_molecule_reciprocal_rank(answer_smiles: str, guesses: list[str], max_rank: int = 25) -> float:
    """Convenience helper for local validation: reciprocal rank of one molecule."""
    target = canonicalize_smiles_to_ik14(answer_smiles)
    if target is None:
        raise HostVisibleError(f"Unparsable answer: {answer_smiles!r}")
    for rank, g in enumerate(guesses[:max_rank], 1):
        if canonicalize_smiles_to_ik14(g) == target:
            return 1.0 / rank
    return 0.0


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False))
    # stored inchikey14 vs scorer key example from the data notebook (carvone)
    print("carvone scorer key:", canonicalize_smiles_to_ik14("CC1=CCC(CC1=O)C(=C)C"), "(expected YAHNGTQFNICUIJ; stored column has ULDHMXUKGWMISQ)")
    print("2-pyridone / 2-hydroxypyridine:", canonicalize_smiles_to_ik14("O=c1cccc[nH]1"), canonicalize_smiles_to_ik14("Oc1ccccn1"))
