"""115 v2 stage 1 (reports/agent_review/115_plan.md, v2 sections), written before any R / A model exists; revised after Codex 120 (still before any
R / A model). Three arms built with the SAME code on the SAME system: P0 = the public fpnet_fold1 (fold-1 slot, sha 1739d568...) rebuilt
(run_<tag>_p0e115), R = the real-only fine-tuned final (run_<tag>_re115), A = the simulation-mixed final (run_<tag>_ae115); each table =
b1_features --fold_safe <arm slot> whose fpnet_fold0.pt is the arm's checkpoint (fp_bits and the rest identical). Measure = the 110 FP proxy:
b1_features truth_fp_rank over the raw-InChIKey14 window (best alias rank, pessimistic ties; -1 = not in the window -> RR 0; an EMPTY window,
n_unique 0, carries NaN = -1); C2-ineligible truths (reach_external_b1 False) count as unreached.
Checks before any number (STOP): ck115 PASS for R and A and the CURRENT final files still have the checked sha256; manifests of ALL three tags
(f1dev, np053f1dev, c1bankdev): no extra checkpoint, fpnet sha = slot / R final / A final, fp_bits of every slot = the registered bits, every
other setting equal; per stratum the molecule set of every arm = the selection CSV's (no missing / extra / duplicate); per molecule the same
n_unique, reach_external_b1, truth_in_window and n_query in all arms; ranks finite, -1 or 1..n_unique (or NaN with an empty window).
Gate (115_plan v2, Codex 118): dFP(A - R) > 0 AND dFP(A - P0) > 0, dFP = 1/4 dMRR(np053f1dev NP_H) + 1/4 dMRR(np053f1dev NP_N) + 1/2 dMRR(f1dev
D_np_single); otherwise stop. Diagnostics only (never used for the decision): per-stratum FP MRR / top-1 of the three arms, rows where the v8w7a
main misses rank 1 (diag/r102), and the truth's simulated exposure in A by IDENTITY (Codex 120 Q5): the plan's own rule (make_simplan.py) maps
the eval identity_group to its canonical pool row (lowest pid among the pool rows of its train_structs official keys); states = resolved and in
the M_all catalog (exposure = consumed simulated items of that pid in A's ledger), resolved and not in the catalog (0 by construction), unresolved
(NA, kept apart). The plan inputs, catalog, jobs_pid and A's consumed-jobs file are bound to the plan manifest and A's receipt.
Writes diag/x115_stage1.md / .csv and diag/x115_stage1_decision.json (machine-readable gate + input hashes).
Usage (Spark, experiments/b1_baseline): python -X utf8 x115_stage1.py"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
E = os.path.join(ROOT, "experiments", "e115"); SLOT = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4"
BITS = "c3869e86449d6fed6e79e9655f8a7d35bd55c3138ecddfc1dae5072627e78677"
ARMS = ("p0", "r", "a")
TAGS = {"f1dev": ("run_f1dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
        "np053f1dev": ("run_np053_f1dev", ["NP_H", "NP_X", "NP_N"])}
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "c1bankdev": "c1bank_f1/c1dev/p2_molecules.csv"}
SLOTS = {"p0": os.path.join(ROOT, "data/external/fpnet_fold1_as_fold0"), "r": os.path.join(ROOT, "data/external/e115_slot_r"), "a": os.path.join(ROOT, "data/external/e115_slot_a")}


def stop(msg): sys.exit(f"STOP (115 stage 1): {msg}")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


CK, RC = {}, {}
for arm, run, tag in (("r", "runR", "e115R"), ("a", "runA", "e115A")):
    p = os.path.join(E, run, f"{tag}_ck115.json")
    if not os.path.exists(p): stop(f"missing completion check {p}")
    c = json.load(open(p))
    if not c.get("passed"): stop(f"completion check failed for {arm}")
    if sha(os.path.join(E, run, f"{tag}_final.pt")) != c["final_sha256"]: stop(f"{arm}: the final checkpoint changed after its completion check")
    CK[arm] = c["final_sha256"]; RC[arm] = json.load(open(os.path.join(E, run, f"{tag}_receipt.json")))
WANT = {"p0": SLOT, "r": CK["r"], "a": CK["a"]}
for arm in ARMS:
    if sha(os.path.join(SLOTS[arm], "fpnet_fold0.pt")) != WANT[arm]: stop(f"slot {SLOTS[arm]} does not hold the {arm} checkpoint")
    if sha(os.path.join(SLOTS[arm], "fp_bits.npy")) != BITS: stop(f"slot {SLOTS[arm]} fp_bits is not the registered bits")
SEL = {}
for tag, csv in EVAL_CSV.items():   # manifests of ALL tags (Codex 120 Q6.2) and the selection CSVs
    M = {arm: json.load(open(os.path.join(HERE, f"run_{tag}_{arm}e115", "b1_features_manifest.json"))) for arm in ARMS}
    for arm in ARMS:
        if M[arm].get("extra_ckpts") != []: stop(f"{tag} {arm}: extra checkpoints {M[arm].get('extra_ckpts')}")
        if M[arm].get("fpnet") != WANT[arm]: stop(f"{tag} {arm}: fpnet sha {M[arm].get('fpnet')} != {WANT[arm]}")
    for arm in ("r", "a"):
        diff = {k for k in set(M["p0"]) | set(M[arm]) if k not in ("fpnet", "seconds") and M["p0"].get(k) != M[arm].get(k)}
        if diff: stop(f"{tag}: manifests p0 / {arm} differ in {sorted(diff)}")
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str)
    if ev.duplicated(["set", "molecule"]).any(): stop(f"{tag}: duplicate molecules in the selection CSV")
    SEL[tag] = ev
rr = lambda r: np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
# truth exposure in A by identity (diagnostic, Codex 120 Q5): the plan's inputs / outputs as hashed in plan_manifest.json; A's ledger as in its receipt
PM = json.load(open(os.path.join(E, "mall", "plan_manifest.json")))
for p, h in PM["inputs"].items():
    if sha(os.path.join(ROOT, p)) != h: stop(f"plan input {p} changed since make_simplan")
for f in ("catalog.parquet", "jobs_pid.npy"):
    if sha(os.path.join(E, "mall", f)) != PM["outputs"][f]: stop(f"plan output {f} changed since make_simplan")
led = RC["a"].get("ledger", {}); cons_p = os.path.join(E, "runA", led.get("consumed_jobs_file", "e115A_consumed_jobs.npy"))
if sha(cons_p) != led.get("consumed_jobs_sha256"): stop("A's consumed-jobs file differs from its receipt")
if RC["a"]["setup"]["sim"].get("jobs_sha256") != PM["outputs"]["jobs.json"]: stop("A was trained on a different job list")
inp = {os.path.basename(p): os.path.join(ROOT, p) for p in PM["inputs"]}
P = pd.read_parquet(inp["pool_meta.parquet"], columns=["pid", "key"]); key2pid = dict(zip(P.key.astype(str), P.pid.astype(int)))
st = pd.read_parquet(inp["structures.parquet"], columns=["inchikey14", "identity_group"]); ik2g = dict(zip(st.inchikey14.astype(str), st.identity_group.astype(int)))
ts = pd.read_parquet(inp["train_structs.parquet"], columns=["key", "inchikey14"]); ts["g"] = ts.inchikey14.astype(str).map(ik2g)
canon = {}
for k, g in zip(ts.key.astype(str), ts.g):
    if k in key2pid and g == g: canon[int(g)] = min(canon.get(int(g), 1 << 62), key2pid[k])   # make_simplan's rule: lowest pid
cat = set(pd.read_parquet(os.path.join(E, "mall", "catalog.parquet"), columns=["pid"]).pid.astype(int))
jp = np.load(os.path.join(E, "mall", "jobs_pid.npy"), allow_pickle=False); cons = np.load(cons_p, allow_pickle=False)
if len(cons) != len(jp): stop("consumed-jobs ledger length != job list")
expo = np.bincount(jp[cons > 0], weights=cons[cons > 0].astype(float), minlength=len(P))
rows = []
for tag, (old, sets) in TAGS.items():
    ev = SEL[tag]; ig = dict(zip(ev.molecule, ev.identity_group.astype(int)))
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R = R[R.view == "c2"].set_index(["set", "molecule"]).main
    for s in sets:
        L_ = {arm: pd.read_csv(os.path.join(HERE, f"run_{tag}_{arm}e115", f"b1_molecules_{s}.csv")) for arm in ARMS}
        for d in L_.values(): d["molecule"] = d.molecule.astype(str)
        want = set(ev.molecule[ev.set == s])
        if not want: stop(f"{tag} {s}: no selected molecules")
        for arm, d in L_.items():   # completeness against the selection (Codex 120 Q6.3)
            if d.molecule.duplicated().any() or set(d.molecule) != want: stop(f"{tag} {s} {arm}: molecules differ from the selection (missing {len(want - set(d.molecule))}, extra {len(set(d.molecule) - want)})")
        cols = ["molecule", "truth_fp_rank", "n_unique", "reach_external_b1", "truth_in_window", "n_query"]
        z = L_["p0"][cols].rename(columns={c: c + "_p0" for c in cols[1:]})
        for arm in ("r", "a"):
            z = z.merge(L_[arm][cols].rename(columns={c: c + "_" + arm for c in cols[1:]}), on="molecule", validate="one_to_one")
        for c_ in ("n_unique", "reach_external_b1", "truth_in_window", "n_query"):
            for arm in ("r", "a"):
                if (z[f"{c_}_p0"].astype(str) != z[f"{c_}_{arm}"].astype(str)).any(): stop(f"{tag} {s}: {c_} differs between p0 and {arm}")
        nu = pd.to_numeric(z.n_unique_p0, errors="coerce").astype(float)   # Codex 121: finite non-negative integer; an empty window must say truth not in it, not reached
        if not (np.isfinite(nu).all() and (nu >= 0).all() and (nu == np.round(nu)).all()): stop(f"{tag} {s}: n_unique not a finite non-negative integer")
        fls = lambda c: z[c].astype(str).str.lower().isin(["false", "0"]).values
        emp = (nu == 0).values
        if (emp & ~(fls("truth_in_window_p0") & fls("reach_external_b1_p0"))).any(): stop(f"{tag} {s}: an empty window with truth_in_window / reach_external_b1 not False")
        for arm in ARMS:   # an EMPTY window (n_unique 0, truth not in it) carries NaN in b1_features = not in the window = -1 (same fix as x110_stage1, 2026-10-29)
            v_ = pd.to_numeric(z[f"truth_fp_rank_{arm}"], errors="coerce").astype(float); n_ = pd.to_numeric(z[f"n_unique_{arm}"], errors="coerce").astype(float)
            ok_ = (np.isfinite(v_) & (v_ == np.round(v_)) & ((v_ == -1) | ((v_ >= 1) & (v_ <= n_)))) | (emp & v_.isna().values)
            if not ok_.all(): stop(f"{tag} {s} {arm}: truth_fp_rank outside -1 / 1..n_unique ({int((~ok_).sum())} rows)")
        ok = z.reach_external_b1_p0.astype(bool).values
        for arm in ARMS: z[f"r_{arm}"] = np.where(ok, z[f"truth_fp_rank_{arm}"].fillna(-1).values.astype(float), -1.0)
        cp = [canon.get(ig[m]) for m in z.molecule]
        z["exposure_state"] = ["unresolved" if c is None else ("in_catalog" if c in cat else "not_in_catalog") for c in cp]
        z["truth_sim_exposure"] = [np.nan if c is None else (float(expo[c]) if c in cat else 0.0) for c in cp]
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
     "| stratum | n | FP MRR@25 P0 / R / A | top-1 P0 / R / A | truth in M_all (resolved) / unresolved | truth simulated in A (n) | FP MRR A - R: truth simulated / not (resolved) |",
     "|---|---:|---|---|---|---:|---|"]
for (tag, s), d in Z.groupby(["tag", "set"], sort=False):
    res = (d.exposure_state != "unresolved").values; sim = res & (d.truth_sim_exposure.fillna(0) > 0).values; dd = rr(d.r_a.values) - rr(d.r_r.values)
    L.append(f"| {tag} {s} | {len(d)} | {rr(d.r_p0.values).mean():.4f} / {rr(d.r_r.values).mean():.4f} / {rr(d.r_a.values).mean():.4f} | "
             f"{(d.r_p0 == 1).mean():.3f} / {(d.r_r == 1).mean():.3f} / {(d.r_a == 1).mean():.3f} | "
             f"{((d.exposure_state == 'in_catalog').sum() / max(1, res.sum())):.2f} / {int((~res).sum())} | {int(sim.sum())} | "
             f"{(dd[sim].mean() if sim.any() else float('nan')):+.4f} / {(dd[res & ~sim].mean() if (res & ~sim).any() else float('nan')):+.4f} |")
open(os.path.join(HERE, "diag/x115_stage1.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
HS = {"reader": sha(os.path.abspath(__file__)), "r_final": CK["r"], "a_final": CK["a"], "consumed_jobs": led.get("consumed_jobs_sha256"),
      "stage1_csv": sha(os.path.join(HERE, "diag/x115_stage1.csv"))}
for tag in TAGS:
    for arm in ARMS: HS[f"{tag}_{arm}_manifest"] = sha(os.path.join(HERE, f"run_{tag}_{arm}e115", "b1_features_manifest.json"))
json.dump(dict(stage=1, gate="PASS" if gate else "NO", dFP_A_R=d_ar, dFP_A_P0=d_ap, sha256=HS), open(os.path.join(HERE, "diag/x115_stage1_decision.json"), "w"), indent=1)
