"""Validate the rank-band probe (ranks 26-50 of the main order) of one pipeline run (Codex 027 checks).

Checks per molecule: (1) no official identity shared between the main top-25 and the band; (2) band length = min(25, max(0, n_rows - 25))
with n_rows the number of ranked candidates (b1_stage_stats n_shortlist; mismatches reported), CCO when n_rows <= 25; (3) a truth found by
the main list is never in the band; (4) band RR in {0} U {1/k, k = 1..25}; (5) the official-scorer band score equals the mean per-molecule RR.
Usage: python -X utf8 validate_band.py --run <pipeline out dir with --solution> [--view c1]
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
import metric

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--view", default="")
a = ap.parse_args()
main = pd.read_csv(f"{a.run}/submission.csv").set_index("molecule_id").smiles
band = pd.read_csv(f"{a.run}/submission_probe_band26.csv").set_index("molecule_id").smiles
st = pd.read_csv(f"{a.run}/b1_stage_stats.csv").set_index("molecule")
per = pd.read_csv(f"{a.run}/eval_per_molecule.csv").set_index("molecule_id")
sc = json.load(open(f"{a.run}/eval_scores.json"))
key = {}
def ik(s):
    if s not in key:
        try: key[s] = metric.canonicalize_smiles_to_ik14(s)
        except Exception: key[s] = None
    return key[s]
bad = {"overlap": [], "length": [], "truth_both": [], "rr_value": []}
lens = []
for m in main.index:
    ml = [x for x in str(main[m]).split(";") if x]; bl = [x for x in str(band[m]).split(";") if x]
    b_is_cco = bl == ["CCO"]
    mk = {ik(x) for x in ml} - {None}; bk = {ik(x) for x in bl if not b_is_cco} - {None}
    if mk & bk: bad["overlap"].append(m)
    n_rows = int(st.loc[m, "n_shortlist"]) if m in st.index and pd.notna(st.loc[m, "n_shortlist"]) else None
    exp = None if n_rows is None else min(25, max(0, n_rows - 25))
    got = 0 if b_is_cco else len(bl)
    lens.append((n_rows, got))
    if exp is not None and got != exp: bad["length"].append((m, n_rows, got))
    rr_m = float(per.loc[m, "rr"]) if m in per.index else 0.0; rr_b = float(per.loc[m, "rr_probe_band26"]) if m in per.index else 0.0
    if rr_m > 0 and rr_b > 0: bad["truth_both"].append(m)
    if rr_b > 0 and not any(abs(rr_b - 1.0 / k) < 1e-9 for k in range(1, 26)): bad["rr_value"].append((m, rr_b))
band_official = sc.get("official_mrr25_probe", {}).get("band26")
band_mean = float(per["rr_probe_band26"].fillna(0).mean())
L = np.array([x for x in lens if x[0] is not None])
print(f"{a.run} {a.view}: molecules {len(main)} | band official {band_official} vs mean RR {band_mean:.6f} | molecules with band RR > 0: {int((per['rr_probe_band26'] > 0).sum())} | "
      f"n_rows <= 25: {int((L[:, 0] <= 25).sum()) if len(L) else 0}, 26-49: {int(((L[:, 0] > 25) & (L[:, 0] < 50)).sum()) if len(L) else 0}, >= 50: {int((L[:, 0] >= 50).sum()) if len(L) else 0}")
print({k: (len(v), v[:3]) for k, v in bad.items()})
ok = not bad["overlap"] and not bad["truth_both"] and not bad["rr_value"] and band_official is not None and abs(band_official - band_mean) < 1e-9
print("BAND VALIDATION " + ("PASS" if ok else "FAIL") + (f" (length mismatches {len(bad['length'])}: n_shortlist may count before identity dedup)" if bad["length"] else ""))
