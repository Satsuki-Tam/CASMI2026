"""115 v2 stage 1 (reports/agent_review/115_plan.md, v2 sections), written before any R / A model exists. Three arms built with the SAME code on
the SAME system: P0 = the public fpnet_fold1 (fold-1 slot, sha 1739d568...) rebuilt (run_<tag>_p0e115), R = the real-only fine-tuned final
(run_<tag>_re115), A = the simulation-mixed final (run_<tag>_ae115); each table = b1_features --fold_safe <arm slot> whose fpnet_fold0.pt is
the arm's checkpoint (fp_bits and the rest identical). Measure = the 110 FP proxy: b1_features truth_fp_rank over the raw-InChIKey14 window
(best alias rank, pessimistic ties; -1 = not in the window -> RR 0); C2-ineligible truths (reach_external_b1 False) count as unreached.
Checks before any number (STOP): ck115 PASS for R and A (final sha256 from <tag>_ck115.json); manifests: no extra checkpoint, fpnet sha = slot /
R final / A final, every other setting equal; per stratum the same molecule set; per molecule the same n_unique, reach_external_b1,
truth_in_window and n_query in all arms; ranks finite, -1 or 1..n_unique.
Gate (115_plan v2, Codex 118): dFP(A - R) > 0 AND dFP(A - P0) > 0, dFP = 1/4 dMRR(np053f1dev NP_H) + 1/4 dMRR(np053f1dev NP_N) + 1/2 dMRR(f1dev
D_np_single); otherwise stop. Diagnostics only: per-stratum FP MRR / top-1 of the three arms, rows where the v8w7a main misses rank 1
(diag/r102), and the truth's M_all membership / simulated exposure in A (consumed-jobs ledger x jobs_pid) -- never used for the decision.
Usage (Spark, experiments/b1_baseline): python -X utf8 x115_stage1.py"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
E = os.path.join(ROOT, "experiments", "e115"); SLOT = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4"
ARMS = ("p0", "r", "a")
TAGS = {"f1dev": ("run_f1dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
        "np053f1dev": ("run_np053_f1dev", ["NP_H", "NP_X", "NP_N"])}
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv"}


def stop(msg): sys.exit(f"STOP (115 stage 1): {msg}")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


CK = {}
for arm, run, tag in (("r", "runR", "e115R"), ("a", "runA", "e115A")):
    p = os.path.join(E, run, f"{tag}_ck115.json")
    if not os.path.exists(p): stop(f"missing completion check {p}")
    c = json.load(open(p))
    if not c.get("passed"): stop(f"completion check failed for {arm}")
    CK[arm] = c["final_sha256"]
WANT = {"p0": SLOT, "r": CK["r"], "a": CK["a"]}
for tag in TAGS:
    M = {arm: json.load(open(os.path.join(HERE, f"run_{tag}_{arm}e115", "b1_features_manifest.json"))) for arm in ARMS}
    for arm in ARMS:
        if M[arm].get("extra_ckpts") != []: stop(f"{tag} {arm}: extra checkpoints {M[arm].get('extra_ckpts')}")
        if M[arm].get("fpnet") != WANT[arm]: stop(f"{tag} {arm}: fpnet sha {M[arm].get('fpnet')} != {WANT[arm]}")
    for arm in ("r", "a"):
        diff = {k for k in set(M["p0"]) | set(M[arm]) if k not in ("fpnet", "seconds") and M["p0"].get(k) != M[arm].get(k)}
        if diff: stop(f"{tag}: manifests p0 / {arm} differ in {sorted(diff)}")
rr = lambda r: np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
# truth exposure in A (diagnostic): truth official key -> pool pid -> consumed simulated items
pool = pd.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "pid"]); k2p = dict(zip(pool.key.astype(str), pool.pid.astype(int)))
cat = set(pd.read_parquet(os.path.join(E, "mall", "catalog.parquet"), columns=["pid"]).pid.astype(int))
jp = np.load(os.path.join(E, "mall", "jobs_pid.npy"), allow_pickle=False); cons = np.load(os.path.join(E, "runA", "e115A_consumed_jobs.npy"), allow_pickle=False)
expo = np.bincount(jp[cons > 0], weights=cons[cons > 0].astype(float), minlength=len(pool))
rows = []
for tag, (old, sets) in TAGS.items():
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[tag])); ev["molecule"] = ev.molecule.astype(str); sk = dict(zip(ev.molecule, ev.scorer_key.astype(str)))
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R = R[R.view == "c2"].set_index(["set", "molecule"]).main
    for s in sets:
        L_ = {arm: pd.read_csv(os.path.join(HERE, f"run_{tag}_{arm}e115", f"b1_molecules_{s}.csv")) for arm in ARMS}
        for d in L_.values(): d["molecule"] = d.molecule.astype(str)
        ms = set(L_["p0"].molecule)
        if any(set(d.molecule) != ms or d.molecule.duplicated().any() for d in L_.values()): stop(f"{tag} {s}: molecule sets differ")
        cols = ["molecule", "truth_fp_rank", "n_unique", "reach_external_b1", "truth_in_window", "n_query"]
        z = L_["p0"][cols].rename(columns={c: c + "_p0" for c in cols[1:]})
        for arm in ("r", "a"):
            z = z.merge(L_[arm][cols].rename(columns={c: c + "_" + arm for c in cols[1:]}), on="molecule", validate="one_to_one")
        for c_ in ("n_unique", "reach_external_b1", "truth_in_window", "n_query"):
            for arm in ("r", "a"):
                if (z[f"{c_}_p0"].astype(str) != z[f"{c_}_{arm}"].astype(str)).any(): stop(f"{tag} {s}: {c_} differs between p0 and {arm}")
        for arm in ARMS:
            v_ = pd.to_numeric(z[f"truth_fp_rank_{arm}"], errors="coerce").astype(float); n_ = pd.to_numeric(z[f"n_unique_{arm}"], errors="coerce").astype(float)
            ok_ = np.isfinite(v_) & (v_ == np.round(v_)) & ((v_ == -1) | ((v_ >= 1) & (v_ <= n_)))
            if not ok_.all(): stop(f"{tag} {s} {arm}: truth_fp_rank outside -1 / 1..n_unique ({int((~ok_).sum())} rows)")
        ok = z.reach_external_b1_p0.astype(bool).values
        for arm in ARMS: z[f"r_{arm}"] = np.where(ok, z[f"truth_fp_rank_{arm}"].values.astype(float), -1.0)
        pid = z.molecule.map(lambda m: k2p.get(sk.get(m, ""), -1)).values.astype(int)
        z["truth_in_mall"] = [p in cat for p in pid]; z["truth_sim_exposure"] = [float(expo[p]) if p >= 0 else 0.0 for p in pid]
        z["tag"] = tag; z["set"] = s; z["main_c2"] = [float(R.get((s, m), np.nan)) for m in z.molecule]; rows.append(z)
Z = pd.concat(rows, ignore_index=True); Z.to_csv(os.path.join(HERE, "diag/x115_stage1.csv"), index=False)


def dm(tag, s, x, y):
    d = Z[(Z.tag == tag) & (Z.set == s)]
    if not len(d): stop(f"empty cell {tag} {s}")
    return float(rr(d[f"r_{x}"].values).mean() - rr(d[f"r_{y}"].values).mean())


dfp = lambda x, y: 0.25 * dm("np053f1dev", "NP_H", x, y) + 0.25 * dm("np053f1dev", "NP_N", x, y) + 0.5 * dm("f1dev", "D_np_single", x, y)
d_ar, d_ap = dfp("a", "r"), dfp("a", "p0"); gate = d_ar > 0 and d_ap > 0
L = ["# 115 stage 1: FP-only rank of the truth over the whole window (P0 / R / A rebuilt on the same system); C2-eligible truths only", "",
     f"- R final {CK['r'][:16]}, A final {CK['a'][:16]}, P0 = fold-1 slot {SLOT[:16]}",
     f"- **dFP(A - R) = {d_ar:+.5f}, dFP(A - P0) = {d_ap:+.5f} -> gate {'PASS (both > 0) -> stage 3' if gate else 'NO -> stop'}**", "",
     "| stratum | n | FP MRR@25 P0 / R / A | top-1 P0 / R / A | truth in M_all | truth simulated in A (n) | FP MRR A - R: truth simulated / not |", "|---|---:|---|---|---:|---:|---|"]
for (tag, s), d in Z.groupby(["tag", "set"], sort=False):
    sim = (d.truth_sim_exposure > 0).values; dd = rr(d.r_a.values) - rr(d.r_r.values)
    L.append(f"| {tag} {s} | {len(d)} | {rr(d.r_p0.values).mean():.4f} / {rr(d.r_r.values).mean():.4f} / {rr(d.r_a.values).mean():.4f} | "
             f"{(d.r_p0 == 1).mean():.3f} / {(d.r_r == 1).mean():.3f} / {(d.r_a == 1).mean():.3f} | {d.truth_in_mall.mean():.2f} | {int(sim.sum())} | "
             f"{(dd[sim].mean() if sim.any() else float('nan')):+.4f} / {(dd[~sim].mean() if (~sim).any() else float('nan')):+.4f} |")
open(os.path.join(HERE, "diag/x115_stage1.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
