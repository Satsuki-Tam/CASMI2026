"""115 stage 2 (115_plan.md: pool correspondence; no model, no performance): the simulated positives must index the SAME pool rows as the
training Data (traindata.Data reads work/pool_meta.parquet / pool_fp.npy in row order) and carry the right targets.
Checks (exit 1 on any failure): (1) the training pool_meta (run work/) and the catalog's source pool are byte-identical and pid == row index;
(2) every catalog row equals its pool row (key, smiles, mass, formula, src == 2 = COCONUT-only); (3) the packed FP target pool_fp[pid] equals
casmi.chem.raw_fingerprint(smiles)[fp_bits] recomputed now, on a fixed-hash subset (--n_fp); (4) no catalog key is a known identity key or alias
(train_structs key / rawkey, structures inchikey14 / scorer_key) -> no simulated positive can sit on an excluded alias row (train_fpaug's 'bad'
set for grp < 0 rows) or share an identity with a held-out group; (5) recorded only: catalog scorer-key overlap with every development /
confirmation selection CSV. Usage (.venv, Spark): python -I stage2_check.py <run dir with work/> <catalog dir> <structures.parquet> <code dir>
<fp_bits.npy> <out.json> [--n_fp 2000] [--csvs a.csv b.csv ...]"""
import argparse, glob, hashlib, json, os, sys
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("cat"); ap.add_argument("folds"); ap.add_argument("code"); ap.add_argument("bits"); ap.add_argument("out")
ap.add_argument("--n_fp", type=int, default=2000); ap.add_argument("--csvs", nargs="*", default=[]); ap.add_argument("--pool_src", default="")
a = ap.parse_args(); sys.path.insert(0, a.code)
from casmi import chem
res, fail = {}, []
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True); res[name] = dict(ok=bool(ok), detail=str(detail)); (None if ok else fail.append(name))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
W = os.path.join(a.run, "work"); PM = os.path.join(W, "pool_meta.parquet")
if a.pool_src: check("catalog source pool == training pool (sha256)", sha(a.pool_src) == sha(PM), f"{sha(PM)[:16]}")
P = pd.read_parquet(PM); check("pid == row index", bool((P.pid.values == np.arange(len(P))).all()), f"rows {len(P)}")
C = pd.read_parquet(os.path.join(a.cat, "catalog.parquet"))
R = P.iloc[C.pid.values]
eq = (R.key.astype(str).values == C.key.astype(str).values) & (R.smiles.astype(str).values == C.smiles.astype(str).values) & (np.abs(R.mass.values - C.mass.values) < 1e-6) & (R.formula.astype(str).values == C.formula.astype(str).values)
check("catalog rows equal their pool rows (key, smiles, mass, formula)", bool(eq.all()), f"{int(eq.sum())}/{len(C)}")
check("catalog rows are COCONUT-only (src == 2)", bool((R.src.values == 2).all()), f"{int((R.src.values == 2).sum())}/{len(C)}")
B = np.load(a.bits, allow_pickle=False); PF = np.load(os.path.join(W, "pool_fp.npy"), mmap_mode="r", allow_pickle=False)
sub = C.assign(h=[hashlib.sha256(("fp" + str(k)).encode()).hexdigest() for k in C.key]).sort_values("h").head(a.n_fp)
bad_fp, none_fp = 0, 0
for r in sub.itertuples(index=False):
    fp = chem.raw_fingerprint(str(r.smiles))
    if fp is None: none_fp += 1; continue
    if not np.array_equal(np.packbits(fp[B]), np.asarray(PF[int(r.pid)])): bad_fp += 1
check("pool FP target == recomputed raw_fingerprint[fp_bits]", bad_fp == 0 and none_fp == 0, f"checked {len(sub)}, mismatched {bad_fp}, unparsable {none_fp}")
ts = pd.read_parquet(os.path.join(W, "train_structs.parquet"), columns=["key", "rawkey", "inchikey14"])
st = pd.read_parquet(a.folds, columns=["inchikey14", "scorer_key"])
known = set(ts.key.astype(str)) | set(ts.rawkey.astype(str)) | set(ts.inchikey14.astype(str)) | set(st.inchikey14.astype(str)) | set(st.scorer_key.astype(str))
hit = C.key.astype(str).isin(known)
check("no catalog key is a known identity key / alias", not bool(hit.any()), f"{int(hit.sum())} of {len(C)}")
ov = {}
for p in a.csvs:
    for f in glob.glob(p):
        e = pd.read_csv(f, usecols=lambda c: c in ("scorer_key", "raw_key", "molecule"))
        ks = set(e.get("scorer_key", pd.Series(dtype=str)).astype(str)) | set(e.get("raw_key", pd.Series(dtype=str)).astype(str))
        ov[f] = int(C.key.astype(str).isin(ks).sum())
res["overlap_with_selection_csvs (recorded only)"] = ov; print("overlap (recorded):", json.dumps(ov), flush=True)
res["passed"] = not fail; json.dump(res, open(a.out, "w"), indent=1)
print("STAGE2", "PASS" if not fail else f"FAIL {fail}"); sys.exit(1 if fail else 0)
