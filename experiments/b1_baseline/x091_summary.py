"""091 development reading (091_prereg_fpmean.md incl. the platform-control amendment).
Primary: f1/f2 dev NP strata strict C2 (C/D/E/F pooled within a fold, folds = equal blocks), main with fp_s override (diag/r091m_*) minus main with the
PC-recomputed merged fp_m override (diag/r091mm_*); same evaluator, ranker (rank_v7a_pc), candidate rows. Gate: >= +0.003, both folds > 0, pooled lower > 0,
non-inferiority (L >= -0.01) on G C1 (f1/f2), 053 NP C1, panel C1 clean. Reference: fp_s main minus the table main (090 R0 = r090m_rank_v7a_pc main;
includes the Spark/PC numeric differences). Breakdowns: number of query spectra (1 / 2-3 / 4+), truth COCONUT, GL path / fallback, 053 C2."""
import os, sys, json, pickle
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv",
            "p2dev": "eval_set2/v2/p2_molecules.csv", "panel": "panel_np250/p1_molecules.csv"}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
_POOL = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "v2_pool", "pool_meta.parquet"), columns=["key", "src"])
POOL_COCO = set(_POOL.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
COCO_RAW = set(str(x) for x in pickle.load(open(os.path.join(HERE, "..", "..", "data", "external", "coconut", "coco_meta.pkl"), "rb"))["keys"])
def tcoco(tag):
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[tag]))
    return {str(m): (str(k) in POOL_COCO) or (str(r) in COCO_RAW) for m, k, r in zip(ev.molecule, ev.scorer_key, ev.raw_key if "raw_key" in ev.columns else ev.molecule)}
