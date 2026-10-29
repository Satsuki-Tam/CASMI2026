"""133 v2 (Codex 133, 'must before reading'): one validator for the MIST v4 inputs at every entry point (training, evaluation, pipeline).
validate_table(X, name, feat=None): X = one mist_<tag>_<set>.parquet of mist_score_v4.py.
  - no null set / molecule / official_key / smiles / status; status in the registered set; no +-inf anywhere; no duplicate (set, molecule, smiles)
    or (set, molecule, official_key);
  - status ok: mist_cos finite in [0, 1] (tol 1e-6), n_q integer in 1..8, mist_fint finite in [0, 1] (tol 1e-6), mist_npk finite >= 0, and
    mist_ppm finite in [0, 20] (MIST's assignment threshold, tol 1e-6) when mist_npk > 0, NaN when mist_npk == 0;
  - status not ok: mist_cos / mist_fint / mist_npk / mist_ppm NaN and n_q == 0;
  - feat (the B1 feature table of the same set, optional): the (molecule, smiles, official_key) rows of X are exactly the table's rows of the same
    molecules (one-to-one; the official identity / SMILES pairs agree).
validate_qflags(Q, X, name): Q = mist_<tag>_<set>_qflags.parquet (mist_qflags.py): unique molecules, covering every molecule of X
  (Q lists the whole selection, incl. the empty-window molecules without candidate rows); n_mist_q integer 0..8;
  a molecule with an ok candidate has n_mist_q > 0; candidates with status no_qrows / no_mist_adduct belong to molecules with that qreason.
Every violation raises ValueError (the caller stops; a failure is never turned into 'MIST missing')."""
import numpy as np, pandas as pd
STATUSES = {"ok", "no_qrows", "no_mist_adduct", "no_formula", "mass_mismatch", "no_fp"}
TOL = 1e-6


def _fail(name, msg): raise ValueError(f"MIST input {name}: {msg}")


def validate_table(X, name, feat=None):
    need = ["set", "molecule", "smiles", "official_key", "mist_cos", "mist_ll", "n_q", "status", "mist_fint", "mist_npk", "mist_ppm"]
    miss = [c for c in need if c not in X.columns]
    if miss: _fail(name, f"missing columns {miss}")
    if X[["set", "molecule", "official_key", "smiles", "status"]].isna().any().any(): _fail(name, "null key / status")
    st = set(X.status.astype(str))
    if not st <= STATUSES: _fail(name, f"unknown status {st - STATUSES}")
    num = X[["mist_cos", "mist_ll", "n_q", "mist_fint", "mist_npk", "mist_ppm"]].to_numpy(float)
    if np.isinf(num).any(): _fail(name, "+-inf value")
    k = X[["set", "molecule", "smiles"]].astype(str)
    if k.duplicated().any() or X[["set", "molecule", "official_key"]].astype(str).duplicated().any(): _fail(name, "duplicate rows")
    ok = (X.status.astype(str) == "ok").values; c = X.mist_cos.values.astype(float); q = X.n_q.values.astype(float)
    fi = X.mist_fint.values.astype(float); npk = X.mist_npk.values.astype(float); pp = X.mist_ppm.values.astype(float)
    if not (np.isfinite(c[ok]).all() and (c[ok] >= -TOL).all() and (c[ok] <= 1 + TOL).all()): _fail(name, "ok without a finite cos in [0, 1]")
    if not ((q[ok] == np.round(q[ok])).all() and (q[ok] >= 1).all() and (q[ok] <= 8).all()): _fail(name, "ok with n_q outside the integers 1..8")
    if not (np.isfinite(fi[ok]).all() and (fi[ok] >= -TOL).all() and (fi[ok] <= 1 + TOL).all()): _fail(name, "ok with mist_fint outside [0, 1]")
    if not (np.isfinite(npk[ok]).all() and (npk[ok] >= 0).all()): _fail(name, "ok with a non-finite / negative mist_npk")
    has = ok & (npk > 0); none = ok & (npk == 0)
    if not (np.isfinite(pp[has]).all() and (pp[has] >= -TOL).all() and (pp[has] <= 20 + TOL).all()): _fail(name, "assigned peaks but mist_ppm not finite in [0, 20]")
    if not np.isnan(pp[none]).all(): _fail(name, "no assigned peak but a finite mist_ppm")
    nok = ~ok
    if not (np.isnan(c[nok]).all() and (q[nok] == 0).all() and np.isnan(fi[nok]).all() and np.isnan(npk[nok]).all() and np.isnan(pp[nok]).all()): _fail(name, "a non-ok row with a value or queries")
    if feat is not None:
        f = feat[feat.molecule.astype(str).isin(set(X.molecule.astype(str)))][["molecule", "smiles", "official_key"]].astype(str)
        x = X[["molecule", "smiles", "official_key"]].astype(str)
        j = f.merge(x, on=["molecule", "smiles", "official_key"], how="outer", indicator=True)
        if not (j._merge == "both").all() or len(j) != len(x) or len(j) != len(f): _fail(name, f"rows do not match the feature table: {j._merge.value_counts().to_dict()}")
    return True


def validate_qflags(Q, X, name):
    if Q.molecule.astype(str).duplicated().any(): _fail(name, "duplicate molecules in the query flags")
    if not set(X.molecule.astype(str)) <= set(Q.molecule.astype(str)): _fail(name, "candidate-table molecules without a query flag")   # Q also lists the empty-window molecules of the selection
    nq = Q.n_mist_q.values.astype(float)
    if not ((nq == np.round(nq)).all() and (nq >= 0).all() and (nq <= 8).all()): _fail(name, "n_mist_q outside the integers 0..8")
    qn = dict(zip(Q.molecule.astype(str), nq)); qr = dict(zip(Q.molecule.astype(str), Q.qreason.fillna("").astype(str)))
    for mid, h in X.groupby(X.molecule.astype(str)):
        s = set(h.status.astype(str))
        if "ok" in s and qn[mid] == 0: _fail(name, f"{mid}: ok candidate without a MIST query")
        for r in ("no_qrows", "no_mist_adduct"):
            if r in s and qr[mid] != r: _fail(name, f"{mid}: candidate status {r} but qreason {qr[mid]!r}")
    return True
