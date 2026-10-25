"""Compare two LightGBM text models: same structure (non-numeric tokens, token count) and numeric tokens equal within a relative tolerance.
LightGBM with deterministic=0 and several threads is not bitwise reproducible (summation order); this is the regression check used instead of cmp.
Usage: python model_equiv.py A.txt B.txt [--rtol 1e-9] -> exit 0 if equivalent."""
import re, sys
a, b = open(sys.argv[1]).read().split(), open(sys.argv[2]).read().split()
rtol = float(sys.argv[sys.argv.index("--rtol") + 1]) if "--rtol" in sys.argv else 1e-9
num = re.compile(r"^-?\d+(\.\d+)?([eE][-+]?\d+)?$")
if len(a) != len(b): print(f"DIFFERENT token count {len(a)} vs {len(b)}"); sys.exit(1)
worst, n_num, bad = 0.0, 0, 0
for x, y in zip(a, b):
    xs, ys = x.split("="), y.split("=")
    if len(xs) != len(ys): print("DIFFERENT structure", x[:60], y[:60]); sys.exit(1)
    for u, v in zip(xs, ys):
        if u == v: continue
        uu, vv = u.split(" ") if " " in u else [u], v.split(" ") if " " in v else [v]
        if not (num.match(u) and num.match(v)): print("DIFFERENT non-numeric token", u[:60], v[:60]); sys.exit(1)
        fu, fv = float(u), float(v); n_num += 1
        rel = abs(fu - fv) / max(abs(fu), abs(fv), 1e-300); worst = max(worst, rel); bad += rel > rtol
print(f"tokens {len(a)} | differing numeric tokens {n_num} | max relative difference {worst:.3e} | above rtol {bad}")
sys.exit(1 if bad else 0)