def glmeta(tag):
    run = os.path.join(HERE, RUN_OF[tag]); out = {}
    for f in sorted(os.listdir(run)):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(run, f)); F["molecule"] = F.molecule.astype(str)
        M = pd.read_csv(os.path.join(run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        pth = os.path.join(run, "work", f"gl_{s}.json")
        try: ok = json.load(open(pth + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        gl = json.load(open(pth)) if ok else {}
        for mid, g0 in F.groupby("molecule", sort=False):
            for view in ("c2", "c1"):
                if view == "c1" and (mid not in M.index or not bool(M.loc[mid, "c1_usable"])): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]; fin = sum((gl.get(mid) or {}).get(sm) is not None for sm in g.smiles)
                out[(s, view, mid)] = bool(len(g) and fin >= max(2, 0.5 * len(g)))
    return out
def load(tag):
    p = {k: os.path.join(HERE, f"diag/{k}_rank_v7a_pc_{tag}.csv") for k in ("r091m", "r091mm", "r090m")}
    if not (os.path.exists(p["r091m"]) and os.path.exists(p["r091mm"])): return None
    s_ = pd.read_csv(p["r091m"]); m_ = pd.read_csv(p["r091mm"])
    x = s_[["set", "view", "molecule", "main"]].rename(columns={"main": "S"}); x["M"] = m_["main"].values
    assert (m_.molecule.astype(str).values == s_.molecule.astype(str).values).all()
    x["T"] = pd.read_csv(p["r090m"])["main"].values if os.path.exists(p["r090m"]) else np.nan
    x["molecule"] = x.molecule.astype(str); T = tcoco(tag); x["tcoco"] = [T.get(m, False) for m in x.molecule]
    G = glmeta(tag); x["gl_ok"] = [G.get((s, v, m), False) for s, v, m in zip(x.set, x.view, x.molecule)]
    fpq = pd.read_parquet(os.path.join(HERE, f"diag/fpmean_{tag}.parquet"), columns=["set", "molecule", "nq"]).drop_duplicates(["set", "molecule"])
    nq = {(str(s), str(m)): int(q) for s, m, q in zip(fpq.set, fpq.molecule, fpq.nq)}; x["nq"] = [nq.get((s, m), 0) for s, m in zip(x.set, x.molecule)]
    return x
def block_stat(blocks):
    blocks = [b for b in blocks if len(b)]
    pt = float(np.mean([b.mean() for b in blocks]))
    bs = np.array([np.mean([b[rng.integers(0, len(b), len(b))].mean() for b in blocks]) for _ in range(NB)])
    return pt, np.percentile(bs, [2.5, 97.5])
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo >= -e else "undetermined")
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
D = {t: load(t) for t in RUN_OF}
miss = [t for t, d in D.items() if d is None]
if any(t in miss for t in ("f1dev", "f2dev", "np053f1dev", "np053f2dev", "panel")): sys.exit(f"missing tables: {miss}")
def blocks(tags, f, a_="M", b_="S"): return [(D[t][f(D[t])][b_] - D[t][f(D[t])][a_]).values for t in tags]
NPC2 = lambda x: (x.view == "c2") & x.set.isin(NP)
bl = blocks(("f1dev", "f2dev"), NPC2); p, ci = block_stat(bl); folds = [float(b.mean()) for b in bl]
g = block_stat(blocks(("f1dev", "f2dev"), lambda x: (x.view == "c1") & (x.set == "G_tims_crosslib")))
n1 = block_stat(blocks(("np053f1dev", "np053f2dev"), lambda x: x.view == "c1"))
pn = block_stat(blocks(("panel",), lambda x: (x.view == "c1") & x.molecule.isin(CLEAN)))
gate = p >= 0.003 and all(f_ > 0 for f_ in folds) and ci[0] > 0 and all(c[1][0] >= -0.01 for c in (g, n1, pn))
L = ["# 091 development reading (per-spectrum FPNet logit mean vs PC-recomputed merged input)", "", f"tables missing (stress only): {miss}", "",
     f"- **Primary (f1/f2 NP strict C2, fp_s - fp_m)**: {fmt(p, ci)} (fold 1 {folds[0]:+.4f}, fold 2 {folds[1]:+.4f})",
     f"- G C1 (f1/f2): {fmt(*g)} ({st(*g[1])}); 053 NP C1: {fmt(*n1)} ({st(*n1[1])}); panel C1 clean: {fmt(*pn)} ({st(*pn[1])})",
     f"- **GATE to the pipeline implementation: {'PASS' if gate else 'FAIL'}**", ""]
L.append(f"- 053 dev C2 (NP_H/X/N, f1/f2 blocks): {fmt(*block_stat(blocks(('np053f1dev', 'np053f2dev'), lambda x: x.view == 'c2')))}")
L.append(f"- reference fp_s main - table main (incl. platform noise), f1/f2 NP C2: {fmt(*block_stat(blocks(('f1dev', 'f2dev'), NPC2, 'T', 'S')))}; "
         f"fp_m main - table main: {fmt(*block_stat(blocks(('f1dev', 'f2dev'), NPC2, 'T', 'M')))}")
for nm, f in (("query spectra 1", lambda x: NPC2(x) & (x.nq == 1)), ("2-3", lambda x: NPC2(x) & x.nq.between(2, 3)), ("4+", lambda x: NPC2(x) & (x.nq >= 4)),
              ("truth COCONUT", lambda x: NPC2(x) & x.tcoco), ("truth not COCONUT", lambda x: NPC2(x) & ~x.tcoco), ("GL path", lambda x: NPC2(x) & x.gl_ok), ("fallback", lambda x: NPC2(x) & ~x.gl_ok)):
    bb = blocks(("f1dev", "f2dev"), f); n = sum(len(b) for b in bb)
    L.append(f"- f1/f2 NP C2 {nm} (n {n}): {fmt(*block_stat(bb)) if n else 'n/a'}")
x = pd.concat([D[t][lambda d: d.view == "c2"] for t in ("np053f1dev", "np053f2dev")])
for nm, f in (("1", x.nq == 1), ("2-3", x.nq.between(2, 3)), ("4+", x.nq >= 4)):
    L.append(f"- 053 C2 query spectra {nm} (n {int(f.sum())}): {(x[f].S - x[f].M).mean():+.4f}")
if D["p2dev"] is not None:
    L.append(f"- dev2 NP C2 (stress): {fmt(*block_stat([(D['p2dev'][lambda d: (d.view == 'c2') & (d.set == s)].S - D['p2dev'][lambda d: (d.view == 'c2') & (d.set == s)].M).values for s in NP]))}")
open(os.path.join(HERE, "diag/x091_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
