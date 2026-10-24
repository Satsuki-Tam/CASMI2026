"""B1 shared definitions: adduct -> neutral mass, electron-mass convention, scorer identity, entropy similarity.

Ion m/z = M + sum(adduct atoms) -/+ electron (positive: minus m_e, negative: plus m_e). enveda-180 positive-mode m/z carry a +m_e bias
(no electron removed) and are corrected by the caller (subtract ELECTRON before using these formulas).
"""
import numpy as np

ELECTRON = 0.00054858
H, C, N, O, Na, K, Cl = 1.00782503, 12.0, 14.0030740, 15.9949146, 22.9897693, 38.9637067, 34.9688527
H2O = 2 * H + O
# neutral mass M = prec + ADDUCT_SHIFT[adduct]
ADDUCT_SHIFT = {
    "[M+H]+": -(H - ELECTRON),
    "[M+NH4]+": -(N + 4 * H - ELECTRON),
    "[M+Na]+": -(Na - ELECTRON),
    "[M+K]+": -(K - ELECTRON),
    "[M-H2O+H]+": H2O - (H - ELECTRON),
    "[M-2H2O+H]+": 2 * H2O - (H - ELECTRON),
    "[M-H]-": (H - ELECTRON),
    "[M-H2O-H]-": H2O + (H - ELECTRON),
    "[M+CH2O2-H]-": -(C + 2 * H + 2 * O) + (H - ELECTRON),
    "[M+Cl]-": -(Cl + ELECTRON),
}
TEST_ADDUCTS = list(ADDUCT_SHIFT)
POSITIVE = {a for a in ADDUCT_SHIFT if a.endswith("+")}


def neutral_mass(prec, adduct):
    s = ADDUCT_SHIFT.get(adduct)
    return None if s is None else float(prec) + s


# ----------------------------------------------------------------------------------------------- spectral entropy similarity
def clean_peaks(mz, it, prec=None, floor=0.001, top=512, prec_margin=1.5):
    """relative-intensity filter, drop peaks at/above the precursor (minus margin), keep the top-N, L1-normalise."""
    mz = np.asarray(mz, np.float64); it = np.asarray(it, np.float64)
    ok = np.isfinite(mz) & np.isfinite(it) & (it > 0)
    if prec is not None: ok &= mz < float(prec) - prec_margin
    mz, it = mz[ok], it[ok]
    if len(it) == 0: return mz, it
    it = it / it.max(); keep = it >= floor; mz, it = mz[keep], it[keep]
    if len(it) > top:
        idx = np.argpartition(-it, top - 1)[:top]; mz, it = mz[idx], it[idx]
    o = np.argsort(mz); mz, it = mz[o], it[o]
    return mz, it / it.sum()


def entropy_weight(it):
    """Li et al. 2021 entropy weighting: S < 3 -> intensity^(0.25 + 0.25 S), renormalised."""
    p = it / it.sum(); s = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    if s < 3.0:
        w = 0.25 + 0.25 * s; p = p ** w; p = p / p.sum()
    return p


def merge_tolerance(mz_a, ia, mz_b, ib, tol_da=0.01, tol_ppm=20.0):
    """align two sorted peak lists: greedy nearest matching within max(tol_da, tol_ppm) -> aligned intensity vectors."""
    i = j = 0; a_out, b_out = [], []
    while i < len(mz_a) and j < len(mz_b):
        tol = max(tol_da, mz_a[i] * tol_ppm * 1e-6); d = mz_a[i] - mz_b[j]
        if abs(d) <= tol:
            a_out.append(ia[i]); b_out.append(ib[j]); i += 1; j += 1
        elif d < 0:
            a_out.append(ia[i]); b_out.append(0.0); i += 1
        else:
            a_out.append(0.0); b_out.append(ib[j]); j += 1
    while i < len(mz_a): a_out.append(ia[i]); b_out.append(0.0); i += 1
    while j < len(mz_b): a_out.append(0.0); b_out.append(ib[j]); j += 1
    return np.asarray(a_out), np.asarray(b_out)


def entropy_similarity(mz_a, ia, mz_b, ib, tol_da=0.01, tol_ppm=20.0):
    """spectral entropy similarity in [0, 1] of two cleaned (sorted, L1-normalised) spectra."""
    if len(ia) == 0 or len(ib) == 0: return 0.0
    pa, pb = entropy_weight(ia), entropy_weight(ib)
    a, b = merge_tolerance(mz_a, pa, mz_b, pb, tol_da, tol_ppm)
    m = (a + b) / 2.0
    def ent(p):
        p = p[p > 0]; return float(-(p * np.log(p)).sum())
    return max(0.0, min(1.0, 1.0 - (2 * ent(m) - ent(a) - ent(b)) / np.log(4)))
