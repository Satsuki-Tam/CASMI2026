"""133 reading (133_prereg_mist_ranker.md), written before any 133 evaluation result. Inputs: diag/r133[f2]_{P,M}_<tag>.csv = gen_eval2fd_m133.py with
P = rank_v8w7a (fe61dc42) and M = rank_m133 in the same run, MIST v4 tables (experiments/mist/scores_v4).
Checks (STOP): the row manifest lists exactly the expected files and every file matches; every input of the input record re-hashed equal; the
evaluator / rankfeats / wf_common / P / M / MIST scorer / adapter / checkpoint / commit equal to 133_registered_versions.json; the MIST v4
manifest of every tag (checkpoint, commit, code hashes, each set's output sha = the file); completeness of both CSVs against the selection CSV +
c1_usable (no missing / extra / duplicate rows), identical row keys in P and M; P's main equal to the frozen P (r102 / r111_base) on every
expected row (one-to-one); every main value finite in [0, 1]; one identity group per cell row.
Readings (fixed; d = M main - P main per row, strict, identity bootstrap 4,000 per cell):
  fold 1: gate = primary (1/4 NP_H C2 + 1/4 NP_N C2 + 1/2 D C2, cells of np053f1dev / f1dev) >= +0.005 and 95% lower > 0; block A (NP_H / NP_N
          C2) and block D lower >= -0.01; protections lower >= -0.01: old B f1dev C-F C2, G C1 f1dev, NP C1 np053f1dev H/N, c1dev C1 pooled,
          c1dev positive-ion C1 (C1_pos_*) pooled -> diag/x133_decision.json (PASS / NO).
  fold 2 (--fold 2, only after a fold-1 PASS): primary > 0 and block A / D, old B, G C1, NP C1 lower >= -0.01 -> stability ok / no.
Diagnostics (not for the decision): rows up / down per cell, MIST-applicable (positive-capable) vs not.
v2 (Codex 133, before any result): + validator / query-flag / trainer versions, control = P byte for byte, control and M share the fit roster,
composition, params, rounds and differ only by EXTRA_MIST; P / M share n_cand and the GL path per row and are identical on the GL fallback path.
Usage (Spark, experiments/b1_baseline): python -X utf8 x133_summary.py [--fold 2]"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12; ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, default=1, choices=[1, 2]); A = ap.parse_args(); K_ = A.fold


def stop(msg): sys.exit(f"STOP (133 check): {msg}")


DEC = os.path.join(HERE, "diag", "x133_decision.json")
if K_ == 2 and not (os.path.exists(DEC) and json.load(open(DEC)).get("gate") == "PASS"): stop("fold 2 is read only after a fold-1 PASS")
SUF = "" if K_ == 1 else "f2"
TAGF, TAGN = f"f{K_}dev", f"np053f{K_}dev"; TAGB = "c1bankdev" if K_ == 1 else None
EVAL_CSV = {TAGF: f"eval_set_f{K_}/p2_molecules.csv", TAGN: f"np053_f{K_}dev/p2_molecules.csv"}
RUN_OF = {TAGF: f"run_f{K_}dev", TAGN: f"run_np053_f{K_}dev"}
BASE_OF = {TAGF: f"diag/r102_{TAGF}.csv", TAGN: f"diag/r102_{TAGN}.csv"}
if TAGB: EVAL_CSV[TAGB] = "c1bank_f1/c1dev/p2_molecules.csv"; RUN_OF[TAGB] = "run_c1bankdev_f1"; BASE_OF[TAGB] = "diag/r111_base_c1bankdev.csv"
NPS = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CELLS_A = [(TAGN, "NP_H"), (TAGN, "NP_N")]; CELLS_D = [(TAGF, "D_np_single")]
PROT = {f"old B {TAGF} C-F C2": ([(TAGF, s) for s in NPS], "c2"), f"G C1 {TAGF}": ([(TAGF, "G_tims_crosslib")], "c1"), f"NP C1 {TAGN} H/N": (CELLS_A, "c1")}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


REG = json.load(open(os.path.join(HERE, "133_registered_versions.json")))
man = os.path.join(HERE, f"diag/x133{SUF}_rows_manifest.txt")
if not os.path.exists(man): stop("row manifest missing")
ML = [ln.split() for ln in open(man) if ln.strip()]; files = [f for _, f in ML]
expf = sorted([f"diag/r133{SUF}_{k}_{t}.csv" for t in EVAL_CSV for k in ("P", "M")] + [f"diag/x133{SUF}_inputs.txt"])
if len(files) != len(set(files)) or sorted(files) != expf: stop(f"row manifest lists {sorted(files)}, expected {expf}")
for h, f in ML:
    if sha(os.path.join(HERE, f)) != h: stop(f"{f} differs from the row manifest")
INP = {f: h for h, f in (ln.split() for ln in open(os.path.join(HERE, f"diag/x133{SUF}_inputs.txt")) if ln.strip())}
for f, h in INP.items():
    if sha(os.path.join(HERE, f)) != h: stop(f"input {f} changed since the evaluation")
for f, k in (("gen_eval2fd_m133.py", "evaluator_sha256"), ("b1_rankfeats.py", "rankfeats_sha256"), ("wf_common.py", "wf_common_sha256"), ("rank_v8w7a/lambdarank.txt", "P_sha256"),
             ("rank_m133/lambdarank.txt", "M_sha256")):
    if INP.get(f) != REG[k]: stop(f"{f} is not the registered version")
for f, k in (("../mist/mist_validate.py", "validator_sha256"), ("../mist/mist_qflags.py", "qflags_sha256"), ("b1_rank_train.py", "trainer_sha256"),
             ("rank_m133_ctrl/lambdarank.txt", "P_sha256")):   # v2 (Codex 133): the control retrained with the same trainer = P, byte for byte
    if sha(os.path.join(HERE, f)) != REG[k]: stop(f"{f} is not the registered version")
import filecmp
for f in ("fit_roster.csv", "fit_composition.json"):
    if not filecmp.cmp(os.path.join(HERE, "rank_m133_ctrl", f), os.path.join(HERE, "rank_m133", f), shallow=False): stop(f"control and M differ in {f} (training rows / composition)")
RC, RM = json.load(open(os.path.join(HERE, "rank_m133_ctrl", "rank_results.json"))), json.load(open(os.path.join(HERE, "rank_m133", "rank_results.json")))
if RC["selected"]["params"] != RM["selected"]["params"] or RC["selected"]["rounds"] != RM["selected"]["rounds"] or RC["c1_repeat"] != RM["c1_repeat"] or RC["drop"] != RM["drop"]: stop("control and M differ in the recipe")
sys.path.insert(0, HERE); from b1_rankfeats import EXTRA_MIST
if RM["feature_names"] != RC["feature_names"] + [c for c in EXTRA_MIST if c not in set(RM["drop"])]: stop("M feature list != control + EXTRA_MIST")
print("control / M: same fit roster, composition, params, rounds; features differ by EXTRA_MIST only")
for t in EVAL_CSV:
    mf = json.load(open(os.path.join(ROOT, "experiments", "mist", "scores_v4", f"mist_{t}_manifest.json")))
    if mf.get("ckpt_sha256") != REG["mist_ckpt_sha256"] or mf.get("mist_commit") != REG["mist_commit"]: stop(f"MIST v4 scores of {t}: checkpoint / commit not registered")
    cd_ = mf.get("code", {})
    if cd_.get("mist_score_v4.py") != REG["mist_score_v4_sha256"] or cd_.get("mist_adapter.py") != REG["mist_adapter_sha256"] or cd_.get("wf_common.py") != REG["wf_common_sha256"]: stop(f"MIST v4 scores of {t}: code not registered")
    for s_, rec in mf["sets"].items():
        if rec.get("output_sha256") != sha(os.path.join(ROOT, "experiments", "mist", "scores_v4", f"mist_{t}_{s_}.parquet")): stop(f"MIST output {t} {s_} differs from its manifest")
    print(f"{t}: MIST v4 manifest ok")
D = {}
for t, csv in EVAL_CSV.items():
    xs = {}
    for k in ("P", "M"):
        x = pd.read_csv(os.path.join(HERE, f"diag/r133{SUF}_{k}_{t}.csv")); x["molecule"] = x.molecule.astype(str); xs[k] = x
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str); ig = dict(zip(ev.molecule, ev.identity_group.astype(int)))
    exp = set()
    for s, g in ev.groupby("set"):
        M = pd.read_csv(os.path.join(HERE, RUN_OF[t], f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        for m in g.molecule:
            if m not in M.index: stop(f"{t} {s} {m}: selected molecule without a ledger row")
            exp.add((s, "c2", m)); cu = str(M.loc[m, "c1_usable"])
            if cu not in ("True", "False"): stop(f"{t} {s} {m}: c1_usable is not a boolean")
            if cu == "True": exp.add((s, "c1", m))
    for k, x in xs.items():
        got = list(zip(x.set, x.view, x.molecule))
        if len(got) != len(set(got)): stop(f"{t} {k}: duplicate rows")
        if set(got) != exp: stop(f"{t} {k}: rows missing {len(exp - set(got))} / extra {len(set(got) - exp)}")
        v = x["main"].values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{t} {k}: main not finite in [0, 1]")
    y = pd.read_csv(os.path.join(HERE, BASE_OF[t]), usecols=["set", "view", "molecule", "main"]); y["molecule"] = y.molecule.astype(str)
    if not exp <= set(zip(y.set, y.view, y.molecule)): stop(f"{t}: the frozen P lacks expected rows")
    z = xs["P"].merge(y, on=["set", "view", "molecule"], how="left", suffixes=("", "_base"), validate="one_to_one")
    if z.main_base.isna().any() or ((z.main - z.main_base).abs() > TOL).any(): stop(f"{t}: P's main differs from {BASE_OF[t]}")
    j = xs["P"][["set", "view", "molecule", "main", "n_cand", "gl_ok133", "top25_133"]].merge(xs["M"][["set", "view", "molecule", "main", "n_cand", "gl_ok133", "top25_133"]].rename(columns={"main": "mm", "n_cand": "n_cand_m", "gl_ok133": "gl_ok_m", "top25_133": "top25_m"}), on=["set", "view", "molecule"], how="inner", validate="one_to_one")
    if not (j.n_cand.values == j.n_cand_m.values).all(): stop(f"{t}: P / M candidate counts differ")
    gp_, gm_ = j.gl_ok133.fillna(-1).values, j.gl_ok_m.fillna(-1).values
    if not (gp_ == gm_).all(): stop(f"{t}: P / M differ in the GL path")
    fb_ = (gp_ == 0)
    if not ((j.top25_133.values[fb_] == j.top25_m.values[fb_]).all() and np.allclose(j.main.values[fb_], j.mm.values[fb_], rtol=0, atol=0)): stop(f"{t}: P / M lists differ on the GL fallback path")
    print(f"{t}: GL path {int((gp_ == 1).sum())}, fallback {int(fb_.sum())} (P = M there), empty {int((gp_ == -1).sum())}")
    if len(j) != len(exp): stop(f"{t}: P / M rows do not match one-to-one")
    j["ig"] = j.molecule.map(ig)
    if j.ig.isna().any() or j.duplicated(["set", "view", "ig"]).any(): stop(f"{t}: identity group missing or repeated within a cell")
    if t == TAGB and j[j.view == "c1"].ig.duplicated().any(): stop("bank: identity group repeated across the pooled C1 rows")
    D[t] = j.sort_values(["set", "view", "molecule"]).reset_index(drop=True)


def cellrows(t, s, view):
    r = D[t]; r = r[(r.set == s) & (r.view == view)]
    if not len(r): stop(f"empty cell {t} {s} {view}")
    return r


def boot(cells, view, seed):
    rng = np.random.default_rng(seed); arrs = [(cellrows(t, s, view)["mm"] - cellrows(t, s, view)["main"]).values.astype(float) for t, s in cells]
    return float(np.mean([a.mean() for a in arrs])), np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])


def boot_pooled(r, seed):
    if not len(r): stop("empty pooled set")
    rng = np.random.default_rng(seed); a = (r["mm"] - r["main"]).values.astype(float); return float(a.mean()), np.array([a[rng.integers(0, len(a), len(a))].mean() for _ in range(NB)])


ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
pa, ba = boot(CELLS_A, "c2", 1331); pd_, bd = boot(CELLS_D, "c2", 1332); p, bs = 0.5 * pa + 0.5 * pd_, 0.5 * ba + 0.5 * bd
pr = {k: boot(c, w, 1337) for k, (c, w) in PROT.items()}
L = [f"# 133 reading (fold {K_}): M (v8w7a recipe + EXTRA_MIST) - P (rank_v8w7a), same rows / recipe (133_prereg_mist_ranker.md)", ""]
L += ["| primary | block A | block D | " + " | ".join(PROT) + (" | c1dev C1 pooled | c1dev positive-ion C1 |" if TAGB else " |"), "|---|---|---|" + "---|" * len(PROT) + ("---|---|" if TAGB else "")]
gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
stab = p > 0 and ci(ba)[0] >= -0.01 and ci(bd)[0] >= -0.01 and all(ci(b)[0] >= -0.01 for _, b in pr.values())
cell = ""
if TAGB:
    bank = D[TAGB]; c1 = bank[bank.view == "c1"]; pb, bb = boot_pooled(c1, 1338); pos = c1[c1.set.astype(str).str.startswith("C1_pos")]; pp, bp = boot_pooled(pos, 1339)
    gate = gate and ci(bb)[0] >= -0.01 and ci(bp)[0] >= -0.01; cell = f" | {fmt(pb, bb)} (n {len(c1)}) | {fmt(pp, bp)} (n {len(pos)})"
L.append(f"| **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pd_, bd)} | " + " | ".join(fmt(*pr[k]) for k in PROT) + cell + " |")
if K_ == 1:
    json.dump(dict(stage=1, gate=("PASS" if gate else "NO"), primary=p, lower=float(ci(bs)[0]), reader_sha256=sha(os.path.abspath(__file__)), registered_versions=REG,
                   rows_manifest_sha256=sha(man)), open(DEC, "w"), indent=1)
    L += ["", f"- **Gate (fold 1): {'PASS -> fold 2 (--fold 2)' if gate else 'NO'}**"]
else:
    L += ["", f"- fold-2 stability: primary {p:+.4f}, blocks / protections lower >= -0.01: {stab} -> " + ("go to the confirmation" if stab else "**no confirmation**")]
L += ["", "## Diagnostics (not used for the decision)", "", "| tag | set | view | n | P main | M main | rows up / down |", "|---|---|---|---:|---:|---:|---|"]
for t, x in D.items():
    for (s, w), r in x.groupby(["set", "view"], sort=True):
        L.append(f"| {t} | {s} | {w} | {len(r)} | {r.main.mean():.4f} | {r.mm.mean():.4f} | {int((r.mm > r.main + TOL).sum())} / {int((r.mm < r.main - TOL).sum())} |")
out = chr(10).join(L) + chr(10); open(os.path.join(HERE, f"diag/x133{SUF}_summary.md"), "w", encoding="utf-8").write(out); print(out)
