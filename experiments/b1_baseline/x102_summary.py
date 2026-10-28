"""102 reading (102_prereg_elite.md), written before any result was read. Inputs: diag/r102_<tag>.csv (gen_eval2fd --v7f --emodel rank_e1b,rank_e1r, main = rank_v8w7a).
Candidates (6): rrf_rank_e1b_{0.5,1.0}, rrf_rank_e1r_{0.5,1.0}, rrf_pe_{0.5,1.0}; d = variant - main per (set, view, molecule) row (strict: unreachable truths stay as 0).
Primary = mean of block A (053 NP C2: NP_H, NP_N equal, folds f1/f2 equal) and block B (f1/f2 dev NP C2: C/D/E/F equal, folds equal); bootstrap within strata.
Gate: primary >= +0.005 and lower > 0; blocks A and B lower >= -0.01; protections lower >= -0.01: G C1 (f1/f2), panel C1 clean, 053 NP C1 (H/N).
Selection: the passing candidate with the largest primary point estimate, else none. E-ordering value: rrf_e(a) - rrf_pe(a) on the primary.
Diagnostics only: E alone / p_e / oracle, rescue-loss counts, truth in the E window vs not, truth COCONUT vs not, GL path vs fallback, H vs N, C1 rank-1 losses, dev2."""
import json, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000
TAGS = ["np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel", "p2dev"]
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv",
            "p2dev": "eval_set2/v2/p2_molecules.csv", "panel": "panel_np250/p1_molecules.csv"}
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
_POOL = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "v2_pool", "pool_meta.parquet"), columns=["key", "src"])
POOL_COCO = set(_POOL.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
EM = ["rank_e1b", "rank_e1r"]; AL = ["0.5", "1.0"]
CANDS = [f"rrf_{m}_{a}" for m in EM for a in AL] + [f"rrf_pe_{a}" for a in AL]


def glmeta(tag):
    """(set, view, molecule) -> gl_ok under the production GL-cover rule on the view list (as x087)."""
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


D = {}
for t in TAGS:
    p = os.path.join(HERE, f"diag/r102_{t}.csv")
    if not os.path.exists(p): continue
    x = pd.read_csv(p); x["molecule"] = x.molecule.astype(str)
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[t])); ev["molecule"] = ev.molecule.astype(str)
    x["tcoco"] = x.molecule.map(dict(zip(ev.molecule, ev.scorer_key.astype(str).isin(POOL_COCO)))).fillna(False).astype(bool)
    G_ = glmeta(t); x["gl_ok"] = [G_.get((s_, v_, m_), False) for s_, v_, m_ in zip(x.set, x.view, x.molecule)]
    x["e_reach"] = x.e_reach.astype(str).isin(["True", "1", "1.0"])
    D[t] = x
miss = [t for t in TAGS if t not in D]
if any(t in miss for t in ("np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel")): sys.exit(f"missing: {miss}")


def blocks(spec, var, extra=None):
    """spec = [(tag, view, [sets])]; one block per (tag, set) -> list of d arrays (variant - main)."""
    out = []
    for tag, view, sets in spec:
        x = D[tag]; x = x[x.view == view]
        if extra is not None: x = x[extra(x)]
        for s in sets:
            b = x[x.set == s]
            if len(b): out.append((b[var] - b.main).values.astype(float))
    return out


def boot(bl, seed):
    rng = np.random.default_rng(seed); bl = [b for b in bl if len(b)]
    pt = float(np.mean([b.mean() for b in bl]))
    bs = np.array([np.mean([b[rng.integers(0, len(b), len(b))].mean() for b in bl]) for _ in range(NB)])
    return pt, bs


ci = lambda bs: np.percentile(bs, [2.5, 97.5])
fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
st = lambda bs, e=0.01: "harm" if ci(bs)[1] < -e else ("non-inferior" if ci(bs)[0] >= -e else "undetermined")
SPEC_A = [(t, "c2", ["NP_H", "NP_N"]) for t in ("np053f1dev", "np053f2dev")]
SPEC_B = [(t, "c2", NP) for t in ("f1dev", "f2dev")]
PROT = {"G C1 (f1/f2)": ([(t, "c1", ["G_tims_crosslib"]) for t in ("f1dev", "f2dev")], None),
        "panel C1 clean": ([("panel", "c1", ["P_np250"])], lambda x: x.molecule.isin(CLEAN)),
        "053 NP C1 (H/N)": ([(t, "c1", ["NP_H", "NP_N"]) for t in ("np053f1dev", "np053f2dev")], None)}


def primary(var, seed=102):
    pa, ba = boot(blocks(SPEC_A, var), seed); pb, bb = boot(blocks(SPEC_B, var), seed + 1)
    return (pa + pb) / 2, (ba + bb) / 2, (pa, ba), (pb, bb)


