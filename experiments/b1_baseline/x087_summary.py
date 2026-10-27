"""087 development reading (087_prereg_v8w7a.md). One gen_eval2m --v7f pass: diag/r087m_<model>_<tag>.csv for rank_v7a (Spark), rank_v7a_pc (control),
rank_v8w7a (candidate). Primary: 053 dev NP_H C2, f1/f2 equal blocks, v8w7a - v7a_pc, tau +0.005. Also: B-restricted in-B rank-1 share not available
from the CSV (main only) -> reported as the truth-COCONUT C2 and the non-COCONUT C2 (truth key joined to COCONUT membership), the GL path vs fallback split
(fallback must be ~0: the ranker is not used there). Main protection (eps 0.01, three states): panel C1 clean, f1/f2 G C1, f1/f2 NP C2 (C/D/E/F)."""
import os, json, pickle
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(20261027); NB = 4000
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv",
            "p2dev": "eval_set2/v2/p2_molecules.csv", "panel": "panel_np250/p1_molecules.csv"}
_POOL = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "v2_pool", "pool_meta.parquet"), columns=["key", "src"])
POOL_COCO = set(_POOL.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
COCO_RAW = set(str(x) for x in pickle.load(open(os.path.join(HERE, "..", "..", "data", "external", "coconut", "coco_meta.pkl"), "rb"))["keys"])
def tcoco(tag):
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[tag]))
    return {str(m): (str(k) in POOL_COCO) or (str(r) in COCO_RAW) for m, k, r in zip(ev.molecule, ev.scorer_key, ev.raw_key if "raw_key" in ev.columns else ev.molecule)}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
def glmeta(tag):
    """(set, view, molecule) -> gl_ok (production GL-cover rule on the view list), as in r071_summary.meta."""
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
GLM = {t: glmeta(t) for t in ("np053f1dev", "np053f2dev")}
def pair(ma, mb, tag):
    pa, pb = (os.path.join(HERE, f"diag/r087m_{m}_{tag}.csv") for m in (ma, mb))
    if not (os.path.exists(pa) and os.path.exists(pb)): return None
    a = pd.read_csv(pa); b = pd.read_csv(pb); x = a.merge(b, on=["set", "view", "molecule"], suffixes=("_a", "_b")); assert len(x) == len(a) == len(b)
    x["d"] = x.main_b - x.main_a; x["molecule"] = x.molecule.astype(str); T = tcoco(tag); x["tcoco"] = [T.get(m, False) for m in x.molecule]
    G_ = GLM.get(tag, {}); x["gl_ok"] = [G_.get((s_, v_, m_), False) for s_, v_, m_ in zip(x.set, x.view, x.molecule)]
    return x
def block_stat(blocks):
    blocks = [b for b in blocks if len(b)]
    pt = float(np.mean([b.mean() for b in blocks]))
    bs = np.array([np.mean([b[rng.integers(0, len(b), len(b))].mean() for b in blocks]) for _ in range(NB)])
    return pt, np.percentile(bs, [2.5, 97.5])
st = lambda lo, hi, e=0.01: "harm" if hi < -e else ("non-inferior" if lo > -e else "undetermined")
fmt = lambda p, ci: f"{p:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]"
L = ["# 087 development reading", ""]
for name, ma, mb in (("CAND v8w7a - v7a_pc", "rank_v7a_pc", "rank_v8w7a"), ("REPRO v7a_pc - v7a", "rank_v7a", "rank_v7a_pc"), ("context v8w7a - v7a", "rank_v7a", "rank_v8w7a")):
    X = {t: pair(ma, mb, t) for t in EVAL_CSV}
    row = [name]
    def sel(t, f):
        x = X.get(t); return None if x is None else x[f(x)]
    nph = [sel(t, lambda x: (x.view == "c2") & (x.set == "NP_H")) for t in ("np053f1dev", "np053f2dev")]
    row.append(fmt(*block_stat([z.d.values for z in nph if z is not None])))
    for lab, f in (("COCONUT-truth C2 (053, all sets)", lambda x: (x.view == "c2") & x.tcoco), ("non-COCONUT C2 (f1/f2 C+D)", None)):
        if f is not None: row.append(fmt(*block_stat([sel(t, f).d.values for t in ("np053f1dev", "np053f2dev") if X.get(t) is not None])))
        else: row.append(fmt(*block_stat([sel(t, lambda x: (x.view == "c2") & x.set.isin(NP[:2]) & ~x.tcoco).d.values for t in ("f1dev", "f2dev") if X.get(t) is not None])))
    gl = [sel(t, lambda x: (x.view == "c2") & (x.set == "NP_H") & x.gl_ok) for t in ("np053f1dev", "np053f2dev")]
    row.append(fmt(*block_stat([z.d.values for z in gl if z is not None])) if all(z is not None for z in gl) else "n/a")
    fb = [sel(t, lambda x: (x.view == "c2") & ~x.gl_ok) for t in ("np053f1dev", "np053f2dev")]
    row.append(f"max |d| {max(float(np.abs(z.d.values).max()) if len(z) else 0.0 for z in fb):.4f}" if all(z is not None for z in fb) else "n/a")
    prot = []
    if X.get("panel") is not None:
        z = sel("panel", lambda x: (x.view == "c1") & x.molecule.isin(CLEAN)); p, ci = block_stat([z.d.values]); prot.append(f"{fmt(p, ci)} ({st(*ci)})")
    else: prot.append("n/a")
    g = [sel(t, lambda x: (x.view == "c1") & (x.set == "G_tims_crosslib")) for t in ("f1dev", "f2dev")]
    if all(z is not None for z in g): p, ci = block_stat([z.d.values for z in g]); prot.append(f"{fmt(p, ci)} ({st(*ci)})")
    else: prot.append("n/a")
    n = [sel(t, lambda x: (x.view == "c2") & x.set.isin(NP)) for t in ("f1dev", "f2dev")]
    if all(z is not None for z in n): p, ci = block_stat([z.d.values for z in n]); prot.append(f"{fmt(p, ci)} ({st(*ci)})")
    else: prot.append("n/a")
    L.append("| " + " | ".join(row + prot) + " |")
L.insert(2, "| comparison | primary NP_H C2 (f1,f2) | COCONUT-truth C2 (053) | non-COCO C2 (f1/f2 C+D) | NP_H C2 GL path | fallback (must be ~0) | panel C1 clean | G C1 (f1/f2) | f1/f2 NP C2 |")
L.insert(3, "|---|---|---|---|---|---|---|---|---|")
open(os.path.join(HERE, "diag/x087_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
