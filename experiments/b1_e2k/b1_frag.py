"""In-silico fragmentation score (MetFrag-lite, own implementation, 2026-10-26) shared by the evaluator probe and the pipeline.

For a candidate structure, fragments are the connected components left after removing one or two bonds of the heavy-atom graph:
one non-ring bond (a bridge), two non-ring bonds, or two bonds of the same SSSR ring (ring opening; kept only if it disconnects).
A fragment's neutral mass is the sum of its heavy atoms (most common isotope) and their attached hydrogens; its ion m/z is
mass + h * H (h in H_SHIFTS) + proton (positive mode) or - proton (negative mode).
Score of a query spectrum = explained intensity fraction: sum over the query's top peaks (below the precursor - 0.5 Da) of
intensity * parsimony(best explaining fragment) / sum of their intensities, parsimony 1.0 for one bond and PARS2 for two bonds;
the candidate's score is the max over the query spectra. Settings follow the held-out ablation reported in the competition forum
(topic 743254: 2-bond cleavages down-weighted x0.6, linear intensity, 0.005 Da, H shifts -2..+3), fixed before any local evaluation.
"""
import numpy as np

H_SHIFTS = (-2, -1, 0, 1, 2, 3)
PARS2, TOL_DA, TOP_PEAKS, MAX_BONDS = 0.6, 0.005, 40, 120
PROTON = 1.007276; HMASS = 1.00782503207
_CACHE = {}


def _components(n, adj, removed):
    lab = [-1] * n; out = []
    for s in range(n):
        if lab[s] >= 0: continue
        lab[s] = len(out); members = [s]; stack = [s]
        while stack:
            u = stack.pop()
            for v, k in adj[u]:
                if lab[v] >= 0 or k in removed: continue
                lab[v] = lab[s]; members.append(v); stack.append(v)
        out.append(members)
    return out


def fragments(smiles):
    """-> (masses ndarray, n_breaks ndarray): unique fragment neutral masses (rounded 1e-4) with their minimal break count; None if unusable."""
    if smiles in _CACHE: return _CACHE[smiles]
    from rdkit import Chem
    m = Chem.MolFromSmiles(smiles) if smiles else None
    if m is None or m.GetNumBonds() == 0 or m.GetNumBonds() > MAX_BONDS:
        _CACHE[smiles] = None; return None
    pt = Chem.GetPeriodicTable(); n = m.GetNumAtoms()
    am = np.array([pt.GetMostCommonIsotopeMass(a.GetAtomicNum()) + a.GetTotalNumHs() * HMASS for a in m.GetAtoms()])
    adj = [[] for _ in range(n)]
    for b in m.GetBonds():
        i, j, k = b.GetBeginAtomIdx(), b.GetEndAtomIdx(), b.GetIdx(); adj[i].append((j, k)); adj[j].append((i, k))
    bridges = [b.GetIdx() for b in m.GetBonds() if not b.IsInRing()]
    rings = [list(r) for r in m.GetRingInfo().BondRings()]
    best = {}

    def add(cs, nbr):
        if len(cs) < 2: return
        for c in cs:
            if len(c) == n: continue
            mm = round(float(am[c].sum()), 4)
            if best.get(mm, 9) > nbr: best[mm] = nbr
    for k in bridges: add(_components(n, adj, {k}), 1)
    for x in range(len(bridges)):
        for y in range(x + 1, len(bridges)): add(_components(n, adj, {bridges[x], bridges[y]}), 2)
    for r in rings:
        for x in range(len(r)):
            for y in range(x + 1, len(r)): add(_components(n, adj, {r[x], r[y]}), 2)
    if not best:
        _CACHE[smiles] = None; return None
    ks = np.array(sorted(best)); out = (ks, np.array([best[x] for x in ks]))
    if len(_CACHE) < 300_000: _CACHE[smiles] = out
    return out


def score(frag, spectra):
    """frag = fragments(smiles); spectra = list of dicts (mz, it, prec, mode). Returns the max explained-intensity fraction (0 if unusable)."""
    if frag is None: return 0.0
    masses, nbr = frag; best = 0.0
    shifts = np.array(H_SHIFTS, float) * HMASS; wfrag = np.where(nbr == 1, 1.0, PARS2)
    for s in spectra:
        mz = np.asarray(s["mz"], float); it = np.asarray(s["it"], float); prec = float(s["prec"])
        ok = np.isfinite(mz) & np.isfinite(it) & (it > 0) & (mz < prec - 0.5)
        mz, it = mz[ok], it[ok]
        if not len(mz): continue
        if len(mz) > TOP_PEAKS:
            o = np.argsort(-it)[:TOP_PEAKS]; mz, it = mz[o], it[o]
        sign = 1.0 if s.get("mode", "positive") in ("positive", 1, "1", "+") else -1.0
        ions = (masses[:, None] + shifts[None, :] + sign * PROTON).ravel(); w = np.repeat(wfrag, len(shifts))
        o = np.argsort(ions); ions, w = ions[o], w[o]
        lo = np.searchsorted(ions, mz - TOL_DA, "left"); hi = np.searchsorted(ions, mz + TOL_DA, "right")
        expl = np.array([w[a:b].max() if b > a else 0.0 for a, b in zip(lo, hi)])
        best = max(best, float((it * expl).sum() / it.sum()))
    return best
