"""110 amendment (Codex 110 (2)): audit of the seed-1 run's training split, read-only, separate from the running job's check_inputs.json.
Checks (any failure -> exit 1, nothing else is changed):
  S1 split.parquet: columns (sid, fold), sid unique and in [0, n), labels only {hold, np}; work/split.parquet is a regular file (not a link into the
     shared input dir) and the shared input dir has no split.parquet (make_split.py links every SRC file before writing the split).
  S2 train_structs: sid == 0..n-1; every row maps to a global identity group and fold (no missing); scorer key -> one fold and one group.
  S3 full-sid equality with the expected labels: NP-example group (libmask bit 9) -> np, other identity fold <held_out> -> hold, rest -> train
     (absent from split.parquet = train); no train sid in an NP-example group or in the held-out fold.
  S4 inputs equal the public package's: sha256 of train_structs / structures vs SPLIT_AUDIT.json, fp_bits vs MODEL_INPUTS.json, and the same rule
     with held-out fold 0 reproduces the package's split.parquet exactly (sid, fold).
Writes <run>/split_audit.json (counts, hashes of the split, inputs, trainer code). Usage: python -I split_audit.py <run> <structures.parquet> <pkg> <held_out_fold>"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
RUN, FOLDS, PKG, FOLD = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); WD = os.path.join(RUN, "work")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
fail = []
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}"); (None if ok else fail.append(name))
sp_path = os.path.join(WD, "split.parquet"); ts_path = os.path.realpath(os.path.join(WD, "train_structs.parquet")); src = os.path.dirname(ts_path)
check("S1 split is a regular file", os.path.isfile(sp_path) and not os.path.islink(sp_path), sp_path)
check("S1 shared input dir has no split.parquet", not os.path.lexists(os.path.join(src, "split.parquet")), src)
ts = pd.read_parquet(ts_path); sp = pd.read_parquet(sp_path); n = len(ts)
check("S1 split columns", list(sp.columns) == ["sid", "fold"], str(list(sp.columns)))
check("S1 split sid unique / in range", (not sp.sid.duplicated().any()) and sp.sid.between(0, n - 1).all(), f"rows {len(sp)} n {n}")
check("S1 split labels", set(sp.fold.unique()) <= {"hold", "np"}, str(sorted(sp.fold.unique())))
st = pd.read_parquet(FOLDS, columns=["inchikey14", "identity_group", "fold_identity"]).drop_duplicates("inchikey14")
j = ts.merge(st, on="inchikey14", how="left", validate="many_to_one")
check("S2 sid == 0..n-1", len(j) == n and (j.sid.values == np.arange(n)).all())
check("S2 every row has a global group and fold", j.identity_group.notna().all() and j.fold_identity.notna().all(), f"missing {int(j.fold_identity.isna().sum())}")
check("S2 key -> one fold / one group", j.groupby("key").fold_identity.nunique().max() == 1 and j.groupby("key").identity_group.nunique().max() == 1)
is_np = (j.libmask.astype("int64") & (1 << 9)) != 0; np_groups = set(j.identity_group[is_np])
def expected(fold): return np.where(j.identity_group.isin(np_groups), "np", np.where(j.fold_identity == fold, "hold", "train"))
act = np.array(["train"] * n, dtype=object); act[sp.sid.values] = sp.fold.values; exp = expected(FOLD)
check("S3 full-sid equality with expected labels", (act == exp).all(), f"mismatch {int((act != exp).sum())}")
tr = act == "train"
check("S3 no train sid in an NP-example group / held-out fold", not (tr & j.identity_group.isin(np_groups).values).any() and not (tr & (j.fold_identity.values == FOLD)).any())
sa = json.load(open(os.path.join(PKG, "SPLIT_AUDIT.json"), encoding="utf-8"))["input_sha256"]; mi = json.load(open(os.path.join(PKG, "MODEL_INPUTS.json"), encoding="utf-8"))
h_ts, h_st = sha(ts_path), sha(FOLDS); h_bits_run, h_bits_pkg = sha(os.path.realpath(os.path.join(WD, "fp_bits.npy"))), sha(os.path.join(PKG, "fp_bits.npy"))
check("S4 train_structs sha == public audit", h_ts == next(v for k, v in sa.items() if k.endswith("train_structs.parquet")), h_ts[:16])
check("S4 structures sha == public audit", h_st == next(v for k, v in sa.items() if k.endswith("structures.parquet")), h_st[:16])
check("S4 fp_bits (training) == package == MODEL_INPUTS", h_bits_run == h_bits_pkg == mi["fp_bits_sha256"], h_bits_run[:16])
p0 = pd.read_parquet(os.path.join(PKG, "split.parquet")); e0 = expected(0); r0 = pd.DataFrame(dict(sid=j.sid.values, fold=e0)); r0 = r0[r0.fold != "train"].reset_index(drop=True)
check("S4 fold-0 rule reproduces the package split", len(p0) == len(r0) and (p0.sid.values == r0.sid.values).all() and (p0.fold.astype(str).values == r0.fold.values).all(), f"package {len(p0)} rebuilt {len(r0)}")
code = {f: sha(os.path.join(PKG, f)) for f in ("train_fivefold.py", "train_fpnet.py", "make_split.py")}
out = dict(passed=not fail, failed=fail, held_out_fold=FOLD, n_structures=n, labels={k: int(v) for k, v in pd.Series(act).value_counts().items()}, np_groups=len(np_groups),
           sha256=dict(split=sha(sp_path), train_structs=h_ts, structures=h_st, fp_bits=h_bits_run, **{f"code_{k}": v for k, v in code.items()}), split_path=sp_path, input_dir=src)
json.dump(out, open(os.path.join(RUN, "split_audit.json"), "w"), indent=2); print(json.dumps(out)); sys.exit(1 if fail else 0)
