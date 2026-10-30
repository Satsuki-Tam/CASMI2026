"""Library-analog channel shared by the evaluator probe (analog_probe.py) and the submission pipeline (b1_pipeline.py --analog_w).

Idea (public analog-propagation baseline; own implementation, 2026-10-26): train spectra similar to the query spectrum (the reference
peaks may also be shifted by the precursor difference = modified-cosine idea) are analogs; a candidate is scored by its Morgan Tanimoto
similarity to the analog structures, weighted by the spectral similarity:
    ap = max_a tan(c, a) * sim_a^3        (other features: a1 = max tan*sim, best_tan, top_tan, mean_tan = sum tan sim^3 / sum sim^3)
Reference store: up to `reps` representative spectra per (official key, polarity) among the test adducts (preference [M+H]+ / [M-H]-,
collision energy closest to 35 eV, store row), cleaned like B1 (clean_peaks floor/top) and entropy-weighted once, sorted by neutral mass.
Masks (evaluation views, as b1_features): query rows never; `drop_keys` removed entirely (C2: truth key + identity group); `relib` =
(key, library): that key's representatives are re-selected from its spectra outside that library (C1: the truth's own library).
"""
import numpy as np
from numba import njit, prange
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_weight

N_ANALOG, WIN, REPS, TOP, FLOOR, SIM_POW = 80, 200.0, 3, 64, 0.005, 3.0


@njit(cache=True, fastmath=True)
def _sim(qmz, qp, qS, rmz, rp, rS, shift):
    i = 0; j = 0; n = len(qmz); m = len(rmz); Sm = 0.0
    while i < n and j < m:
        rm = rmz[j] + shift; tol = max(0.01, qmz[i] * 20e-6); d = qmz[i] - rm
        if abs(d) <= tol:
            v = 0.5 * (qp[i] + rp[j]); i += 1; j += 1
        elif d < 0:
            v = 0.5 * qp[i]; i += 1
        else:
            v = 0.5 * rp[j]; j += 1
        if v > 0: Sm -= v * np.log(v)
    while i < n:
        v = 0.5 * qp[i]; i += 1
        if v > 0: Sm -= v * np.log(v)
    while j < m:
        v = 0.5 * rp[j]; j += 1
        if v > 0: Sm -= v * np.log(v)
    s = 1.0 - (2.0 * Sm - qS - rS) / np.log(4.0)
    return min(1.0, max(0.0, s))


@njit(cache=True, fastmath=True, parallel=True)
def _search(qmz, qp, qS, qprec, lo, hi, roff, rmz, rp, rS, rprec):
    out = np.zeros(hi - lo, np.float32)
    for k in prange(hi - lo):
        r = lo + k; s0 = _sim(qmz, qp, qS, rmz[roff[r]:roff[r + 1]], rp[roff[r]:roff[r + 1]], rS[r], 0.0)
        sh = qprec - rprec[r]
        if abs(sh) > 0.001:
            s1 = _sim(qmz, qp, qS, rmz[roff[r]:roff[r + 1]], rp[roff[r]:roff[r + 1]], rS[r], sh)
            if s1 > s0: s0 = s1
        out[k] = s0
    return out


def sim_pair(q, r):
    """shifted entropy similarity of two prepared spectra (mz, p, S, prec)."""
    s0 = _sim(q[0], q[1], q[2], r[0], r[1], r[2], 0.0); sh = q[3] - r[3]
    if abs(sh) > 0.001: s0 = max(s0, _sim(q[0], q[1], q[2], r[0], r[1], r[2], sh))
    return s0


