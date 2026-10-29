"""132: the fixed E-lite RRF of 102 (variant rrf_rank_e1r_0.5) as one shared function, used by the submission pipeline (b1_pipeline.py) and by the
check that replays it inside a copy of the 102 evaluator (gen_eval2fd_e132.py, parity (A) of 132_prereg_elite_public.md).
Definition (102 v2, gen_eval2fd --emodel): rows = one molecule's candidates (unique official identities) in any fixed row order, `order` = the final
main order P (a permutation of the rows). E = the rows with in_coconut | in_train | official key in the E key set. The E model is applied to the
E rows only, with every list-relative feature recomputed within E (feature_matrix on the sub-arrays; ICE = NaN). E order = E prediction
descending, ties by the main position. RRF(i) = 1 / (K + r_P(i)) + alpha / (K + r_E(i)) (r_P = 1-based main rank, r_E = 1-based E rank, 0 for
rows outside E), ties by the main position. A non-finite E prediction stops the run (it must not turn into another vote)."""
import numpy as np


def positions(order, n):
    """0-based main position of every row; order must be a permutation of range(n)."""
    o = np.asarray(order, np.int64)
    if len(o) != n or (n and not np.array_equal(np.sort(o), np.arange(n))): raise ValueError("132: the main order is not a permutation of the rows")
    pos = np.empty(n, np.int64); pos[o] = np.arange(n); return pos


def e_mask(in_coconut, in_train, keys, eks):
    keys = list(keys)
    return np.asarray(in_coconut, bool) | np.asarray(in_train, bool) | np.fromiter((str(k) in eks for k in keys), bool, len(keys))


def e_matrix(feature_matrix, feats, ei, fp, gl, pop, lsid, lpmid, lsynonyms, np_bits, src_mask, lotus_refs, lib, lib_same, lib_nref, in_tier, in_train, in_coconut,
             ppm_err, fp_rank_window, n_query, ce_known, n_window, ana_ap, ana_mt):
    """feature matrix of the E rows ei, every relative feature computed within E (as gen_eval2fd 102)."""
    sub = lambda arr: np.asarray(arr)[ei]; feats = list(feats)
    return feature_matrix(sub(fp), sub(gl), np.full(len(ei), np.nan), sub(pop), sub(lsid), sub(lpmid), sub(lsynonyms), sub(np_bits), sub(src_mask), sub(lotus_refs), sub(lib),
                          sub(lib_same), sub(lib_nref), sub(in_tier), sub(in_train), sub(in_coconut), sub(ppm_err), sub(fp_rank_window), float(n_query), float(ce_known),
                          n_window=n_window, feats=feats,
                          analog=(dict(ap=sub(ana_ap), mean_tan=sub(ana_mt)) if any(f_.startswith("ana_") or f_ == "z_ana_ap" for f_ in feats) else None))


def e_rank(booster, X, ei, pos):
    """E order (row indices): prediction descending, ties by the main position."""
    se = np.asarray(booster.predict(X), float)
    if not np.isfinite(se).all(): raise RuntimeError("132: non-finite E prediction - stop (an E failure must not turn into another vote)")
    ei = np.asarray(ei, np.int64)
    return [int(ei[j]) for j in np.lexsort((pos[ei], -se))]


def rrf(order, es, K, alpha):
    """identity RRF of the main order with the E order; ties by the main position. Returns the full new order (row indices)."""
    n = len(order); pos = positions(order, n)
    r2 = np.full(n, np.inf)
    if len(es): r2[np.asarray(es, np.int64)] = np.arange(1, len(es) + 1)
    sc = 1.0 / (K + pos + 1) + alpha * np.where(np.isfinite(r2), 1.0 / (K + r2), 0.0)
    return [int(i) for i in np.lexsort((pos, -sc))]


def fused_order(booster, feats, feature_matrix, eks, rows, order, fp, gl, pop, lib, n_query, ce_known, n_window, K, alpha):
    """pipeline entry: rows = b1_pipeline candidate dicts of one molecule, order = its final main order, fp / gl / pop / lib = the arrays the
    main fusion used. -> (new order, E order, number of E rows)."""
    n = len(rows); order = [int(i) for i in order]; pos = positions(order, n)
    col = lambda k: [r[k] for r in rows]
    ei = np.flatnonzero(e_mask(col("in_coconut"), col("in_train"), col("key"), eks)); es = []
    if len(ei):
        X = e_matrix(feature_matrix, feats, ei, fp, gl, pop, col("lsid"), col("lpmid"), col("lsynonyms"), col("np"), col("src_mask"), col("lotus_refs"), lib, col("lib_same"),
                     col("lib_nref"), col("in_tier"), col("in_train"), col("in_coconut"), col("ppm_err"), col("fp_rank_window"), n_query, ce_known, n_window,
                     col("ana_ap"), col("ana_mean_tan"))
        es = e_rank(booster, X, ei, pos)
    return rrf(order, es, K, alpha), es, int(len(ei))
