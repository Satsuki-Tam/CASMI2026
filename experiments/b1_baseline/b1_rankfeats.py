"""Shared candidate-feature construction for the learned fusion (training and inference use exactly this function).

All features are label-free and molecule-relative where it matters (z within the molecule's shortlist). Missing model scores are
encoded explicitly (gl_missing / ice_missing) and the z-term is set to the list minimum (never 'average'); when a model has < 2 finite
values on the list its z-term is 0 for every candidate.
"""
import numpy as np

FEATS = ["z_fp", "z_gl", "z_ice", "fp", "gl", "ice", "pop_public", "lsid", "lpmid", "lsynonyms", "np_bit", "src_bit", "lotus", "lib_sim", "lib_same", "lib_nref", "lib_margin",
         "lib_max_mol", "in_tier", "in_train", "in_coconut", "ppm_err", "fp_rank_window", "n_cands", "gl_missing", "ice_missing", "n_query", "ce_known"]


def zlist(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.full_like(x, np.nan)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    elif ok.sum() >= 1: out[ok] = 0.0
    out[~ok] = np.nanmin(out[ok]) if ok.any() else 0.0
    return out


def term(vals):
    v = np.asarray(vals, float)
    return zlist(v) if np.isfinite(v).sum() >= 2 else np.zeros(len(v))


def feature_matrix(fp, gl, ice, pop_public, lsid, lpmid, lsynonyms, np_bits, src_mask, lotus_refs, lib_sim, lib_same, lib_nref, in_tier, in_train, in_coconut,
                   ppm_err, fp_rank_window, n_query, ce_known):
    """arrays of equal length (one molecule's candidates) -> (n, len(FEATS)) float matrix in FEATS order."""
    fp = np.asarray(fp, float); gl = np.asarray(gl, float); ice = np.asarray(ice, float); lib = np.asarray(lib_sim, float)
    top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
    cols = dict(z_fp=zlist(fp), z_gl=term(gl), z_ice=term(ice), fp=np.nan_to_num(fp, nan=np.nanmin(fp) if np.isfinite(fp).any() else 0.0),
                gl=np.nan_to_num(gl, nan=-1.0), ice=np.nan_to_num(ice, nan=-1.0), pop_public=np.asarray(pop_public, float), lsid=np.asarray(lsid, float), lpmid=np.asarray(lpmid, float),
                lsynonyms=np.asarray(lsynonyms, float), np_bit=(np.asarray(np_bits, float) != 0).astype(float), src_bit=((np.asarray(src_mask).astype(np.int64) & 1) != 0).astype(float),
                lotus=np.log1p(np.maximum(np.asarray(lotus_refs, float), 0)), lib_sim=lib, lib_same=np.asarray(lib_same, float), lib_nref=np.asarray(lib_nref, float), lib_margin=lib - second,
                lib_max_mol=np.full(len(fp), float(lib.max()) if len(lib) else 0.0), in_tier=np.asarray(in_tier, float), in_train=np.asarray(in_train, float), in_coconut=np.asarray(in_coconut, float),
                ppm_err=np.nan_to_num(np.asarray(ppm_err, float), nan=10.0), fp_rank_window=np.log1p(np.asarray(fp_rank_window, float)), n_cands=np.full(len(fp), float(len(fp))),
                gl_missing=(~np.isfinite(gl)).astype(float), ice_missing=(~np.isfinite(ice)).astype(float), n_query=np.full(len(fp), float(n_query)), ce_known=np.full(len(fp), float(ce_known)))
    return np.column_stack([cols[c] for c in FEATS])
