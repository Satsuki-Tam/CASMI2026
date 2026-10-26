"""Analog-derivative candidate generation (own implementation; v2 2026-10-26 after Codex 042) for structures absent from the databases.

A parent structure P (a train analog chosen by spectral similarity) and the target neutral mass M (from the query precursor m/z and
adduct, never from a label) give d = M - mass(P). Every one-step edit and every ordered two-step combination of the biosynthetic edits
below (both orders of two different edits) whose formula change equals d within the tolerance is applied at every matching site of P
(RDKit reaction SMARTS). A product is kept only if its own exact mass is within the tolerance of M (the SMARTS can match larger groups
than the declared formula change, e.g. a substituted sugar). Tolerance = max(TOL_MIN Da, TOL_PPM ppm of M) (10 ppm = the B1 window).
The edit list is written from natural-product biosynthesis (oxidation/reduction, O/N/C-methylation, glycosylation with the common plant
sugars, acylation with the common plant acyl units, prenylation, sulfation, and the reverse edits); the same idea is used by the public
lineage (analog derivatives), the list and the code here are our own.
v2 changes (Codex 042): product exact-mass check, both orders of two-step edits, strict caps, official keys for de-duplication.
"""
import itertools

TOL_PPM, TOL_MIN, MAX_STEPS, MAX_PER_PARENT, BUDGET = 10.0, 0.002, 2, 300, 600
CAP_STEP1, CAP_STEP2, MAX_INTERMEDIATES = 32, 12, 24
M_ = dict(C=12.0, H=1.00782503207, O=15.99491461956, N=14.0030740048, S=31.97207100, Cl=34.96885268)

# name: (reaction SMARTS, net formula change of the molecule)
EDITS = {
    "OH_ar": ("[cH:1]>>[c:1]O", dict(O=1)),
    "OH_al": ("[CX4;H1,H2,H3;!$(C[OX2H]):1]>>[C:1]O", dict(O=1)),
    "Me_O": ("[OX2H;!$(OC=O):1]>>[O:1]C", dict(C=1, H=2)),
    "Me_N": ("[NX3;H1,H2;!$(NC=O):1]>>[N:1]C", dict(C=1, H=2)),
    "Me_c": ("[cH:1]>>[c:1]C", dict(C=1, H=2)),
    "OMe_ar": ("[cH:1]>>[c:1]OC", dict(C=1, H=2, O=1)),
    "Ac_O": ("[OX2H;!$(OC=O):1]>>[O:1]C(C)=O", dict(C=2, H=2, O=1)),
    "Mal_O": ("[OX2H;!$(OC=O):1]>>[O:1]C(=O)CC(=O)O", dict(C=3, H=2, O=3)),
    "Hex_O": ("[OX2H;!$(OC=O):1]>>[O:1]C1OC(CO)C(O)C(O)C1O", dict(C=6, H=10, O=5)),
    "Pen_O": ("[OX2H;!$(OC=O):1]>>[O:1]C1OCC(O)C(O)C1O", dict(C=5, H=8, O=4)),
    "dHex_O": ("[OX2H;!$(OC=O):1]>>[O:1]C1OC(C)C(O)C(O)C1O", dict(C=6, H=10, O=4)),
    "GlcA_O": ("[OX2H;!$(OC=O):1]>>[O:1]C1OC(C(=O)O)C(O)C(O)C1O", dict(C=6, H=8, O=6)),
    "Hex_C": ("[cH:1]>>[c:1]C1OC(CO)C(O)C(O)C1O", dict(C=6, H=10, O=5)),
    "SO3_O": ("[OX2H;!$(OC=O):1]>>[O:1]S(=O)(=O)O", dict(S=1, O=3)),
    "Pre_c": ("[cH:1]>>[c:1]CC=C(C)C", dict(C=5, H=8)),
    "Pre_O": ("[OX2H;!$(OC=O):1]>>[O:1]CC=C(C)C", dict(C=5, H=8)),
    "Cou_O": ("[OX2H;!$(OC=O):1]>>[O:1]C(=O)C=Cc1ccc(O)cc1", dict(C=9, H=6, O=2)),
    "Caf_O": ("[OX2H;!$(OC=O):1]>>[O:1]C(=O)C=Cc1ccc(O)c(O)c1", dict(C=9, H=6, O=3)),
    "Fer_O": ("[OX2H;!$(OC=O):1]>>[O:1]C(=O)C=Cc1ccc(O)c(OC)c1", dict(C=10, H=8, O=3)),
    "Gal_O": ("[OX2H;!$(OC=O):1]>>[O:1]C(=O)c1cc(O)c(O)c(O)c1", dict(C=7, H=4, O=4)),
    "H2_CC": ("[C:1]=[C:2]>>[C:1][C:2]", dict(H=2)),
    "H2_CO": ("[C:1]=[O:2]>>[C:1][O:2]", dict(H=2)),
    "dH2_CC": ("[CX4;H1,H2:1][CX4;H1,H2:2]>>[C:1]=[C:2]", dict(H=-2)),
    "ox_CHOH": ("[CX4;H1,H2:1][OX2H:2]>>[C:1]=[O:2]", dict(H=-2)),
    "COOH_Me": ("[CH3:1]>>[C:1](=O)O", dict(O=2, H=-2)),
    "dMe_O": ("[O:1][CH3]>>[O:1]", dict(C=-1, H=-2)),
    "dMe_N": ("[N:1][CH3]>>[N:1]", dict(C=-1, H=-2)),
    "dOH_ar": ("[c:1][OX2H]>>[c:1]", dict(O=-1)),
    "dOH_al": ("[CX4:1][OX2H]>>[C:1]", dict(O=-1)),
    "dAc_O": ("[O:1]C(=O)[CH3]>>[O:1]", dict(C=-2, H=-2, O=-1)),
    "dHex_glyc": ("[O:1]C1OC(CO)C(O)C(O)C1O>>[O:1]", dict(C=-6, H=-10, O=-5)),
    "dPen_glyc": ("[O:1]C1OCC(O)C(O)C1O>>[O:1]", dict(C=-5, H=-8, O=-4)),
    "ddHex_glyc": ("[O:1]C1OC(C)C(O)C(O)C1O>>[O:1]", dict(C=-6, H=-10, O=-4)),
    "dSO3": ("[O:1]S(=O)(=O)[OX2H]>>[O:1]", dict(S=-1, O=-3)),
    "dPre_c": ("[c:1]CC=C(C)C>>[c:1]", dict(C=-5, H=-8)),
    "dCOOH": ("[C,c:1]C(=O)[OX2H]>>[C,c:1]", dict(C=-1, O=-2)),
}


