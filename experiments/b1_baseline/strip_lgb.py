"""Strip the per-tree statistics that LightGBM does not need for prediction (split_gain, leaf_weight, leaf_count, internal_value, internal_weight,
internal_count) from a text model and rewrite the header's tree_sizes, so that the embedded kernel blob stays under the ~1 MiB notebook limit.
Checks the block segmentation against the original tree_sizes and that predictions are bit-identical on random inputs.
Usage: python -I strip_lgb.py IN.txt OUT.txt"""
import sys, re
import numpy as np, lightgbm as lgb
src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8", newline="").read()
i0 = txt.index("Tree=0\n"); i1 = txt.index("end of trees")
head, body, foot = txt[:i0], txt[i0:i1], txt[i1:]
starts = [m.start() for m in re.finditer(r"(?m)^Tree=\d+\n", body)] + [len(body)]
blocks = [body[starts[k]:starts[k + 1]] for k in range(len(starts) - 1)]
sizes = [int(x) for x in re.search(r"(?m)^tree_sizes=(.*)$", head).group(1).split()]
assert [len(b.encode("utf-8")) for b in blocks] == sizes, "block segmentation does not match tree_sizes"
DROP = ("split_gain=", "leaf_weight=", "leaf_count=", "internal_value=", "internal_weight=", "internal_count=")
nb = ["".join(l for l in b.splitlines(keepends=True) if not l.startswith(DROP)) for b in blocks]
head2 = re.sub(r"(?m)^tree_sizes=.*$", "tree_sizes=" + " ".join(str(len(b.encode("utf-8"))) for b in nb), head)
open(dst, "w", encoding="utf-8", newline="").write(head2 + "".join(nb) + foot)
a = lgb.Booster(model_file=src); b = lgb.Booster(model_file=dst)
rng = np.random.default_rng(0); nf = a.num_feature()
X = rng.normal(0, 3, (20000, nf)); X[rng.random(X.shape) < 0.1] = np.nan
pa, pb = a.predict(X), b.predict(X)
print(f"{src}: bytes {len(txt):,} -> {len(head2 + ''.join(nb) + foot):,}; trees {len(blocks)}; random rows max |diff| {np.abs(pa - pb).max():.3e}, identical {np.array_equal(pa, pb)}")
