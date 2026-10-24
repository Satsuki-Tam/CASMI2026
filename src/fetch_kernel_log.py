"""List a Kaggle kernel's output files and download only the small ones that match a pattern (default: the execution log and JSON manifests),
instead of `kaggle kernels output`, which pulls every output file (GBs for the B1 kernel).
Usage: python -X utf8 src/fetch_kernel_log.py <owner/slug> <out_dir> [regex]
"""
import os, sys
from kaggle import api

ref, out = sys.argv[1], sys.argv[2]; pat = sys.argv[3] if len(sys.argv) > 3 else r"(\.log|\.json)$"
os.makedirs(out, exist_ok=True)
try:
    lst = api.kernels_list_files(ref)
    files = getattr(lst, "files", None) or (lst.get("files") if isinstance(lst, dict) else lst) or []
    for f in files:
        name = getattr(f, "name", None) or getattr(f, "fileName", None) or (f.get("name") if isinstance(f, dict) else str(f))
        size = getattr(f, "size", None) or getattr(f, "totalBytes", None) or (f.get("size") if isinstance(f, dict) else None)
        print(f"  {name}  {size}")
except Exception as e:
    print("list failed:", repr(e))
res = api.kernels_output(ref, out, force=True, quiet=True, file_pattern=pat)
print("downloaded:", res if not isinstance(res, tuple) else res[0], "->", out)
