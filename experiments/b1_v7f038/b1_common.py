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


# ---------------------------------------------------------------------------------------------------------------------------------
# Forward-model adduct proxies (2026-10-25). The MassSpecGym ICEBERG/GLACIER checkpoints cover positive [M+H]+ / [M+Na]+ only, so a
# molecule without such a spectrum gets no forward evidence (panel enveda-np-examples: 34/250; 16 of them have an [M+NH4]+ spectrum,
# 18 are negative-only). The public lineage's N1A arm A (LB-validated, +0.027 [0.010, 0.047] on its NP bench) scores [M+NH4]+ and
# [M-H2O+H]+ spectra of such molecules as [M+H]+ proxies; proxies where a real [M+H]+ exists HURT (-0.047) and are never made.
#   [M+NH4]+   : M = prec - 18.033823 (NH4+), drop peaks >= M + 1.007276 - 1.5 (the adduct/precursor region), precursor -> M + 1.007276
#   [M-H2O+H]+ : M = prec + 18.010565 - 1.007276, keep peaks < prec - 1.5, precursor -> M + 1.007276
#   [M-2H2O+H]+, [M+K]+, [M+Na]+ : never (as in the public lineage)
# neg=True (EXPERIMENTAL, not LB-validated): negative-mode spectra mapped onto the positive axis (deprotonated fragment F-H -> F+H:
# m/z + 2*1.007276), precursor -> M + 1.007276. Fragmentation chemistry differs between modes; use only after a paired test.
PROTON_MASS = 1.007276; NH4_ION = 18.033823; H2O_MASS = 18.010565
NEG_NEUTRAL = {"[M-H]-": lambda p: p + PROTON_MASS, "[M-H2O-H]-": lambda p: p + PROTON_MASS + H2O_MASS, "[M+CH2O2-H]-": lambda p: p - (46.005480 - PROTON_MASS),
               "[M+Cl]-": lambda p: p - 34.969402}


def _is_positive(s):
    md = s.get("mode")
    return md in (1, "1", "positive", "pos", "+")


def forward_proxies(spectra, covered=("[M+H]+", "[M+Na]+"), neg=False):
    """spectra: list of dicts with mz, it, prec, adduct, mode (+ any other keys, copied). Returns the list of proxy spectra (possibly empty)."""
    if any(_is_positive(s) and s.get("adduct") in covered for s in spectra): return []
    out = []
    for s in spectra:
        mz = np.asarray(s["mz"], float); it = np.asarray(s["it"], float); add = s.get("adduct"); prec = float(s["prec"])
        if _is_positive(s) and add == "[M+NH4]+":
            newp = prec - NH4_ION + PROTON_MASS; keep = mz < newp - 1.5; shift = 0.0; kind = "nh4"
        elif _is_positive(s) and add == "[M-H2O+H]+":
            newp = prec + H2O_MASS; keep = mz < prec - 1.5; shift = 0.0; kind = "h2o"
        elif neg and (not _is_positive(s)) and add in NEG_NEUTRAL:
            newp = NEG_NEUTRAL[add](prec) + PROTON_MASS; shift = 2 * PROTON_MASS; keep = (mz + shift) < newp - 1.5; kind = "neg"
        else: continue
        if keep.sum() < 2: continue
        p = dict(s); p.update(mz=(mz[keep] + shift).tolist(), it=it[keep].tolist(), prec=float(newp), adduct="[M+H]+", mode="positive", proxy=kind, proxy_from=add)
        out.append(p)
    return out


def select_queries(items, max_q, adduct_of, ce_of):
    """Query-spectrum selection shared by the evaluator (b1_features), the submission pipeline and the test builder (make_eval_test), Codex 015 (c).
    items: candidate spectra (test adducts only) in a deterministic order that is the final tie-break (store row / test-file order).
    Order within an adduct: collision energy (unknown/NaN -> 0.0), then input order. Adduct order: [M+H]+ first, then by adduct name.
    Selection: round-robin over adducts (first spectrum of each adduct, then the second, ...) until max_q. Returns the selected items in that order."""
    def ce_key(x):
        c = ce_of(x)
        return 0.0 if c is None or c != c else float(c)
    bad = [adduct_of(x) for x in items if adduct_of(x) not in ADDUCT_SHIFT]
    assert not bad, f"select_queries: non-test adducts passed by the caller: {sorted(set(bad))[:5]}"
    by_add = {}
    for x in sorted(items, key=lambda x: (adduct_of(x) != "[M+H]+", adduct_of(x), ce_key(x))):
        by_add.setdefault(adduct_of(x), []).append(x)
    q = []
    while len(q) < max_q and any(by_add.values()):
        for ad in list(by_add):
            if by_add[ad] and len(q) < max_q: q.append(by_add[ad].pop(0))
    return q
