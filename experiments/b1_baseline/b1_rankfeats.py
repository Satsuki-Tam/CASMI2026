"""Shared candidate-feature construction for the learned fusion (training and inference use exactly this function).

All features are label-free and molecule-relative where it matters (z within the molecule's shortlist). Missing model scores are
encoded explicitly (gl_missing / ice_missing) and the z-term is set to the list minimum (never 'average'); when a model has < 2 finite
values on the list its z-term is 0 for every candidate.
"""
import numpy as np

FEATS = ["z_fp", "z_gl", "z_ice", "fp", "gl", "ice", "pop_public", "lsid", "lpmid", "lsynonyms", "np_bit", "src_bit", "lotus", "lib_sim", "lib_same", "lib_nref", "lib_margin",
         "lib_max_mol", "in_tier", "in_train", "in_coconut", "ppm_err", "fp_rank_window", "n_cands", "gl_missing", "ice_missing", "n_query", "ce_known"]
# v3 additions (Codex 008 / diagnostic D1): each model's confidence on this list (top-1 minus top-2 of its z), the candidate's rank within the
# list under each model, its distance to the list's best, the library-similarity rank, the in_train x lib_sim interaction and the window size.
EXTRA_V3 = ["rank_fp", "rank_gl", "rank_ice", "gap_fp", "gap_gl", "gap_ice", "margin_fp_mol", "margin_gl_mol", "margin_ice_mol", "lib_rank", "in_train_x_lib", "log_n_window"]
# v3s = the small block to compare first (Codex 008): per-model rank + per-model confidence + window size
EXTRA_V3S = ["rank_fp", "rank_gl", "rank_ice", "margin_fp_mol", "margin_gl_mol", "margin_ice_mol", "log_n_window"]
# v2_noice: ICE removed entirely (the fixed rule is better without the ICE term on all development sets, 2026-10-24 16:50)
# 2026-10-26 (Codex 027/028 hypothesis 1): FPNet training exposure of each candidate for the checkpoint that produced the table / the inference
# (fp_pos = the candidate identity was a positive of that FPNet's training; negpool = in the v2 pool = the decoy sampler's domain). Opt-in: only
# models whose feature list contains these names need the `exposure` argument; label-free (ledgers per checkpoint, never the view's truth).
EXTRA_EXP = ["fp_pos", "negpool"]
FEATSETS = {"v2": FEATS, "v2_noice": [f for f in FEATS if f not in ("z_ice", "ice", "ice_missing")], "v3s": FEATS + EXTRA_V3S, "v3": FEATS + EXTRA_V3}
FEATSETS["v2_noice_exp"] = FEATSETS["v2_noice"] + EXTRA_EXP
# monotone directions for the constrained variant (0 = unconstrained): only the model scores (up) and the mass error (down), Codex 008
MONO = dict(z_fp=1, z_gl=1, z_ice=1, fp=1, gl=1, ice=1, ppm_err=-1)
# 2026-10-25 (panel probe): reference evidence may only raise a candidate -- in the C2 training view the truth has no references by construction,
# so an unconstrained ranker learns 'has references -> decoy' (lib_same / lib_nref) and collapses on class-1 molecules with many references
MONO_LIB = dict(MONO, lib_sim=1, lib_same=1, lib_margin=1, in_train_x_lib=1)


def rank_desc(v):
    """1 = best; ties share the best rank of their group (independent of the row order); candidates without a value get the worst rank (len)."""
    v = np.asarray(v, float); ok = np.isfinite(v); r = np.full(len(v), float(len(v)))
    if ok.any():
        vals = v[ok]; srt = np.sort(vals)[::-1]
        r[np.flatnonzero(ok)] = np.searchsorted(-srt, -vals, side="left") + 1
    return r


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
                   ppm_err, fp_rank_window, n_query, ce_known, n_window=np.nan, feats=None, exposure=None):
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
    feats = list(feats) if feats is not None else FEATS
    if any(c in EXTRA_EXP for c in feats):
        if exposure is None: raise ValueError("feature list needs the FPNet exposure block (fp_pos / negpool) but no exposure arrays were given")
        cols.update(fp_pos=np.asarray(exposure["fp_pos"], float), negpool=np.asarray(exposure["negpool"], float))
    if any(c in EXTRA_V3 for c in feats):
        def gap(zv): return (float(np.max(zv)) - zv) if len(zv) else zv
        def margin(zv):
            srt = np.sort(zv)[::-1]; return np.full(len(zv), float(srt[0] - srt[1]) if len(srt) > 1 else 0.0)
        cols.update(rank_fp=np.log1p(rank_desc(fp)), rank_gl=np.log1p(rank_desc(gl)), rank_ice=np.log1p(rank_desc(ice)),
                    gap_fp=gap(cols["z_fp"]), gap_gl=gap(cols["z_gl"]), gap_ice=gap(cols["z_ice"]),
                    margin_fp_mol=margin(cols["z_fp"]), margin_gl_mol=margin(cols["z_gl"]), margin_ice_mol=margin(cols["z_ice"]),
                    lib_rank=np.log1p(rank_desc(lib)), in_train_x_lib=cols["in_train"] * lib,
                    log_n_window=np.full(len(fp), np.log1p(float(n_window)) if np.isfinite(float(n_window)) else np.nan))
    return np.column_stack([cols[c] for c in feats])
