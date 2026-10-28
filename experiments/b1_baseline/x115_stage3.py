"""115 v2 stage 3 (reports/agent_review/115_plan.md, v2 sections; written before any R / A model exists; run only if stage 1 passed).
End to end, fold 1: the v8w7a main (gen_eval2fd --v7f, rank_v8w7a frozen, --parents 0, views c1,c2) on three table sets built with the same code:
  P0 = run_<tag>_p0e115 (public fpnet_fold1), R = run_<tag>_re115 (real-only fine-tune), A = run_<tag>_ae115 (simulation-mixed fine-tune)
  -> diag/r115_<arm>_<tag>.csv, tag in {f1dev, np053f1dev, c1bankdev} (the c1dev bank = c1bank_f1/c1dev).
Checks before any number (STOP): (1) GLACIER audit of every (arm, tag, set) bound to the current files and accepted by the evaluator's loader with the
audited finite count; shared candidates carry identical GLACIER values in all arms (one cache); (2) every arm has exactly the expected rows
(c2 for every selected molecule, c1 where c1_usable), main finite in [0, 1], c1_usable identical across arms, one identity group per cell;
(3) REPRODUCTION: P0's main equals the existing main on every row with the same row keys -- diag/r102_<tag>.csv for f1dev / np053f1dev and
diag/r111_base_c1bankdev.csv for the bank -- otherwise exit 2 (no candidate difference is computed).
Decision (both comparisons must pass, Codex 118): for X in {A - R, A - P0}: primary = 1/4 dMRR(np053f1dev NP_H C2) + 1/4 dMRR(np053f1dev NP_N C2)
+ 1/2 dMRR(f1dev D_np_single C2) >= +0.005 with the 95% lower bound > 0; block A (NP_H / NP_N C2, equal) and block D lower bounds >= -0.01;
protections (lower bound >= -0.01): old B = f1dev C/D/E/F C2 (equal), G C1 = f1dev G_tims_crosslib C1, NP C1 = np053f1dev NP_H / NP_N C1 (equal),
C1 bank = c1dev C1 rows POOLED (one identity one vote). Bootstrap 4,000 identity resamples per cell, the SAME resampled rows for both comparisons
(paired across the three arms), fixed seeds. An empty cell or an undetermined protection is a failure. A pass is a fold-1 development result:
fold 2 must pass the same gate on its own (fold-2 initial weights, the same recipe); not an unopened confirmation or a submission decision.
Revised after Codex 120 (before any R / A model): stage 3 is bound to the stage-1 decision (gate PASS, its hashes = the current files); GLACIER
values are checked across ALL three arms per (query, SMILES) after checking that each molecule's query input is identical in every arm (finite
values equal; finite / null disagreement = STOP); baselines (r102 / r111_base) are hashed, must be finite in [0, 1], and a row-key mismatch is a
reproduction failure (exit 2 with the audit); no --allow_repro path (a reproduction failure needs a new registered procedure); the pooled bank set
asserts one row per identity; the ledgers' identity_group equals the selection's. Writes diag/x115_stage3_decision.json (PASS / NO + hashes).
Usage (Spark, experiments/b1_baseline): python -X utf8 x115_stage3.py"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12
sys.path.insert(0, HERE)
import b1_locked_eval as LE
ARMS = ("p0", "r", "a")
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "c1bankdev": "c1bank_f1/c1dev/p2_molecules.csv"}
BASE = {"f1dev": "diag/r102_f1dev.csv", "np053f1dev": "diag/r102_np053f1dev.csv", "c1bankdev": "diag/r111_base_c1bankdev.csv"}
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N")]; CELLS_D = [("f1dev", "D_np_single")]


def stop(msg): sys.exit(f"STOP (115 stage 3): {msg}")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


SETS = {t: sorted(pd.read_csv(os.path.join(HERE, c)).set.unique()) for t, c in EVAL_CSV.items()}
S1 = json.load(open(os.path.join(HERE, "diag/x115_stage1_decision.json")))   # (0) bound to the stage-1 decision
if S1.get("gate") != "PASS": stop("stage 1 did not pass")
BIND = [("stage1_csv", "diag/x115_stage1.csv")] + [(f"{t}_{a}_manifest", f"run_{t}_{a}e115/b1_features_manifest.json") for t in EVAL_CSV for a in ARMS]
BIND += [(f"{t}_{a}_{f}", f"run_{t}_{a}e115/{f}") for t in EVAL_CSV for a in ARMS for s in SETS[t] for f in (f"b1_molecules_{s}.csv", f"b1_runner_{s}_in.json", f"b1_features_{s}.parquet")]
for k, f in BIND:   # every table of the nine runs is the one stage 1 read (Codex 122)
    if S1["sha256"].get(k) is None or S1["sha256"][k] != sha(os.path.join(HERE, f)): stop(f"{f} not bound to the stage-1 decision or changed after it")
WANT = {"p0": "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4", "r": S1["sha256"]["r_final"], "a": S1["sha256"]["a_final"]}
for t in EVAL_CSV:
    for arm in ARMS:
        m_ = json.load(open(os.path.join(HERE, f"run_{t}_{arm}e115", "b1_features_manifest.json")))
        if m_.get("fpnet") != WANT[arm] or m_.get("extra_ckpts") != []: stop(f"{t} {arm}: table not built from the {arm} checkpoint")
GLV = {}
for arm in ARMS:   # (1) GLACIER audit gate
    for t in EVAL_CSV:
        run = f"run_{t}_{arm}e115"
        for s in SETS[t]:
            g = os.path.join(HERE, run, "work", f"gl_{s}.json"); p = g + ".audit.json"; inp = os.path.join(HERE, run, f"b1_runner_{s}_in.json")
            if not os.path.isfile(p): stop(f"missing GLACIER audit {p}")
            au = json.load(open(p))
            if au.get("failure", 1) != 0: stop(f"GLACIER audit failures {au.get('failure')} in {p}")
            hs = au.get("sha256", {})
            if hs.get("output") != sha(g) or hs.get("input") != sha(inp) or hs.get("meta") != sha(g + ".meta.json"): stop(f"GLACIER audit {p} is not about the current files")
            d, meta, _ = LE.runner(os.path.join(HERE, run), s, "gl")
            if d is None: stop(f"the evaluator's loader rejects {g} (status {(meta or {}).get('status')})")
            nfin = sum(1 for dd in d.values() for v in (dd or {}).values() if v is not None and np.isfinite(float(v)))
            if nfin != au.get("finite"): stop(f"{g}: loader sees {nfin} finite values, audit {au.get('finite')}")
            GLV[(arm, t, s)] = d
nshared = 0
for t in EVAL_CSV:   # all three arms (Codex 120 Q3): identical query inputs per molecule, then one value per (molecule, SMILES)
    for s in SETS[t]:
        Q = {}
        for arm in ARMS:
            for q in json.load(open(os.path.join(HERE, f"run_{t}_{arm}e115", f"b1_runner_{s}_in.json"))):
                k_ = json.dumps({x: y for x, y in q.items() if x != "cands"}, sort_keys=True)
                if Q.setdefault(str(q["mid"]), k_) != k_: stop(f"{t} {s} {q['mid']}: the query input differs between arms")
        U = {}
        for arm in ARMS:
            for m, dd in GLV[(arm, t, s)].items():
                for smi, v in (dd or {}).items():
                    fin = v is not None and bool(np.isfinite(float(v))); key = (str(m), smi)
                    if key in U:
                        f0, v0 = U[key]; nshared += 1
                        if f0 != fin or (fin and float(v) != v0): stop(f"{t} {s} {m}: GLACIER value of a shared candidate differs between arms (finite {f0} / {fin})")
                    else: U[key] = (fin, float(v) if fin else None)
D, CHK, LED, BSHA, KEYFAIL = {}, [], {}, {}, []
for t, csv in EVAL_CSV.items():   # (2) rows, (3) reproduction
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ig = dict(zip(ev.molecule, ev.identity_group.astype(int)))
    X = {}
    for arm in ARMS:
        p = os.path.join(HERE, f"diag/r115_{arm}_{t}.csv")
        if not os.path.exists(p): stop(f"missing {p}")
        x = pd.read_csv(p, usecols=["set", "view", "molecule", "main"]); x["molecule"] = x.molecule.astype(str)
        exp, c1u = set(), {}
        for s, g in ev.groupby("set"):
            M = pd.read_csv(os.path.join(HERE, f"run_{t}_{arm}e115", f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule"); LED[(arm, t, s)] = M
            if set(M.index) != set(g.molecule) or M.index.duplicated().any(): stop(f"{arm} {t} {s}: ledger molecules differ from the selection")
            for m in g.molecule:
                if int(M.loc[m, "identity_group"]) != ig[m]: stop(f"{arm} {t} {s} {m}: ledger identity_group differs from the selection")
                cu = str(M.loc[m, "c1_usable"])   # Codex 121: explicit boolean only
                if cu not in ("True", "False"): stop(f"{arm} {t} {s} {m}: c1_usable is not a boolean ({cu})")
                exp.add((s, "c2", m)); c1u[(s, m)] = cu == "True"
                if c1u[(s, m)]: exp.add((s, "c1", m))
        got = list(zip(x.set, x.view, x.molecule))
        if len(got) != len(set(got)): stop(f"{arm} {t}: duplicate rows")
        if set(got) != exp: stop(f"{arm} {t}: rows missing {len(exp - set(got))} / extra {len(set(got) - exp)}")
        v = x.main.values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{arm} {t}: main not finite in [0, 1]")
        X[arm] = (x.rename(columns={"main": f"main_{arm}"}), c1u)
    if X["r"][1] != X["p0"][1] or X["a"][1] != X["p0"][1]: stop(f"{t}: c1_usable differs between the arms")
    z = X["p0"][0].merge(X["r"][0], on=["set", "view", "molecule"], validate="one_to_one").merge(X["a"][0], on=["set", "view", "molecule"], validate="one_to_one")
    z["ig"] = z.molecule.map(ig)
    if z.ig.isna().any() or z.duplicated(["set", "view", "ig"]).any(): stop(f"{t}: identity group missing or repeated within a cell")
    y = pd.read_csv(os.path.join(HERE, BASE[t]), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str); BSHA[t] = sha(os.path.join(HERE, BASE[t]))
    yv = y.main.values.astype(float)
    if not (np.isfinite(yv).all() and (yv >= 0).all() and (yv <= 1).all()) or y.duplicated(["set", "view", "molecule"]).any(): stop(f"{t}: baseline {BASE[t]} not finite in [0, 1] or duplicated")
    k_new, k_old = set(zip(z.set, z.view, z.molecule)), set(zip(y.set, y.view, y.molecule))
    if k_new != k_old:
        KEYFAIL.append(f"- {t}: row keys differ from the existing main: new only {len(k_new - k_old)}, old only {len(k_old - k_new)}"); z["tag"] = t; D[t] = z; continue
    q = z.merge(y, on=["set", "view", "molecule"], how="left", validate="one_to_one"); q["dr"] = q.main_p0 - q.main
    for (s, vw), r in q.groupby(["set", "view"], sort=True):
        CHK.append(f"| {t} {s} {vw} | {len(r)} | {int((r.dr.abs() > TOL).sum())} | {r.dr.mean():+.5f} | {r.dr.abs().mean():.5f} | {r.dr.abs().max():.4f} |")
    z["tag"] = t; D[t] = z
HDR = ["## Reproduction of the existing main by P0 (P0 - existing)", "", "| cell | rows | rows differing | signed mean | mean abs | max abs |", "|---|---:|---:|---:|---:|---:|"]
if KEYFAIL or any(int(c.split("|")[3]) > 0 for c in CHK):
    open(os.path.join(HERE, "diag/x115_stage3_repro.md"), "w", encoding="utf-8").write(chr(10).join(HDR + CHK + [""] + KEYFAIL) + chr(10))
    print("STOP (115 stage 3): P0 does not reproduce the existing main on every row; see diag/x115_stage3_repro.md (no candidate difference computed)")
    sys.exit(2)


def cell(t, s, view):
    r = D[t]; r = r[(r.set == s) & (r.view == view)]
    if not len(r): stop(f"empty cell {t} {s} {view}")
    return r


def boot2(cells, view, seed):
    """paired bootstrap: the same resampled rows give (A - R) and (A - P0); cells equally weighted."""
    rng = np.random.default_rng(seed); C = [cell(t, s, view) for t, s in cells]
    dar = [c.main_a.values - c.main_r.values for c in C]; dap = [c.main_a.values - c.main_p0.values for c in C]
    pt = (float(np.mean([x.mean() for x in dar])), float(np.mean([x.mean() for x in dap])))
    bs = np.empty((NB, 2))
    for i in range(NB):
        idx = [rng.integers(0, len(x), len(x)) for x in dar]
        bs[i] = (np.mean([x[j].mean() for x, j in zip(dar, idx)]), np.mean([x[j].mean() for x, j in zip(dap, idx)]))
    return pt, bs


def pooled2(t, view, seed):
    r = D[t]; r = r[r.view == view]
    if not len(r): stop(f"empty pooled set {t} {view}")
    if r.ig.duplicated().any(): stop(f"pooled set {t} {view}: an identity appears more than once (one identity one vote)")
    rng = np.random.default_rng(seed); dar = r.main_a.values - r.main_r.values; dap = r.main_a.values - r.main_p0.values
    bs = np.empty((NB, 2))
    for i in range(NB):
        j = rng.integers(0, len(r), len(r)); bs[i] = (dar[j].mean(), dap[j].mean())
    return (float(dar.mean()), float(dap.mean())), bs


ci = lambda b: np.percentile(b, [2.5, 97.5]); fmt = lambda p, b: f"{p:+.4f} [{ci(b)[0]:+.4f}, {ci(b)[1]:+.4f}]"
(pa, ba), (pd_, bd) = boot2(CELLS_A, "c2", 1151), boot2(CELLS_D, "c2", 1152)
PROT = {"old B f1dev C-F C2": boot2([("f1dev", s) for s in NPS], "c2", 1157), "G C1 f1dev": boot2([("f1dev", "G_tims_crosslib")], "c1", 1157),
        "NP C1 np053f1dev H/N": boot2(CELLS_A, "c1", 1157), "C1 bank c1dev pooled": pooled2("c1bankdev", "c1", 1158)}
res = {}
for k, name in ((0, "A - R"), (1, "A - P0")):
    prim = 0.5 * pa[k] + 0.5 * pd_[k]; bp = 0.5 * ba[:, k] + 0.5 * bd[:, k]
    ok = prim >= 0.005 and ci(bp)[0] > 0 and ci(ba[:, k])[0] >= -0.01 and ci(bd[:, k])[0] >= -0.01 and all(ci(b[:, k])[0] >= -0.01 for _, b in PROT.values())
    res[name] = (prim, bp, ok)
gate = all(v[2] for v in res.values())
L = ["# 115 stage 3: v8w7a main on P0 / R / A tables (fold 1)", "", f"- GLACIER: shared (molecule, SMILES) values checked across the three arms: {nshared}", ""] + HDR + CHK
L += ["", "## Decision (both comparisons must pass)", "", "| comparison | primary | block A | block D | " + " | ".join(PROT) + " | pass |", "|---|---|---|---|" + "---|" * len(PROT) + "---|"]
for k, name in ((0, "A - R"), (1, "A - P0")):
    prim, bp, ok = res[name]
    L.append(f"| {name} | **{fmt(prim, bp)}** | {fmt(pa[k], ba[:, k])} | {fmt(pd_[k], bd[:, k])} | " + " | ".join(fmt(p[k], b[:, k]) for p, b in PROT.values()) + f" | {'yes' if ok else 'no'} |")
L += ["", f"**Gate: {'PASS (fold 1) -> fold 2 replication' if gate else 'NO'}**", "",
      "## Diagnostics (row means; not used for the decision)", "", "| cell | n | main P0 | main R | main A | A - R rescued / lost | A - P0 rescued / lost |", "|---|---:|---:|---:|---:|---|---|"]
for t, z in D.items():
    for (s, view), r in z.groupby(["set", "view"], sort=True):
        d1, d2 = r.main_a - r.main_r, r.main_a - r.main_p0
        L.append(f"| {t} {s} {view} | {len(r)} | {r.main_p0.mean():.4f} | {r.main_r.mean():.4f} | {r.main_a.mean():.4f} | {int((d1 > TOL).sum())} / {int((d1 < -TOL).sum())} | {int((d2 > TOL).sum())} / {int((d2 < -TOL).sum())} |")
pd.concat(D.values(), ignore_index=True).to_csv(os.path.join(HERE, "diag/x115_stage3.csv"), index=False)
open(os.path.join(HERE, "diag/x115_stage3.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
HS = {"reader": sha(os.path.abspath(__file__)), "stage1_decision": sha(os.path.join(HERE, "diag/x115_stage1_decision.json")), "stage3_csv": sha(os.path.join(HERE, "diag/x115_stage3.csv"))}
HS.update({f"baseline_{t}": h for t, h in BSHA.items()}); HS.update({f"r115_{a}_{t}": sha(os.path.join(HERE, f"diag/r115_{a}_{t}.csv")) for a in ARMS for t in EVAL_CSV})
json.dump(dict(stage=3, gate="PASS" if gate else "NO", comparisons={n: dict(primary=v[0], lower=float(ci(v[1])[0]), passed=bool(v[2])) for n, v in res.items()}, sha256=HS),
          open(os.path.join(HERE, "diag/x115_stage3_decision.json"), "w"), indent=1)
