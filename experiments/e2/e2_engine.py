"""145 E2 engine: the per-molecule E2 computation shared by the Kaggle pipeline (test queries: no masks) and the development parity check
(the C1 masks of b1_ewin.py / e2_feats.py). One call = E window -> f.z / official keys -> library similarity -> MetFrag-lite -> analog
features -> e2_common.view_frame -> E2 score -> ranked official keys. The window, merge and library rules are copied from b1_ewin.py and the
feature rules from e2_feats.py (the versions that built the 144 development tables), so the kernel and the evaluator compute the same numbers.
Dependencies are injected (the caller owns the worker pool, the FPNet, the spectra store and the analog store):
  feat_map(smiles) -> (raw InChIKey14 list, f.z array)   [b1_features._feat with the molecule's zlog]
  okey_map(smiles) -> official keys                       [b1_features._okey]
  frag_map(list of (smiles, spectra)) -> list of {smiles: score} [b1_frag.score(b1_frag.fragments(s), spectra)]
Masks (development only): query_rows = the query acquisitions (never references); c1_truth = (truth key, alias raw keys, selection library):
the truth's references from its selection library are removed (library similarity) and the truth key is re-represented outside that library
(analogs, b1_analog relib) -- the C1 view. Without masks every reference is used (the test regime)."""
import numpy as np, pandas as pd
from b1_common import ELECTRON, clean_peaks, entropy_similarity

PPM, MAX_REF, DUP_SIM = 10.0, 24, 0.98
ANA = ("ap", "a1", "best_tan", "top_tan", "mean_tan")


def exact_dup(q, rmz, rit, rprec, radd):
    """b1_features.exact_dup: same adduct, precursor within 5 mDa, identical cleaned peak list."""
    if q["adduct"] != radd or abs(q["prec"] - rprec) >= 0.005: return False
    qmz, qit = q["clean"]
    return len(qmz) == len(rmz) and len(qmz) > 0 and np.allclose(qmz, rmz, atol=2e-4) and np.allclose(qit, rit, atol=1e-3)


class EStores:
    """Mass-sorted E sources: PubChemLite structures with a PubChem-tier row, the v2 pool (train src 1/3, COCONUT src 2/3), the COCONUT
    store (sorted by mass, as shipped) and BIO (ChEBI / LIPID MAPS; shipped SMILES and monoisotopic mass)."""

    def __init__(self, tmass, toff, tbuf, pcl_tier_rows, pool, cmass, csmi, bio):
        self.toff, self.tbuf = toff, tbuf
        r = np.sort(np.asarray(pcl_tier_rows, np.int64)); m = np.asarray(tmass[r], np.float64); o = np.argsort(m, kind="stable"); self.pcl_rows, self.pcl_mass = r[o], m[o]
        po = np.argsort(pool["mass"].to_numpy(), kind="stable")
        self.pmass = pool["mass"].to_numpy()[po]; self.psmi = pool["smiles"].to_numpy()[po]; self.psrc = pool["src"].to_numpy()[po]; self.ppid = pool["pid"].to_numpy()[po]; self.pkey = pool["key"].to_numpy()[po]
        self.cmass, self.csmi = (np.asarray(cmass), np.asarray(csmi)) if cmass is not None else (np.zeros(0), np.zeros(0, object))
        bo = np.argsort(bio["monoisotopic_mass"].to_numpy(), kind="stable"); self.bmass = bio["monoisotopic_mass"].to_numpy()[bo]; self.bsmi = bio["smiles"].to_numpy()[bo]

    def tier_smiles(self, r):
        o = np.asarray(self.toff[r:r + 2]).astype(np.int64); return bytes(self.tbuf[o[0]:o[1]]).decode("ascii")

    def window(self, M_by_add):
        src = {}

        def add(s_, m_, **fl):
            d = src.setdefault(str(s_), dict(train=False, coco=False, pcl=False, bio=False, pid=-1, pkey=None, mass=float(m_)))
            for k_, v_ in fl.items():
                if k_ in ("pid", "pkey"):
                    if d[k_] in (-1, None): d[k_] = v_
                else: d[k_] = d[k_] or v_
        for M in M_by_add.values():
            tol = M * PPM * 1e-6
            lo, hi = np.searchsorted(self.pcl_mass, M - tol, "left"), np.searchsorted(self.pcl_mass, M + tol, "right")
            for tr_, m_ in zip(self.pcl_rows[lo:hi], self.pcl_mass[lo:hi]): add(self.tier_smiles(int(tr_)), m_, pcl=True)
            lo, hi = np.searchsorted(self.pmass, M - tol, "left"), np.searchsorted(self.pmass, M + tol, "right")
            for s_, sr_, pi_, pk_, m_ in zip(self.psmi[lo:hi], self.psrc[lo:hi], self.ppid[lo:hi], self.pkey[lo:hi], self.pmass[lo:hi]):
                add(s_, m_, train=int(sr_) in (1, 3), coco=int(sr_) in (2, 3), pid=int(pi_), pkey=str(pk_))
            lo, hi = np.searchsorted(self.cmass, M - tol, "left"), np.searchsorted(self.cmass, M + tol, "right")
            for s_, m_ in zip(self.csmi[lo:hi], self.cmass[lo:hi]): add(s_, m_, coco=True)
            lo, hi = np.searchsorted(self.bmass, M - tol, "left"), np.searchsorted(self.bmass, M + tol, "right")
            for s_, m_ in zip(self.bsmi[lo:hi], self.bmass[lo:hi]): add(s_, m_, bio=True)
        return src


