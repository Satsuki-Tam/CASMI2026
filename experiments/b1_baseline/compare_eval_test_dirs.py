"""Compare two make_eval_test output dirs (test.parquet rows/columns, masks, solution). Usage: python compare_eval_test_dirs.py DIR_A DIR_B"""
import sys, json, polars as pl
A, B = sys.argv[1], sys.argv[2]
a = pl.read_parquet(f"{A}/test.parquet").sort("spectrum_row"); b = pl.read_parquet(f"{B}/test.parquet").sort("spectrum_row")
print("rows", a.height, b.height, "columns equal", a.columns == b.columns)
same = a.height == b.height and a.columns == b.columns and all(a[c].to_list() == b[c].to_list() for c in a.columns)
print("TEST.PARQUET IDENTICAL" if same else "TEST.PARQUET DIFFERS")
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
        print(f, "identical" if ja == jb else ("identical as sets (list order differs)" if canon(ja) == canon(jb) else "DIFFERS"))
    except FileNotFoundError as e: print(f, "missing:", e)
sa = open(f"{A}/solution.csv").read(); sb = open(f"{B}/solution.csv").read(); print("solution.csv", "identical" if sa == sb else "DIFFERS")
