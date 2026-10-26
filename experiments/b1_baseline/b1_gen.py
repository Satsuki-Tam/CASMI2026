"""Analog-derivative candidate generation (own implementation, 2026-10-26) for molecules absent from every structure database (class 3).

A parent structure P (a train analog chosen by spectral similarity) and the target neutral mass M give d = M - mass(P). Every one- or
two-step combination of the biosynthetic edits below whose exact-mass change equals d (|error| <= TOL Da) is applied at every
matching site of P (RDKit reaction SMARTS); the products (unique InChIKey first blocks) are the generated candidates.
The edit list is written from natural-product biosynthesis (oxidation/reduction, O/N/C-methylation, glycosylation with the common
plant sugars, acylation with the common plant acyl units, prenylation, sulfation, and the reverse edits); the same idea is used by the
public lineage (analog derivatives), the list and the code here are our own.
"""
import itertools
import numpy as np

TOL, MAX_STEPS, MAX_PRODUCTS = 0.003, 2, 400
M_ = dict(C=12.0, H=1.00782503207, O=15.99491461956, N=14.0030740048, S=31.97207100, Cl=34.96885268)

# name: (reaction SMARTS, formula change)
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
# the formula changes above are the net change of the molecule (removed/added H atoms included)


def _mass(d):
    return float(sum(M_[e] * n for e, n in d.items()))


_RXN, _COMBOS = {}, None


def _rxn(name):
    if name not in _RXN:
        from rdkit.Chem import AllChem
        _RXN[name] = AllChem.ReactionFromSmarts(EDITS[name][0])
    return _RXN[name]


def combos():
    global _COMBOS
    if _COMBOS is None:
        names = sorted(EDITS); out = [((n,), _mass(EDITS[n][1])) for n in names]
        for a, b in itertools.combinations_with_replacement(names, 2):
            d = dict(EDITS[a][1])
            for e, v in EDITS[b][1].items(): d[e] = d.get(e, 0) + v
            out.append(((a, b), _mass(d)))
        _COMBOS = out
    return _COMBOS


def matching(delta, tol=TOL, max_steps=MAX_STEPS):
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


def derive(smiles, delta, tol=TOL, max_steps=MAX_STEPS, max_products=MAX_PRODUCTS):
    """-> {smiles: combo} products of `smiles` whose exact mass differs by ~delta (neutral isomerisation pairs when delta ~ 0)."""
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None: return {}
    out, budget = {}, 600
    for combo in matching(delta, tol, max_steps):
        mols = [mol]
        for depth, name in enumerate(combo):
            nxt = []
            for m in mols[:24]:
                nxt.extend(_apply(m, name, 32 if depth == 0 else 12)); budget -= 1
                if budget <= 0: break
            mols = nxt
            if not mols or budget <= 0: break
        for m in mols:
            s = Chem.MolToSmiles(m)
            if s != smiles and s not in out: out[s] = combo
        if len(out) >= max_products or budget <= 0: break
    return out
