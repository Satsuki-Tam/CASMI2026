"""110 stage 1 (110_prereg_fpseed.md sections 3-4, amendments after Codex 110 / 112), written before the model exists. Measure (an FP PROXY, named
precisely after Codex 112): b1_features truth_fp_rank = the best rank, among the truth's aliases (raw key or tautomer alias), of f.z over the
RAW-InChIKey14 window of the +-10 ppm search (fp of a raw key = max over its SMILES spellings; other candidates' tautomer aliases may hold
several ranks; ties pessimistic: rank = number of window keys with f.z >= the truth's); -1 = truth not in the window -> RR 0. This is not the
official-identity MRR of the final list. Control = seed 0 alone (public fpnet_fold1 in the fold-1 slot) REBUILT with the same code on the same
system (run_f1dev_s0rep, run_np053f1dev_s0rep); FPavg = the same build with --extra_ckpts <seed-1 final> (1:1 logit average) (run_*_fpavg).
Same molecules (fold 1: f1dev C-G, np053f1dev NP_H/NP_X/NP_N). C2 eligibility: a truth reachable only as a training structure
(reach_external_b1 False) counts as unreached in both tables (no train-only truth revived in the C2 view).
Checks before any number (STOP on failure): manifests (control: no extra checkpoint; FPavg: exactly one extra = the checked seed-1 final, sha256
equal to ckpt_check.json; same fold-1 slot sha 1739d568...; every other setting equal); per molecule, both arms have the same window size
(n_unique), truth_in_window, reach_external_b1 and n_query; ranks are finite integers, -1 or 1..n_unique.
Gate (registered, Codex 110 (4)): dFP = 1/4 dMRR(np053f1dev NP_H) + 1/4 dMRR(np053f1dev NP_N) + 1/2 dMRR(f1dev D_np_single) must be strictly > 0,
else stop the seed line. Diagnostics only: top-1, mean log-rank difference over rows reached in both (with count), other strata, rows where the
v8w7a main misses rank 1 (diag/r102), and the reproduction of the existing tables (run_f1dev / run_np053_f1dev) by the rebuilt control.
Usage (on the Spark, repo root experiments/b1_baseline): python -X utf8 x110_stage1.py"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CK = json.load(open(os.path.join(ROOT, "experiments/fpnet_seed/f1s1/ckpt_check.json")))
if not CK.get("passed"): sys.exit("STOP: ckpt_check did not pass")
PAIRS = {"f1dev": ("run_f1dev_s0rep", "run_f1dev_fpavg", "run_f1dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
         "np053f1dev": ("run_np053f1dev_s0rep", "run_np053f1dev_fpavg", "run_np053_f1dev", ["NP_H", "NP_X", "NP_N"])}
SLOT = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
for tag, (c0, c1, old, sets) in PAIRS.items():
    m0, m1 = (json.load(open(os.path.join(HERE, d, "b1_features_manifest.json"))) for d in (c0, c1))
    if m0.get("extra_ckpts") != [] or len(m1.get("extra_ckpts", [])) != 1: sys.exit(f"STOP: {tag} extra checkpoints {m0.get('extra_ckpts')} / {m1.get('extra_ckpts')}")
    ex = m1["extra_ckpts"][0]; ex = ex if os.path.isabs(ex) else os.path.join(ROOT, ex)
    if os.path.realpath(ex) != os.path.realpath(CK["final"]) or sha(ex) != CK["final_sha256"]: sys.exit(f"STOP: {tag} extra checkpoint is not the checked seed-1 final")
    if m0.get("fpnet") != SLOT or m1.get("fpnet") != SLOT: sys.exit(f"STOP: {tag} fold-1 slot sha {m0.get('fpnet')} / {m1.get('fpnet')}")
    diff = {k for k in set(m0) | set(m1) if k not in ("extra_ckpts", "seconds") and m0.get(k) != m1.get(k)}
    if diff: sys.exit(f"STOP: {tag} manifests differ in {sorted(diff)}")
rr = lambda r: np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
rows, rep = [], []
for tag, (c0, c1, old, sets) in PAIRS.items():
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R = R[R.view == "c2"].set_index(["set", "molecule"]).main
    for s in sets:
        a, b, o = (pd.read_csv(os.path.join(HERE, d, f"b1_molecules_{s}.csv")) for d in (c0, c1, old))
        for d in (a, b, o): d["molecule"] = d.molecule.astype(str)
        if set(a.molecule) != set(b.molecule) or set(a.molecule) != set(o.molecule) or a.molecule.duplicated().any() or b.molecule.duplicated().any(): sys.exit(f"STOP: {tag} {s} molecule sets differ")
        cols = ["molecule", "truth_fp_rank", "n_unique", "reach_external_b1", "truth_in_window", "n_query"]
        z = a[cols].merge(b[cols], on="molecule", suffixes=("_0", "_avg"), validate="one_to_one")
        for c_ in ("n_unique", "reach_external_b1", "truth_in_window", "n_query"):   # Codex 112: same windows / queries / reach in both arms
            if (z[c_ + "_0"].astype(str) != z[c_ + "_avg"].astype(str)).any(): sys.exit(f"STOP: {tag} {s} {c_} differs between the arms")
        for c_, nu_ in (("truth_fp_rank_0", "n_unique_0"), ("truth_fp_rank_avg", "n_unique_avg")):   # Codex 114: finite, -1 or 1..n_unique
            v_ = pd.to_numeric(z[c_], errors="coerce").astype(float); n_ = pd.to_numeric(z[nu_], errors="coerce").astype(float)
            ok_ = np.isfinite(v_) & (v_ == np.round(v_)) & ((v_ == -1) | ((v_ >= 1) & (v_ <= n_)))
            if not ok_.all(): sys.exit(f"STOP: {tag} {s} {c_} outside -1 / 1..n_unique ({int((~ok_).sum())} rows)")
        q = a[cols].merge(o[cols], on="molecule", suffixes=("", "_old"), validate="one_to_one")
        rep.append(f"| {tag} {s} | {len(q)} | {int((q.truth_fp_rank != q.truth_fp_rank_old).sum())} | {int((q.n_unique != q.n_unique_old).sum())} | {int((q.reach_external_b1.astype(bool) != q.reach_external_b1_old.astype(bool)).sum())} |")
        ok = z.reach_external_b1_0.astype(bool).values
        z["r0"] = np.where(ok, z.truth_fp_rank_0.values.astype(float), -1.0); z["r1"] = np.where(ok, z.truth_fp_rank_avg.values.astype(float), -1.0)
        z["tag"] = tag; z["set"] = s; z["main_c2"] = [float(R.get((s, m), np.nan)) for m in z.molecule]; rows.append(z)
Z = pd.concat(rows, ignore_index=True); Z.to_csv(os.path.join(HERE, "diag/x110_stage1.csv"), index=False)
def dm(tag, s):
    d = Z[(Z.tag == tag) & (Z.set == s)]
    if not len(d): sys.exit(f"STOP: empty cell {tag} {s}")
    return float(rr(d.r1.values).mean() - rr(d.r0.values).mean())
dFP = 0.25 * dm("np053f1dev", "NP_H") + 0.25 * dm("np053f1dev", "NP_N") + 0.5 * dm("f1dev", "D_np_single")
L = ["# 110 stage 1: FP-only rank of the truth over the whole window (rebuilt seed 0 vs 1:1 average with seed 1); C2-eligible truths only", "",
     f"- seed-1 final sha256 {CK['final_sha256'][:16]}, step {CK['step']}; fold-1 slot {SLOT[:16]}",
     f"- **dFP = 1/4 dMRR(NP_H) + 1/4 dMRR(NP_N) + 1/2 dMRR(D) = {dFP:+.5f} -> gate {'PASS (> 0) -> stage 3' if dFP > 0 else 'NO -> stop the seed line'}**", "",
     "| stratum | n | window (median) seed0 / avg | FP MRR@25 seed0 | FP MRR@25 avg | top-1 seed0 / avg | mean log-rank diff (reached both, n) | main misses rank 1: FP MRR seed0 / avg (n) |", "|---|---:|---|---:|---:|---|---|---|"]
for (tag, s), d in Z.groupby(["tag", "set"], sort=False):
    r0, r1 = d.r0.values, d.r1.values; both = (r0 > 0) & (r1 > 0); lr = float(np.mean(np.log(r1[both]) - np.log(r0[both]))) if both.any() else float("nan"); mm = (d.main_c2 < 1).values
    L.append(f"| {tag} {s} | {len(d)} | {d.n_unique_0.median():.0f} / {d.n_unique_avg.median():.0f} | {rr(r0).mean():.4f} | {rr(r1).mean():.4f} | {(r0 == 1).mean():.3f} / {(r1 == 1).mean():.3f} | {lr:+.4f} ({int(both.sum())}) | {rr(r0[mm]).mean():.4f} / {rr(r1[mm]).mean():.4f} ({int(mm.sum())}) |")
L += ["", "Reproduction of the existing tables by the rebuilt control (molecules with a different value; diagnostic):", "",
      "| stratum | n | truth_fp_rank | n_unique | reach_external_b1 |", "|---|---:|---:|---:|---:|"] + rep
open(os.path.join(HERE, "diag/x110_stage1.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
