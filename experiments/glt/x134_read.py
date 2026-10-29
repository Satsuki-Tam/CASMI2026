"""134 stage 2 reading (134_prereg_glt_stage2.md), written before any stage-2 result. Inputs: data/glt/stage2_gl/gl_<cell>_{c0prime,A1}.json (the
inference runner on the same runner inputs) and the stage2_manifest.txt hashes; per cell gl_only_eval.py (view c2) is run here.
Cells: panel = run_panel_fe P_np250 (panel_np250/p1_molecules.csv), f1G = run_f1dev G_tims_crosslib, npH = run_np053_f1dev NP_H, f1D = run_f1dev
D_np_single (fold-1 selection CSVs). Checks (STOP, exit 1): the manifest hashes match the files; A and B cover the same molecules; the export
checks of the job passed (A1_scope.json, check10.json).
Gate (fixed): primary = mean over the two timsTOF cells (panel, f1G) of the per-cell mean rr_form(B) - rr_form(A) >= +0.01 and its 95% lower
bound > 0 (identity bootstrap within cells, 4,000, seed 134); non-inferiority (lower >= -0.01): rr_form of npH and f1D, rr_gl of all four cells.
Writes data/glt/stage2_reading.md / .json. Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/glt/x134_read.py"""
import hashlib, json, os, subprocess, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); G = os.path.join(ROOT, "data/glt"); B = os.path.join(ROOT, "experiments/b1_baseline")
def stop(m): sys.exit(f"STOP (134 check): {m}")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
for ln in open(os.path.join(G, "stage2_manifest.txt")):
    h, f = ln.split(); p = f if os.path.isabs(f) else os.path.join(ROOT, f)
    if sha(p) != h: stop(f"{f} differs from the manifest")
sc = json.load(open(os.path.join(G, "ckpt/A1_scope.json"))); ck = json.load(open(os.path.join(G, "stage2_gl/check10.json")))
if sc["n_frozen_changed"] != 0 or sc["trainable_changed"] == 0 or ck["differing"] == 0 or ck["A1_missing"] != 0: stop("export checks")
CELLS = {"panel": ("run_panel_fe", "P_np250", "panel_np250/p1_molecules.csv"), "f1G": ("run_f1dev", "G_tims_crosslib", "eval_set_f1/p2_molecules.csv"),
         "npH": ("run_np053_f1dev", "NP_H", "np053_f1dev/p2_molecules.csv"), "f1D": ("run_f1dev", "D_np_single", "eval_set_f1/p2_molecules.csv")}
R = {}
for c, (run, s, csv) in CELLS.items():
    out = os.path.join(G, "stage2_gl", f"read_{c}")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "experiments/glt/gl_only_eval.py"), "--run", os.path.join(B, run), "--set", s, "--eval_csv", os.path.join(B, csv),
                        "--gl_a", os.path.join(G, "stage2_gl", f"gl_{c}_c0prime.json"), "--gl_b", os.path.join(G, "stage2_gl", f"gl_{c}_A1.json"), "--views", "c2", "--out", out], capture_output=True, text=True)
    if r.returncode != 0: stop(f"gl_only_eval {c}: {r.stderr[-300:]}")
    R[c] = pd.read_csv(out + ".csv")
rng = np.random.default_rng(134)
def cell_boot(c, met):
    d = (R[c][f"{met}_B"] - R[c][f"{met}_A"]).values.astype(float); d = d[np.isfinite(d)]
    return float(d.mean()), np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]), len(d)
lo = lambda b: float(np.percentile(b, 2.5)); hi = lambda b: float(np.percentile(b, 97.5))
pp, bp, np_ = cell_boot("panel", "rr_form"); pg, bg, ng = cell_boot("f1G", "rr_form"); prim = 0.5 * (pp + pg); bprim = 0.5 * (bp + bg)
noninf = {}
for c in ("npH", "f1D"): m_, b_, n_ = cell_boot(c, "rr_form"); noninf[f"rr_form {c}"] = (m_, lo(b_), hi(b_), n_)
for c in CELLS: m_, b_, n_ = cell_boot(c, "rr_gl"); noninf[f"rr_gl {c}"] = (m_, lo(b_), hi(b_), n_)
gate = prim >= 0.01 and lo(bprim) > 0 and all(v[1] >= -0.01 for v in noninf.values())
L = ["# 134 stage 2 reading: GLACIER A1 (intensity side, timsTOF) - C0' (released), GL-only, view c2", "",
     f"- **primary (timsTOF cells panel + f1G, rr_form B - A): {prim:+.4f} [{lo(bprim):+.4f}, {hi(bprim):+.4f}]** (panel {pp:+.4f}, n {np_}; f1G {pg:+.4f}, n {ng})", "",
     "| non-inferiority | B - A | 95% |", "|---|---:|---|"] + [f"| {k} | {v[0]:+.4f} | [{v[1]:+.4f}, {v[2]:+.4f}] (n {v[3]}) |" for k, v in noninf.items()]
L += ["", f"- **Gate: {'PASS -> stage 3 (main output connection, separate registration)' if gate else 'NO'}**", "", "## per-cell tables (gl_only_eval.py)"]
for c in CELLS: L += ["", open(os.path.join(G, "stage2_gl", f"read_{c}.md"), encoding="utf-8").read()]
open(os.path.join(G, "stage2_reading.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(dict(gate=("PASS" if gate else "NO"), primary=prim, primary_lower=lo(bprim), noninferiority={k: v[:3] for k, v in noninf.items()}, reader_sha256=sha(os.path.abspath(__file__))),
          open(os.path.join(G, "stage2_reading.json"), "w"), indent=1)
print("\n".join(L[:14]))