class E2Engine:
    def __init__(self, stores, booster, key_rows, spectrum, lib_of_row, add_of_row, mode_of_row, prec_of_row, ana_store, key_smi, morgan_fp):
        self.st, self.booster, self.key_rows, self.spectrum = stores, booster, key_rows, spectrum
        self.lib_of_row, self.add_of_row, self.mode_of_row, self.prec_of_row = lib_of_row, add_of_row, mode_of_row, prec_of_row
        self.ana, self.key_smi, self.mfp, self.ref_cache = ana_store, key_smi, morgan_fp, {}

    def tables(self, q, M_by_add, feat_map, okey_map, frag_map, query_rows=frozenset(), c1_truth=None, mol_id="m", set_name="test"):
        """E-window rows (b1_ewin columns; C1 columns = this regime) and e2_feats rows of one molecule; (None, None) for an empty window."""
        src = self.st.window(M_by_add); smiles = list(src)
        if not smiles: return None, None
        raw_keys, fp = feat_map(smiles); okeys = okey_map(smiles); rep = {}
        for i, (rk, ok) in enumerate(zip(raw_keys, okeys)):
            if rk is None or ok is None: continue
            d = src[smiles[i]]; f_ = float(fp[i]) if np.isfinite(fp[i]) else -np.inf
            if ok not in rep: rep[ok] = dict(i=i, rks={rk}, fp=f_, **{k_: d[k_] for k_ in ("train", "coco", "pcl", "bio", "pid", "pkey", "mass")})
            else:
                p = rep[ok]; p["rks"].add(rk)
                for k_ in ("train", "coco", "pcl", "bio"): p[k_] = p[k_] or d[k_]
                if p["pid"] < 0: p["pid"] = d["pid"]; p["pkey"] = d["pkey"]
                if f_ > p["fp"]: p["fp"] = f_; p["i"] = i; p["mass"] = d["mass"]
        keys = list(rep); n_e = len(keys)
        if n_e == 0: return None, None
        tk, aliases, tlib = c1_truth if c1_truth is not None else (None, set(), None)
        tset = {i for i, k in enumerate(keys) if tk is not None and (k == tk or (rep[k]["rks"] & aliases) or rep[k]["pkey"] == tk)}
        fpu = np.array([rep[k]["fp"] for k in keys]); fpu[~np.isfinite(fpu)] = np.nan
        train = np.array([rep[k]["train"] for k in keys])
        cm = np.array([rep[k]["mass"] for k in keys], float); ppm_err = np.min(np.abs(np.array([[(M - m) / m * 1e6 for m in cm] for M in M_by_add.values()])), axis=0)
        lib = np.zeros(n_e); same = np.zeros(n_e); nref = np.zeros(n_e, int)
        for ci, k in enumerate(keys):   # library similarity (b1_ewin rules) for train-structure candidates
            pk = rep[k]["pkey"]
            if pk is None or pk not in self.key_rows or not train[ci]: continue
            is_t = (tk is not None) and ((pk == tk) or (ci in tset)); kept = []
            for x in [int(x) for x in self.key_rows[pk] if int(x) not in query_rows]:
                if x not in self.ref_cache:
                    sh = ELECTRON if (self.lib_of_row[x] == "enveda-180" and self.mode_of_row[x] == "positive") else 0.0
                    mz, it = self.spectrum(x); mz = np.asarray(mz, np.float64) - sh
                    self.ref_cache[x] = (clean_peaks(mz, np.asarray(it, np.float64), float(self.prec_of_row[x]) - sh), float(self.prec_of_row[x]) - sh)
                (rmz, rit), rprec = self.ref_cache[x]
                if any(exact_dup(s, rmz, rit, rprec, self.add_of_row[x]) for s in q): continue
                if any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == self.mode_of_row[x] and entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= DUP_SIM for s in q): continue
                kept.append(x)
            refs = [x for x in kept if not (is_t and self.lib_of_row[x] == tlib)]
            if len(refs) > MAX_REF:
                pri = np.array([0 if self.add_of_row[x] in M_by_add else 1 for x in refs]); refs = [refs[i] for i in np.argsort(pri, kind="stable")[:MAX_REF]]
            b = s1 = 0.0
            for x in refs:
                (rmz, rit), rprec = self.ref_cache[x]
                for s in q:
                    if s["mode"] != self.mode_of_row[x]: continue
                    sim = entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit); b = max(b, sim); s1 = max(s1, sim if self.add_of_row[x] == s["adduct"] else 0.0)
            lib[ci], same[ci], nref[ci] = b, s1, len(refs)
        if len(self.ref_cache) > 300_000: self.ref_cache.clear()
        fs = np.nan_to_num(fpu, nan=-1e18); order = np.argsort(-fs, kind="stable"); frank = np.empty(n_e, int); frank[order] = np.arange(1, n_e + 1)
        rsmi = [smiles[rep[k]["i"]] for k in keys]
        E = pd.DataFrame(dict(set=set_name, molecule=mol_id, official_key=keys, smiles=rsmi, is_truth=[k == tk for k in keys], fp=[float(x) if np.isfinite(x) else None for x in fpu],
                              fp_rank_e=frank, n_e=n_e, ppm_err=ppm_err, in_train_c1=train, in_train_c2=train, in_coconut=[bool(rep[k]["coco"]) for k in keys],
                              in_pcl=[bool(rep[k]["pcl"]) for k in keys], in_bio=[bool(rep[k]["bio"]) for k in keys], lib_sim_c1=lib, lib_sim_c2=lib, lib_same_c1=same,
                              lib_same_c2=same, lib_nref_c1=nref, lib_nref_c2=nref))
        # MetFrag-lite (view independent) and analog features (this regime's masks)
        fsp = [dict(mz=s["mz"], it=s["it"], prec=s["prec"], mode=s["mode"]) for s in q]
        fr = frag_map([(rsmi, fsp)])[0]
        an = self.ana.analogs([dict(mz=s["mz"], it=s["it"], prec=s["prec"], adduct=s["adduct"], mode=s["mode"]) for s in q], query_rows=set(query_rows),
                              relib=(tk, tlib) if tk is not None else None, key_rows=self.key_rows)
        import b1_analog as BA
        afp = [(self.mfp(self.key_smi.get(k)), sv) for k, sv in an]; afp = [(f_, sv) for f_, sv in afp if f_ is not None]
        fa = BA.features([self.mfp(s) for s in rsmi], [f_ for f_, _ in afp], [sv for _, sv in afp])
        F = pd.DataFrame(dict(set=set_name, molecule=mol_id, official_key=keys, frag=[float(fr.get(s, 0.0)) for s in rsmi],
                              **{f"ana_{f}_{v}": np.asarray(fa[f], float) for f in ANA for v in ("c1", "c2")}))
        return E, F

    def rank(self, E, F):
        """E2 order (official keys) of one molecule's tables in the C1 columns (= the test regime)."""
        from e2_common import FEATS, view_frame, rank_lists
        if E is None or not len(E): return []
        X = view_frame(E, F, "c1"); R = rank_lists(X, self.booster.predict(X[FEATS]))
        return R.official_key.astype(str).tolist()


FUSE_K = 10.0


def fuse_rrf(p, e_rank, e_top, w):
    """F of 144 (identical to e2_eval.rrf): candidates P top 25 | E2 top 25, s = 1/(10 + r_P) + w/(10 + r_E); w = 0 -> P exactly."""
    pr = {k: i + 1 for i, k in enumerate(p)}; cand = list(dict.fromkeys(list(p) + (list(e_top) if w else [])))
    s = lambda k: (1.0 / (FUSE_K + pr[k]) if k in pr else 0.0) + (w / (FUSE_K + e_rank[k]) if (w and k in e_rank) else 0.0)
    return sorted(cand, key=lambda k: (-s(k), pr.get(k, 99), e_rank.get(k, 1e9), k))[:25]


def insert2(L, e1):
    """H of 144 (identical to e2_eval.insert2): E2's top 1 to position 2 unless it is already 1st or 2nd; the first is kept."""
    if e1 is None or not L or e1 in L[:2]: return L[:25]
    return ([L[0], e1] + [k for k in L[1:] if k != e1])[:25]
