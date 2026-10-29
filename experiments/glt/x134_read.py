"""134 stage 2 reading (134_prereg_glt_stage2.md v2), written before any stage-2 result. Inputs: data/glt/stage2_gl/gl_<cell>_c0prime.json (C0')
and data/glt/stage2_a2/gl_<cell>_A2.json (A2) -- the inference runner on the same runner inputs and batch plan -- plus their manifest and the A2
export checks; per cell gl_only_eval.py v2 (view c2, full roster, A / B comparability enforced) is run here.
Cells (fold-1 selection CSVs): f1G = run_f1dev G_tims_crosslib (timsTOF; unseen by base GLACIER and by the adaptation), npH = run_np053_f1dev
NP_H, f1D = run_f1dev D_np_single, panel = run_panel_fe P_np250 (timsTOF NP, mostly MSG-seen by base GLACIER: description / protection only).
Checks (STOP, exit 1): manifest hashes; export checks (frozen bit-equal, trainable changed, strict runner reload, scores differ from C0' on the
10-molecule check); every cell's rows = its full selection roster.
Gate (fixed; identity bootstrap within the cell, 4,000, seed 134):
  primary: f1G rr_form(A2) - rr_form(C0') >= +0.01 and 95% lower > 0;
  costs (lower >= -0.01): rr_form of npH and f1D; rr_gl of each of the four cells (incl. the panel).
Panel rr_form is reported, never used to compensate G. Writes data/glt/stage2a2_reading.md / .json; exit 0 also on NO.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/glt/x134_read.py"""
import hashlib, json, os, subprocess, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); G = os.path.join(ROOT, "data/glt"); B = os.path.join(ROOT, "experiments/b1_baseline")
def stop(m): sys.exit(f"STOP (134 check): {m}")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
for ln in open(os.path.join(G, "stage2_a2", "manifest.txt")):
    h, f = ln.split(); p = f if os.path.isabs(f) else os.path.join(ROOT, f)
    if sha(p) != h: stop(f"{f} differs from the manifest")
sc = json.load(open(os.path.join(G, "stage2_a2", "A2_scope.json"))); ck = json.load(open(os.path.join(G, "stage2_a2", "check10.json")))
if sc["n_frozen_changed"] != 0 or sc["trainable_changed"] == 0 or ck["differing"] == 0 or ck["A2_missing"] != 0: stop("export checks")
CELLS = {"f1G": ("run_f1dev", "G_tims_crosslib", "eval_set_f1/p2_molecules.csv"), "npH": ("run_np053_f1dev", "NP_H", "np053_f1dev/p2_molecules.csv"),
         "f1D": ("run_f1dev", "D_np_single", "eval_set_f1/p2_molecules.csv"), "panel": ("run_panel_fe", "P_np250", "panel_np250/p1_molecules.csv")}
R = {}
for c, (run, s, csv) in CELLS.items():
    out = os.path.join(G, "stage2_a2", f"read_{c}")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "experiments/glt/gl_only_eval.py"), "--run", os.path.join(B, run), "--set", s, "--eval_csv", os.path.join(B, csv),
                        "--gl_a", os.path.join(G, "stage2_gl", f"gl_{c}_c0prime.json"), "--gl_b", os.path.join(G, "stage2_a2", f"gl_{c}_A2.json"), "--views", "c2", "--out", out], capture_output=True, text=True)
    if r.returncode != 0: stop(f"gl_only_eval {c}: {(r.stdout + r.stderr)[-400:]}")
    R[c] = pd.read_csv(out + ".csv")
    ev = pd.read_csv(os.path.join(B, csv)); n_roster = int((ev.set.astype(str) == s).sum())
    if len(R[c]) != n_roster or R[c].molecule.astype(str).duplicated().any(): stop(f"{c}: rows {len(R[c])} != roster {n_roster} or duplicates")
rng = np.random.default_rng(134)
def cell(c, met):
    d = (R[c][f"{met}_B"] - R[c][f"{met}_A"]).values.astype(float)
    if not np.isfinite(d).all(): stop(f"{c} {met}: non-finite differences")
    bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]); return float(d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), len(d)
prim = cell("f1G", "rr_form")
costs = {"rr_form npH": cell("npH", "rr_form"), "rr_form f1D": cell("f1D", "rr_form")}
for c in CELLS: costs[f"rr_gl {c}"] = cell(c, "rr_gl")
desc = {"rr_form panel": cell("panel", "rr_form")}
gate = prim[0] >= 0.01 and prim[1] > 0 and all(v[1] >= -0.01 for v in costs.values())
L = ["# 134 stage 2 reading (v2): GLACIER A2 (inten_encoder / inten_decoder / output_map, end-to-end intensity loss, timsTOF) - C0' (released), GL-only, view c2, full rosters", "",
     f"- **primary f1G rr_form: {prim[0]:+.4f} [{prim[1]:+.4f}, {prim[2]:+.4f}] (n {prim[3]})**", "", "| cost / description | A2 - C0' | 95% | n |", "|---|---:|---|---:|"]
L += [f"| {k} | {v[0]:+.4f} | [{v[1]:+.4f}, {v[2]:+.4f}] | {v[3]} |" for k, v in {**costs, **desc}.items()]
L += ["", f"- **Gate: {'PASS -> stage 3 (main-output connection, separate registration)' if gate else 'NO'}**", "", "## per-cell tables (gl_only_eval.py v2)"]
for c in CELLS: L += ["", open(os.path.join(G, "stage2_a2", f"read_{c}.md"), encoding="utf-8").read()]
open(os.path.join(G, "stage2a2_reading.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(gate=("PASS" if gate else "NO"), primary=prim, costs=costs, description=desc, reader_sha256=sha(os.path.abspath(__file__)),
               evaluator_sha256=sha(os.path.join(ROOT, "experiments/glt/gl_only_eval.py"))), open(os.path.join(G, "stage2a2_reading.json"), "w"), indent=1)
print("\n".join(L[:16]))