class Store:
    """representative reference spectra; `row_info(x)` -> (lib, adduct, mode, ce, key) and `spectrum(x)` -> (mz, it) supplied by the caller."""

    def __init__(self, rows, lib, add, mode, ce, key, prec, spectrum, reps=REPS, top=TOP, floor=FLOOR, log=print):
        self.lib, self.add, self.mode, self.ce, self.key, self.prec, self.spectrum = lib, add, mode, ce, key, prec, spectrum
        self.reps, self.top, self.floor = reps, top, floor
        self._prep = {}
        ok = [int(x) for x in rows if add[x] in ADDUCT_SHIFT and key[x] is not None]
        groups = {}
        for x in ok: groups.setdefault((key[x], mode[x]), []).append(x)
        chosen = [x for g in groups.values() for x in self.pick(g)]
        log(f"analog store: {len(chosen):,} representatives for {len({key[x] for x in chosen}):,} keys (from {len(ok):,} test-adduct spectra)")
        keys = sorted({key[x] for x in chosen}); self.keys = keys; self.kix = {k: i for i, k in enumerate(keys)}
        self.S = {}
        for md in ("positive", "negative"):
            items = []
            for x in chosen:
                if mode[x] != md: continue
                c = self.prepared(x)
                if c is not None: items.append((c[3] + ADDUCT_SHIFT[add[x]], x, c))
            items.sort(key=lambda t: (t[0], t[1]))
            lens = np.array([len(c[0]) for _, _, c in items], np.int64); off = np.zeros(len(items) + 1, np.int64); np.cumsum(lens, out=off[1:])
            self.S[md] = dict(M=np.array([t[0] for t in items]), row=np.array([t[1] for t in items], np.int64), off=off,
                              mz=np.concatenate([c[0] for _, _, c in items]) if items else np.zeros(0), p=np.concatenate([c[1] for _, _, c in items]) if items else np.zeros(0),
                              ent=np.array([c[2] for _, _, c in items]), prec=np.array([c[3] for _, _, c in items]), key=np.array([self.kix[key[t[1]]] for t in items], np.int64))
            log(f"analog store {md}: {len(items):,} spectra")
        self._prep = {}   # free the build cache

    def pick(self, rows_):
        def k_(x):
            c = self.ce[x]; ced = abs(float(c) - 35.0) if c is not None and np.isfinite(c) else 999.0
            return (0 if self.add[x] in ("[M+H]+", "[M-H]-") else 1, ced, x)
        return sorted(rows_, key=k_)[:self.reps]

    def prepared(self, x):
        if x in self._prep: return self._prep[x]
        mz, it = self.spectrum(x); sh = ELECTRON if (self.lib[x] == "enveda-180" and self.mode[x] == "positive") else 0.0
        prec = float(self.prec[x]) - sh
        cm, ci = clean_peaks(np.asarray(mz, np.float64) - sh, it, prec, floor=self.floor, top=self.top)
        out = None
        if len(ci):
            p = entropy_weight(ci); out = (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), prec)
        if len(self._prep) < 2_000_000: self._prep[x] = out
        return out

    def analogs(self, qspec, query_rows=(), drop_keys=(), relib=None, key_rows=None, n_analog=N_ANALOG, win=WIN, drop_libs=()):
        """qspec: list of dicts with mz, it, prec (electron-corrected), adduct, mode. Returns [(key, sim)] best first."""
        qset = set(int(x) for x in query_rows); best = {}
        drop_ix = {self.kix[k] for k in drop_keys if k in self.kix}
        re_ix = self.kix.get(relib[0]) if relib else None
        prepped = []
        for s in qspec:
            cm, ci = clean_peaks(np.asarray(s["mz"], np.float64), np.asarray(s["it"], np.float64), float(s["prec"]), floor=self.floor, top=self.top)
            if not len(ci): continue
            p = entropy_weight(ci); q = (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), float(s["prec"]))
            prepped.append((s, q))
            st = self.S.get(s["mode"])
            if st is None or not len(st["M"]): continue
            Mq = q[3] + ADDUCT_SHIFT[s["adduct"]]
            lo = int(np.searchsorted(st["M"], Mq - win, "left")); hi = int(np.searchsorted(st["M"], Mq + win, "right"))
            if hi <= lo: continue
            sims = _search(q[0], q[1], q[2], q[3], lo, hi, st["off"], st["mz"], st["p"], st["ent"], st["prec"])
            for kk in np.flatnonzero(sims > 0.05):
                r = lo + int(kk)
                if int(st["row"][r]) in qset: continue
                if drop_libs and self.lib[int(st["row"][r])] in drop_libs: continue   # sensitivity: analogs from these libraries removed
                ki = int(st["key"][r])
                if ki in drop_ix or ki == re_ix: continue
                v = float(sims[kk])
                if v > best.get(ki, 0.0): best[ki] = v
        if relib and re_ix is not None and key_rows is not None and relib[0] not in drop_keys:   # re-selected representatives of that key outside the library
            alt = [int(x) for x in key_rows.get(relib[0], []) if self.lib[x] != relib[1] and int(x) not in qset and self.add[x] in ADDUCT_SHIFT]
            v = 0.0
            for md in ("positive", "negative"):
                for y in self.pick([x for x in alt if self.mode[x] == md]):
                    cy = self.prepared(y)
                    if cy is None: continue
                    for s, q in prepped:
                        if s["mode"] == md: v = max(v, sim_pair(q, cy))
            if v > 0.05: best[re_ix] = v
        top = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))[:n_analog]
        return [(self.keys[k], v) for k, v in top]


def features(cand_fps, analog_fps, sims, cand_keys=None, analog_keys=None):
    """cand_fps: list of RDKit bit vectors (None allowed); analog_fps/sims: aligned lists. Returns dict of arrays.
    With keys: also the self-excluded *_x features (the candidate's own key removed from its analog set; its self-match is the library channel)."""
    from rdkit import DataStructs
    n = len(cand_fps); out = {k: np.zeros(n) for k in ("ap", "a1", "best_tan", "top_tan", "mean_tan", "ap_x", "mean_tan_x", "best_tan_x")}
    if not analog_fps: return out
    w = np.asarray(sims, np.float64); w3 = w ** SIM_POW
    for i, f in enumerate(cand_fps):
        if f is None: continue
        tan = np.asarray(DataStructs.BulkTanimotoSimilarity(f, analog_fps), np.float64)
        out["ap"][i] = (tan * w3).max(); out["a1"][i] = (tan * w).max(); out["best_tan"][i] = tan.max(); out["top_tan"][i] = tan[0]
        out["mean_tan"][i] = (tan * w3).sum() / (w3.sum() + 1e-9)
        if cand_keys is not None and analog_keys is not None:
            keep = np.array([k_ != cand_keys[i] for k_ in analog_keys], bool)
            if keep.any():
                t_, w3_ = tan[keep], w3[keep]; out["ap_x"][i] = (t_ * w3_).max(); out["best_tan_x"][i] = t_.max(); out["mean_tan_x"][i] = (t_ * w3_).sum() / (w3_.sum() + 1e-9)
    return out
