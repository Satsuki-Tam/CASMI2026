"""156 (v2 prep): invariants of a WORLD E-window table (b1_ewin_world.py) against its world's masks (world_masks.json, the single source of truth).
Checks (exit 1 on any failure; no performance number is printed):
  roster    : every batch molecule (or every --only molecule) has a molecule row; molecules with n_e = 0 have no candidate rows, the others exactly n_e;
  rows      : official keys unique per molecule; every row keeps a source after the masks (train OR COCONUT OR PCL OR BIO); c1 == c2 columns;
  C3        : no row carries a C3 official key or a struct-drop key; a C3 molecule never has its truth in the window (else STOP: mask inconsistency);
  hidden    : a row whose official key is a hidden (C2 / C3) key has no train membership and no reference;
  references: no logged reference row of a batch identity is in that identity's c1_excl, and no logged row belongs to a hidden key.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/e2/w135_ewin_check.py --ewin DIR --masks WORLD/world_masks.json --set SET [--only m1,m2]"""
import argparse, json, os, sys
import numpy as np, pandas as pd, polars as pl

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ewin", required=True); ap.add_argument("--masks", required=True); ap.add_argument("--set", required=True)
    ap.add_argument("--only", default=""); ap.add_argument("--store", default="data/processed/spectra_store"); a = ap.parse_args()
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    W = json.load(open(P_(a.masks))); s = a.set
    E = pd.read_parquet(os.path.join(P_(a.ewin), f"ewin_{s}.parquet")); M = pd.read_csv(os.path.join(P_(a.ewin), f"ewin_molecules_{s}.csv"), dtype={"molecule": str})
    refs = json.load(open(os.path.join(P_(a.ewin), f"ewin_refs_{s}.json")))
    E["molecule"] = E.molecule.astype(str)
    C3 = set(W["c3_okeys"]); DROP = set(W["struct_drop"]); HIDE = set(W["train_hide"]); C1X = {k: set(int(x) for x in v) for k, v in W["c1_excl"].items()}
    cls = W["wclass"]; fails = []
    want = set(a.only.split(",")) if a.only else set(cls)
    if set(M.molecule) != want: fails.append(f"roster: molecule rows {len(M)} vs expected {len(want)} (missing {len(want - set(M.molecule))}, extra {len(set(M.molecule) - want)})")
    nrow = E.groupby("molecule").size()
    for r in M.itertuples(index=False):
        n = int(nrow.get(r.molecule, 0))
        if int(r.n_e) != n: fails.append(f"roster: {r.molecule} n_e {r.n_e} but {n} rows"); break
    if E.duplicated(["molecule", "official_key"]).any(): fails.append("rows: duplicated official key inside a molecule")
    src = E.in_train_c1 | E.in_coconut | E.in_pcl | E.in_bio
    if (~src).any(): fails.append(f"rows: {int((~src).sum())} rows without any source after the masks")
    for c in ("in_train", "lib_sim", "lib_same", "lib_nref"):
        if not (E[f"{c}_c1"] == E[f"{c}_c2"]).all(): fails.append(f"rows: {c} c1 / c2 differ")
    if E.official_key.isin(C3 | DROP).any(): fails.append(f"C3: {int(E.official_key.isin(C3 | DROP).sum())} rows carry a C3 / struct-drop key")
    c3m = [m for m in M.molecule if cls.get(m) == "C3"]
    if M[M.molecule.isin(c3m)].truth_in_ewin.astype(bool).any(): fails.append("C3: a C3 truth is inside the world E window (STOP: mask / identity inconsistency)")
    h = E[E.official_key.isin(HIDE)]
    if len(h) and (h.in_train_c1.any() or (h.lib_nref_c1 > 0).any()): fails.append("hidden: a hidden key keeps train membership or references")
    meta = pl.read_parquet(f"{P_(a.store)}/spec_meta.parquet", columns=["row", "scorer_ik14"]); key_of_row = meta["scorer_ik14"].to_numpy()
    n_ref_rows = 0
    for r in refs:
        rows = set(r["rows"]); n_ref_rows += len(rows)
        if rows & C1X.get(r["pkey"], set()): fails.append(f"references: {r['official_key']} uses c1_excl rows"); break
        if any(key_of_row[x] in HIDE for x in rows): fails.append(f"references: {r['official_key']} uses rows of a hidden key"); break
    status = "PASS" if not fails else "FAIL"
    print(f"EWIN_CHECK {status} {s}: molecules {len(M)}, rows {len(E)}, empty windows {int((M.n_e == 0).sum())}, C3 molecules {len(c3m)}, "
          f"logged batch-identity candidates {len(refs)} ({n_ref_rows} reference rows), train-only drops {int(M.n_drop_trainonly.sum()) if 'n_drop_trainonly' in M else 'n/a'}")
    for f in fails: print("  -", f)
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
