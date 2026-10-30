"""141 reader (141_prereg_gl_retrieval.md §3; written before any A3 number). Per cell, gl_only_eval.py v2.1 compares two GL runs on the same runner
input (view c2, full roster, comparability enforced); here C0' vs A3 and A2 vs A3 (and C0' vs A2, descriptive).
Cells: f1G = run_f1dev G_tims_crosslib, f2G = run_f2dev G_tims_crosslib, npH = run_np053_f1dev NP_H, f1D = run_f1dev D_np_single, panel = run_panel_fe
P_np250. GL files: data/glt/stage2_gl/gl_<cell>_c0prime.json (C0'), data/glt/stage2_a2/gl_<cell>_A2.json (A2), data/glt/a3/gl_<cell>_{c0prime,A2,A3}.json
for cells scored in 141 (f2G C0' / A2 and every A3).
Gate (identity bootstrap 4,000, seed 141):
  primary  : f1G + f2G pooled (200 molecules) rr_form(A3) - rr_form(C0') >= +0.01 and 95% lower > 0;
  objective: same 200 molecules rr_form(A3) - rr_form(A2) point estimate > 0 (interval descriptive; "the objective helped" only if lower > 0);
  costs    : lower >= -0.01 for rr_form of npH and f1D, rr_gl (A3 - C0') of f1G, f2G, npH, f1D and panel.
Checks (STOP): the A3 manifest hashes, the export checks, every cell table = its full roster. Writes data/glt/a3/reading.md / .json.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/glt/x141_read.py"""
import hashlib, json, os, subprocess, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); G = os.path.join(ROOT, "data/glt"); B = os.path.join(ROOT, "experiments/b1_baseline"); A3 = os.path.join(G, "a3")
def stop(m): sys.exit(f"STOP (141 check): {m}")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
for ln in open(os.path.join(A3, "manifest.txt")):
    h, f = ln.split()
    if sha(os.path.join(ROOT, f)) != h: stop(f"{f} differs from the A3 manifest")
sc = json.load(open(os.path.join(A3, "A3_scope.json"))); ck = json.load(open(os.path.join(A3, "check10.json")))
if sc["n_frozen_changed"] != 0 or sc["trainable_changed"] == 0 or ck["differing"] == 0 or ck["A3_missing"] != 0: stop("export checks")
CELLS = {"f1G": ("run_f1dev", "G_tims_crosslib", "eval_set_f1/p2_molecules.csv"), "f2G": ("run_f2dev", "G_tims_crosslib", "eval_set_f2/p2_molecules.csv"),
         "npH": ("run_np053_f1dev", "NP_H", "np053_f1dev/p2_molecules.csv"), "f1D": ("run_f1dev", "D_np_single", "eval_set_f1/p2_molecules.csv"),
         "panel": ("run_panel_fe", "P_np250", "panel_np250/p1_molecules.csv")}
def glf(cell, tag):
    p = os.path.join(A3, f"gl_{cell}_{tag}.json")
    if os.path.exists(p): return p
    return os.path.join(G, "stage2_gl", f"gl_{cell}_c0prime.json") if tag == "c0prime" else os.path.join(G, "stage2_a2", f"gl_{cell}_A2.json")
def run_pair(cell, ta, tb):
    run, s, csv = CELLS[cell]; out = os.path.join(A3, f"read_{cell}_{ta}_vs_{tb}")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "experiments/glt/gl_only_eval.py"), "--run", os.path.join(B, run), "--set", s, "--eval_csv", os.path.join(B, csv),
                        "--gl_a", glf(cell, ta), "--gl_b", glf(cell, tb), "--views", "c2", "--out", out], capture_output=True, text=True)
    if r.returncode != 0: stop(f"gl_only_eval {cell} {ta} vs {tb}: {(r.stdout + r.stderr)[-400:]}")
    T = pd.read_csv(out + ".csv"); ev = pd.read_csv(os.path.join(B, csv)); n = int((ev.set.astype(str) == s).sum())
    if len(T) != n or T.molecule.astype(str).duplicated().any(): stop(f"{cell}: rows {len(T)} != roster {n}")
    return T
rng = np.random.default_rng(141)
def boot(d):
    d = np.asarray(d, float)
    if not np.isfinite(d).all(): stop("non-finite differences")
    bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]); return float(d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), len(d)
T = {(c, p): run_pair(c, *p) for c in CELLS for p in (("c0prime", "A3"), ("A2", "A3"), ("c0prime", "A2"))}
dd = lambda c, p, met: (T[(c, p)][f"{met}_B"] - T[(c, p)][f"{met}_A"]).values
prim = boot(np.concatenate([dd("f1G", ("c0prime", "A3"), "rr_form"), dd("f2G", ("c0prime", "A3"), "rr_form")]))
obj = boot(np.concatenate([dd("f1G", ("A2", "A3"), "rr_form"), dd("f2G", ("A2", "A3"), "rr_form")]))
costs = {"rr_form npH": boot(dd("npH", ("c0prime", "A3"), "rr_form")), "rr_form f1D": boot(dd("f1D", ("c0prime", "A3"), "rr_form"))}
for c in CELLS: costs[f"rr_gl {c}"] = boot(dd(c, ("c0prime", "A3"), "rr_gl"))
desc = {f"A2-C0' rr_form {c}": boot(dd(c, ("c0prime", "A2"), "rr_form")) for c in CELLS}
desc.update({f"A3-C0' rr_form {c}": boot(dd(c, ("c0prime", "A3"), "rr_form")) for c in CELLS})
gate = prim[0] >= 0.01 and prim[1] > 0 and obj[0] > 0 and all(v[1] >= -0.01 for v in costs.values())
L = ["# 141 reading: A3 (retrieval objective) vs C0' / A2, GL-only, view c2, full rosters", "",
     f"- **primary f1G + f2G rr_form A3 - C0': {prim[0]:+.4f} [{prim[1]:+.4f}, {prim[2]:+.4f}] (n {prim[3]})**",
     f"- **objective f1G + f2G rr_form A3 - A2: {obj[0]:+.4f} [{obj[1]:+.4f}, {obj[2]:+.4f}] (n {obj[3]})**", "", "| cost / description | diff | 95% | n |", "|---|---:|---|---:|"]
L += [f"| {k} | {v[0]:+.4f} | [{v[1]:+.4f}, {v[2]:+.4f}] | {v[3]} |" for k, v in {**costs, **desc}.items()]
L += ["", f"- **Gate: {'PASS -> one-shot confirmation on a new unused timsTOF set (separate freeze)' if gate else 'NO'}**"]
open(os.path.join(A3, "reading.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(gate="PASS" if gate else "NO", primary=prim, objective=obj, costs=costs, description=desc, reader_sha256=sha(os.path.abspath(__file__))), open(os.path.join(A3, "reading.json"), "w"), indent=1)
print("\n".join(L))
