"""156 / 158 (v2.1): invariants of a WORLD E-window table (b1_ewin_world.py v2.1) and, with --feats, of its world E2 features
(e2_feats_world.py v2.1), against the world's masks (world_masks.json, the single source of truth). Exit 1 on any failure; no performance
number is printed.
  roster    : molecule rows unique and equal to the batch (or --only) roster; every candidate row's molecule is in the roster; molecules with
              n_e = 0 have no candidate rows, the others exactly n_e;
  provenance: every query's zlog equals the B1 world's gen dump (max |diff| <= 1e-5) -- same query semantics as P / B;
  rows      : official keys unique per molecule; every row keeps a source (train OR COCONUT OR PCL OR BIO); c1 == c2 columns;
  C3        : no row carries a C3 official key or a struct-drop key; a C3 molecule never has its truth in the window (STOP: inconsistency);
  hidden    : a row whose official key is a hidden (C2 / C3) key has no train membership and no reference;
  references: no reference row actually used (after MAX_REF) is in any C1 identity's excluded rows, and none belongs to a hidden key;
  analogs   (--feats): e2_feats_world's analog list of every query equals the W135 world P's analog list (same rule, store and masks)."""
import argparse, json, os, sys
import numpy as np, pandas as pd, polars as pl

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ewin", required=True); ap.add_argument("--masks", required=True); ap.add_argument("--set", required=True)
    ap.add_argument("--only", default=""); ap.add_argument("--feats", action="store_true"); ap.add_argument("--world_p", default="")
    ap.add_argument("--store", default="data/processed/spectra_store"); a = ap.parse_args()
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    W = json.load(open(P_(a.masks))); s = a.set
    E = pd.read_parquet(os.path.join(P_(a.ewin), f"ewin_{s}.parquet")); M = pd.read_csv(os.path.join(P_(a.ewin), f"ewin_molecules_{s}.csv"), dtype={"molecule": str})
    refs = json.load(open(os.path.join(P_(a.ewin), f"ewin_refs_{s}.json")))
    E["molecule"] = E.molecule.astype(str)
    C3 = set(W["c3_okeys"]); DROP = set(W["struct_drop"]); HIDE = set(W["train_hide"]); C1X = set(int(x) for v in W["c1_excl"].values() for x in v)
    cls = W["wclass"]; fails = []
    want = set(a.only.split(",")) if a.only else set(cls)
    if M.molecule.duplicated().any(): fails.append("roster: duplicated molecule rows")
    if set(M.molecule) != want: fails.append(f"roster: molecule rows {len(M)} vs expected {len(want)} (missing {len(want - set(M.molecule))}, extra {len(set(M.molecule) - want)})")
    if not set(E.molecule) <= set(M.molecule): fails.append("roster: candidate rows of a molecule outside the ledger")
    nrow = E.groupby("molecule").size()
    bad_n = [m for m, n in zip(M.molecule, M.n_e) if int(n) != int(nrow.get(m, 0))]
    if bad_n: fails.append(f"roster: {len(bad_n)} molecules whose n_e differs from their candidate rows")
    if "zlog_maxdiff" not in M or not (M.zlog_maxdiff.astype(float) <= 1e-5).all(): fails.append("provenance: a query's zlog differs from the B1 world's gen dump (or no record)")
    if E.duplicated(["molecule", "official_key"]).any(): fails.append("rows: duplicated official key inside a molecule")
    if len(E):
        src = E.in_train_c1.astype(bool) | E.in_coconut.astype(bool) | E.in_pcl.astype(bool) | E.in_bio.astype(bool)
        if (~src).any(): fails.append(f"rows: {int((~src).sum())} rows without any source after the masks")
        for c in ("in_train", "lib_sim", "lib_same", "lib_nref"):
            if not (E[f"{c}_c1"] == E[f"{c}_c2"]).all(): fails.append(f"rows: {c} c1 / c2 differ")
        if E.official_key.isin(C3 | DROP).any(): fails.append(f"C3: {int(E.official_key.isin(C3 | DROP).sum())} rows carry a C3 / struct-drop key")
        h = E[E.official_key.isin(HIDE)]
        if len(h) and (h.in_train_c1.astype(bool).any() or (h.lib_nref_c1 > 0).any()): fails.append("hidden: a hidden key keeps train membership or references")
    c3m = [m for m in M.molecule if cls.get(m) == "C3"]
    if M[M.molecule.isin(c3m)].truth_in_ewin.astype(bool).any(): fails.append("C3: a C3 truth is inside the world E window (STOP: mask / identity inconsistency)")
    meta = pl.read_parquet(f"{P_(a.store)}/spec_meta.parquet", columns=["row", "scorer_ik14"]); key_of_row = meta["scorer_ik14"].to_numpy()
    n_ref_rows = 0
    for r in refs:
        rows = set(int(x) for x in r["rows"]); n_ref_rows += len(rows)
        if rows & C1X: fails.append(f"references: {r['official_key']} uses an excluded C1 row"); break
        if any(key_of_row[x] in HIDE for x in rows): fails.append(f"references: {r['official_key']} uses rows of a hidden key"); break
    n_an = 0
    if a.feats:
        an = json.load(open(os.path.join(P_(a.ewin), f"e2f_analogs_{s}.json")))
        Pw = pd.read_parquet(P_(a.world_p)); Pw["molecule"] = Pw.molecule.astype(str); pan = dict(zip(Pw.molecule, Pw.analogs))
        for m, lst in an.items():
            ref = json.loads(pan.get(m, "[]")); n_an += 1
            if [k for k, _ in lst] != [k for k, _ in ref] or not np.allclose([v for _, v in lst], [v for _, v in ref], atol=1e-9):
                fails.append(f"analogs: {m} differs from the W135 world P analog list"); break
            if any(k in HIDE for k, _ in lst): fails.append(f"analogs: {m} returns a hidden key"); break
        if set(an) != set(M.molecule[M.n_e > 0]) and set(an) != set(M.molecule): fails.append("analogs: analog lists do not cover the scored molecules")
    status = "PASS" if not fails else "FAIL"
    print(f"EWIN_CHECK {status} {s}{' +feats' if a.feats else ''}: molecules {len(M)}, rows {len(E)}, empty windows {int((M.n_e == 0).sum())}, C3 molecules {len(c3m)}, "
          f"logged candidates {len(refs)} ({n_ref_rows} reference rows), source rows removed: C3 {int(M.n_drop_world.sum())} / hidden {int(M.n_drop_trainonly.sum())}, "
          f"max zlog diff {float(M.zlog_maxdiff.max()) if len(M) else 0:.2e}, analog lists checked {n_an}")
    for f in fails: print("  -", f)
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