def _mass(d):
    return float(sum(M_[e] * n for e, n in d.items()))


def tol_for(M):
    return max(TOL_MIN, float(M) * TOL_PPM * 1e-6)


_RXN, _COMBOS, _TAUT = {}, None, None


def _rxn(name):
    if name not in _RXN:
        from rdkit.Chem import AllChem
        _RXN[name] = AllChem.ReactionFromSmarts(EDITS[name][0])
    return _RXN[name]


def combos():
    """one-step edits and ordered two-step combinations (both orders of two different edits)."""
    global _COMBOS
    if _COMBOS is None:
        names = sorted(EDITS); out = [((n,), _mass(EDITS[n][1])) for n in names]
        for a, b in itertools.combinations_with_replacement(names, 2):
            m = _mass(EDITS[a][1]) + _mass(EDITS[b][1])
            out.append(((a, b), m))
            if a != b: out.append(((b, a), m))
        _COMBOS = out
    return _COMBOS


def matching(delta, tol, max_steps=MAX_STEPS):
    return [c for c, m in combos() if abs(m - delta) <= tol and len(c) <= max_steps]


def _apply(mol, name, cap):
    from rdkit import Chem
    out, seen = [], set()
    try:
        prods = _rxn(name).RunReactants((mol,))
    except Exception:
        return out
    for p in prods:
        m = p[0]
        try:
            Chem.SanitizeMol(m); s = Chem.MolToSmiles(m)
        except Exception:
            continue
        if s in seen: continue
        seen.add(s); out.append(m)
        if len(out) >= cap: break
    return out


def official_key(smiles):
    """scorer identity (RemoveStereochemistry -> TautomerEnumerator.Canonicalize -> InChIKey[:14]), as src/metric.py."""
    global _TAUT
    from rdkit import Chem
    from rdkit.Chem.MolStandardize import rdMolStandardize
    if _TAUT is None: _TAUT = rdMolStandardize.TautomerEnumerator()
    try:
        m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
        if m is None: return None
        Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(_TAUT.Canonicalize(m))[:14]
    except (ValueError, RuntimeError, TypeError):
        return None


def derive(smiles, target_mass, tol=None, max_steps=MAX_STEPS, max_products=MAX_PER_PARENT):
    """-> {product smiles: combo} for products of `smiles` whose exact mass is within tol of target_mass (strict cap max_products)."""
    from rdkit import Chem
    from rdkit.Chem.Descriptors import ExactMolWt
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None: return {}
    tol = tol_for(target_mass) if tol is None else tol
    parent = Chem.MolToSmiles(mol); out, budget = {}, BUDGET
    for combo in matching(target_mass - ExactMolWt(mol), tol, max_steps):
        mols = [mol]
        for depth, name in enumerate(combo):
            nxt = []
            for m in mols[:MAX_INTERMEDIATES]:
                nxt.extend(_apply(m, name, CAP_STEP1 if depth == 0 else CAP_STEP2)); budget -= 1
                if budget <= 0: break
            mols = nxt
            if not mols or budget <= 0: break
        for m in mols:
            s = Chem.MolToSmiles(m)
            if s == parent or s in out: continue
            if abs(ExactMolWt(m) - target_mass) > tol: continue   # the edit matched a larger group than declared
            out[s] = combo
            if len(out) >= max_products: return out
        if budget <= 0: break
    return out
