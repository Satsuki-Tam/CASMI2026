"""Compare two make_eval_test output dirs (test.parquet rows/columns, masks, solution). Usage: python compare_eval_test_dirs.py DIR_A DIR_B"""
import sys, json, os, polars as pl
A, B = sys.argv[1], sys.argv[2]
REQUIRED = ("test.parquet", "solution.csv", "exclude_rows_c1.json", "exclude_identities_c2.json", "mask_c1.json", "mask_c2.json", "eval_test_manifest.json")
missing = [f"{d}/{f}" for d in (A, B) for f in REQUIRED if not os.path.exists(f"{d}/{f}")]
if missing: print("MISSING FILES:", missing); sys.exit(2)
ok = True
a = pl.read_parquet(f"{A}/test.parquet").sort("spectrum_row"); b = pl.read_parquet(f"{B}/test.parquet").sort("spectrum_row")
print("rows", a.height, b.height, "columns equal", a.columns == b.columns)
same = a.height == b.height and a.columns == b.columns and all(a[c].to_list() == b[c].to_list() for c in a.columns)
print("TEST.PARQUET IDENTICAL" if same else "TEST.PARQUET DIFFERS"); ok &= same
if not same and a.columns == b.columns:
    for c in a.columns:
        if a[c].to_list() != b[c].to_list(): print("  differing column:", c)
def canon(o):   # masks: per-molecule row lists are consumed as sets by the pipeline -> compare order-independently
    if isinstance(o, dict): return {k: (sorted(v) if k == "rows" else canon(v)) for k, v in o.items()}
    if isinstance(o, list): return sorted(o) if all(isinstance(x, (int, str)) for x in o) else [canon(x) for x in o]
    return o
for f in ("exclude_rows_c1.json", "exclude_identities_c2.json", "mask_c1.json", "mask_c2.json"):
    try:
        ja, jb = json.load(open(f"{A}/{f}")), json.load(open(f"{B}/{f}"))
        eq = ja == jb or canon(ja) == canon(jb); ok &= eq
        print(f, "identical" if ja == jb else ("identical as sets (list order differs)" if eq else "DIFFERS"))
    except FileNotFoundError as e: print(f, "missing:", e); ok = False
sa = open(f"{A}/solution.csv").read(); sb = open(f"{B}/solution.csv").read(); print("solution.csv", "identical" if sa == sb else "DIFFERS"); ok &= (sa == sb)
ma, mb = json.load(open(f"{A}/eval_test_manifest.json")), json.load(open(f"{B}/eval_test_manifest.json"))
same_cond = all(ma.get(k) == mb.get(k) for k in ("max_spectra", "sets", "limit", "electron_shift_enveda180_positive")); print("build conditions identical" if same_cond else f"BUILD CONDITIONS DIFFER: {ma} vs {mb}"); ok &= same_cond
print("COMPARE", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