L = ["# 102 reading: second engine E-lite + identity RRF with v8w7a (102_prereg_elite.md)", "", f"missing (stress/report only): {miss}", "",
     "| candidate | primary (A+B)/2 | block A 053 NP C2 | block B f1/f2 NP C2 | G C1 | panel C1 clean | 053 NP C1 | gate |", "|---|---|---|---|---|---|---|---|"]
RES = {}
for v in CANDS:
    p, bs, (pa, ba), (pb, bb) = primary(v)
    prot = {k: boot(blocks(sp, v, ex), 7) for k, (sp, ex) in PROT.items()}
    gate = p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and all(ci(b_)[0] >= -0.01 for _, b_ in prot.values())
    RES[v] = (p, gate)
    L.append(f"| {v} | **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pb, bb)} | " + " | ".join(f"{fmt(*prot[k])} ({st(prot[k][1])})" for k in PROT) + f" | {'PASS' if gate else 'no'} |")
passing = [v for v in CANDS if RES[v][1]]
sel = max(passing, key=lambda v: RES[v][0]) if passing else None
L += ["", f"- **Selection: {sel if sel else 'none'}** (passing: {passing})", "", "## E ordering vs source re-weighting (same alpha, primary): rrf_e - rrf_pe"]
for m in EM:
    for a in AL:
        pa_, ba_ = boot(blocks(SPEC_A, f"rrf_{m}_{a}"), 11); pa0, ba0 = boot(blocks(SPEC_A, f"rrf_pe_{a}"), 11)
        pb_, bb_ = boot(blocks(SPEC_B, f"rrf_{m}_{a}"), 12); pb0, bb0 = boot(blocks(SPEC_B, f"rrf_pe_{a}"), 12)
        L.append(f"- {m} a={a}: {fmt(((pa_ - pa0) + (pb_ - pb0)) / 2, ((ba_ - ba0) + (bb_ - bb0)) / 2)} (A {pa_ - pa0:+.4f}, B {pb_ - pb0:+.4f}; paired replicates)")
L += ["", "## Diagnostics (not used for the decision)", "", "| block | n | main | p_e | e1b alone | e1r alone | oracle e1b | oracle e1r | truth in E window |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
def rows(spec, extra=None):
    fr = []
    for tag, view, sets in spec:
        x = D[tag]; x = x[(x.view == view) & x.set.isin(sets)]
        if extra is not None: x = x[extra(x)]
        fr.append(x)
    return pd.concat(fr) if fr else pd.DataFrame()
for lab, sp, ex in (("A 053 NP C2", SPEC_A, None), ("B f1/f2 NP C2", SPEC_B, None), ("G C1", PROT["G C1 (f1/f2)"][0], None), ("panel C1 clean", PROT["panel C1 clean"][0], PROT["panel C1 clean"][1]),
                    ("053 NP C1", PROT["053 NP C1 (H/N)"][0], None), ("panel C2", [("panel", "c2", ["P_np250"])], None)):
    r = rows(sp, ex)
    if not len(r): continue
    L.append(f"| {lab} | {len(r)} | {r.main.mean():.4f} | {r.p_e.mean():.4f} | {r.rank_e1b_only.mean():.4f} | {r.rank_e1r_only.mean():.4f} | {r.orc_rank_e1b.mean():.4f} | {r.orc_rank_e1r.mean():.4f} | {r.e_reach.mean():.3f} |")
L += ["", "| candidate | block | rescued (var > main) | lost (var < main) | new rank-1 | lost rank-1 | d truth in E | d truth not in E | d COCONUT truth | d non-COCONUT truth | d GL path | d fallback | d NP_H | d NP_N |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for v in CANDS:
    for lab, sp in (("A", SPEC_A), ("B", SPEC_B)):
        r = rows(sp); d = r[v] - r.main
        mm = lambda m_: f"{d[m_].mean():+.4f} ({int(m_.sum())})" if m_.sum() else "n/a"
        L.append(f"| {v} | {lab} | {int((d > 1e-12).sum())} | {int((d < -1e-12).sum())} | {int(((r[v] == 1) & (r.main < 1)).sum())} | {int(((r.main == 1) & (r[v] < 1)).sum())} | "
                 f"{mm(r.e_reach)} | {mm(~r.e_reach)} | {mm(r.tcoco)} | {mm(~r.tcoco)} | {mm(r.gl_ok)} | {mm(~r.gl_ok)} | {mm(r.set == 'NP_H')} | {mm(r.set == 'NP_N')} |")
L += ["", "| candidate | C1 rank-1 lost (G / panel clean / 053) | dev2 NP C2 (stress) |", "|---|---|---|"]
for v in CANDS:
    lost = []
    for k, (sp, ex) in PROT.items():
        r = rows(sp, ex); lost.append(str(int(((r.main == 1) & (r[v] < 1)).sum())))
    s2 = fmt(*boot(blocks([("p2dev", "c2", NP)], v), 21)) if "p2dev" in D else "n/a"
    L.append(f"| {v} | {' / '.join(lost)} | {s2} |")
open(os.path.join(HERE, "diag/x102_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
