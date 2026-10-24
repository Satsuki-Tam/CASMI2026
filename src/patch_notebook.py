"""Patch configuration constants inside a Kaggle notebook (.ipynb) by exact string replacement in code cells.

Usage: python -X utf8 src/patch_notebook.py <in.ipynb> <out.ipynb> "OLD=>NEW" ["OLD2=>NEW2" ...]
Each replacement must match exactly once across all code cells (asserted), so edits are explicit and auditable.
"""
import json, sys
src, dst, *reps = sys.argv[1:]
nb = json.load(open(src, encoding="utf-8"))
log = []
for rep in reps:
    old, new = rep.split("=>", 1)
    hits = [(i, "".join(c["source"]).count(old)) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]
    hits = [(i, n) for i, n in hits if n]
    assert len(hits) == 1 and hits[0][1] == 1, f"expected exactly one match for {old!r}, got {hits}"
    i = hits[0][0]
    text = "".join(nb["cells"][i]["source"]).replace(old, new)
    nb["cells"][i]["source"] = text.splitlines(keepends=True)
    log.append(f"cell {i}: {old!r} -> {new!r}")
json.dump(nb, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(log)); print("wrote", dst)
