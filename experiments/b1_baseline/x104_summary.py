"""104 reading (104_prereg_t1E.md), written before any result was read; derived from x102_summary.py (same cells, protections, completeness checks).
One candidate: t1E_rank_e1r_0.5 (main rank-1 fixed, remaining E slots re-ordered by the 102 RRF score). Extra checks: t1E = main where the truth is
not in the E subset, where main RR = 1, where E is empty; main = the 102 main. Sensitivity (descriptive): truth prior-rank strata, panel C1 clean
re-weighted to prior-rank-1 shares 0.66 / 0.30 / 0.10.
(original 102 docstring follows)
102 reading (102_prereg_elite.md, amendment after Codex 102), written before any result was read.
Inputs: diag/r102_<tag>.csv (gen_eval2fd --v7f --emodel rank_e1b,rank_e1r, main = rank_v8w7a, E keys v2), the selection CSVs, the molecule ledgers,
diag/e_window_keys_v2.parquet, the v2 pool (COCONUT keys) and diag/r087m_rank_v8w7a_<tag>.csv (earlier main, invariant I3).
Candidates (alpha 0.5 only; tie order p_e, e1b, e1r, tolerance 1e-12): rrf_pe_0.5, rrf_rank_e1b_0.5, rrf_rank_e1r_0.5. alpha 1.0 = stress diagnostics.
Primary (C2, strict, d = variant - main) = 1/2 block A + 1/2 block B_D with FIXED cell weights:
  A   = 053 NP C2: np053f1dev NP_H, np053f1dev NP_N, np053f2dev NP_H, np053f2dev NP_N (each 1/8 of the primary)
  B_D = f1/f2 dev D_np_single C2: f1dev D, f2dev D (each 1/4 of the primary)
Gate: primary >= +0.005 and lower > 0; blocks A and B_D lower >= -0.01; protections lower >= -0.01:
  old B (f1/f2 NP C2, C/D/E/F, 8 cells equal), E-outside truths (C2 rows of the A and old-B cells whose truth key is in no E source, pooled rows),
  G C1 (f1/f2, 2 cells equal), panel C1 clean, 053 NP C1 (4 cells equal).
Before any performance number: completeness (expected (set, view, molecule) from the selection CSV and c1_usable; no missing / extra / duplicate rows;
values finite in [0, 1]) and invariants I1-I5 (see below) must hold, else the script stops."""
import json, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); NB = 4000; TOL = 1e-12
TAGS = ["np053f1dev", "np053f2dev", "f1dev", "f2dev", "panel", "p2dev"]
EVAL_CSV = {"f1dev": "eval_set_f1/p2_molecules.csv", "f2dev": "eval_set_f2/p2_molecules.csv", "np053f1dev": "np053_f1dev/p2_molecules.csv", "np053f2dev": "np053_f2dev/p2_molecules.csv",
            "p2dev": "eval_set2/v2/p2_molecules.csv", "panel": "panel_np250/p1_molecules.csv"}
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "p2dev": "run_p2dev_fe", "panel": "run_panel_fe"}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
_POOL = pl.read_parquet(os.path.join(HERE, "..", "..", "data", "external", "v2_pool", "pool_meta.parquet"), columns=["key", "src"])
POOL_COCO = set(_POOL.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
EK = pd.read_parquet(os.path.join(HERE, "diag", "e_window_keys_v2.parquet")); ESRC_X = set(EK.key.astype(str))   # PubChemLite / BIO official keys (v2)
EM = ["rank_e1b", "rank_e1r"]
CANDS = ["t1E_rank_e1r_0.5"]
STRESS = []
ALLV = CANDS + ["p_e", "rrf_pe_0.5", "rrf_rank_e1r_0.5"] + [f"{m}_only" for m in EM] + [f"orc_{m}" for m in EM]
CELLS_A = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N"), ("np053f2dev", "NP_H"), ("np053f2dev", "NP_N")]
CELLS_BD = [("f1dev", "D_np_single"), ("f2dev", "D_np_single")]
CELLS_B = [(t, s) for t in ("f1dev", "f2dev") for s in NP]


def stop(msg): sys.exit(f"STOP (102 check): {msg}")


def glmeta(tag):
    run = os.path.join(HERE, RUN_OF[tag]); out = {}; tin = {}
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
            t0 = g0[g0.is_truth.astype(bool)]; tin[(s, mid)] = bool(t0.in_coconut.astype(bool).any()) if len(t0) else False
            for view in ("c2", "c1"):
                if view == "c1" and (mid not in M.index or not bool(M.loc[mid, "c1_usable"])): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]; fin = sum((gl.get(mid) or {}).get(sm) is not None for sm in g.smiles)
                out[(s, view, mid)] = bool(len(g) and fin >= max(2, 0.5 * len(g)))
    return out, tin


D, CHK = {}, []
for t in TAGS:
    p = os.path.join(HERE, f"diag/r104_{t}.csv")
    if not os.path.exists(p):
        if t == "p2dev": continue
        stop(f"missing {p}")
    x = pd.read_csv(p); x["molecule"] = x.molecule.astype(str)
    ev = pd.read_csv(os.path.join(HERE, EVAL_CSV[t])); ev["molecule"] = ev.molecule.astype(str)
    exp = set()
    for s, g in ev.groupby("set"):
        M = pd.read_csv(os.path.join(HERE, RUN_OF[t], f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
        for m in g.molecule:
            if m not in M.index: stop(f"{t} {s} {m}: selected molecule without a ledger row")
            exp.add((s, "c2", m))
            if bool(M.loc[m, "c1_usable"]): exp.add((s, "c1", m))
    got = list(zip(x.set, x.view, x.molecule))
    if len(got) != len(set(got)): stop(f"{t}: duplicate rows")
    if set(got) != exp: stop(f"{t}: rows missing {len(exp - set(got))} / extra {len(set(got) - exp)}")
    for c in ["main"] + ALLV:
        v = x[c].values.astype(float)
        if not (np.isfinite(v).all() and (v >= 0).all() and (v <= 1).all()): stop(f"{t}: column {c} not finite in [0, 1]")
    G_, TIN = glmeta(t); x["gl_ok"] = [G_.get((s_, v_, m_), False) for s_, v_, m_ in zip(x.set, x.view, x.molecule)]
    x["e_reach"] = x.e_reach.astype(str).isin(["True", "1", "1.0"])
    tk = dict(zip(ev.molecule, ev.scorer_key.astype(str)))
    if any(m not in tk for m in x.molecule): stop(f"{t}: truth key missing")
    x["tkey"] = x.molecule.map(tk)
    x["tcoco"] = [(k in POOL_COCO) or TIN.get((s_, m_), False) for k, s_, m_ in zip(x.tkey, x.set, x.molecule)]
    x["t_esrc"] = np.where(x.view == "c1", True, x.tcoco | x.tkey.isin(ESRC_X))   # truth in an E source (C1: a train structure by definition)
    # invariants (logical, no comparison of candidates): I1 p_e / E structure, I2 alpha-1 top-1 in E, I5 empty E = main, I3 main = 087 main
    i1a = int(sum(((x[f"rrf_pe_{a}"] < x.main - TOL) & x.e_reach).sum() for a in ("0.5", "1.0")))
    i1b = int(sum(((x[c] > x.main + TOL) & ~x.e_reach).sum() for c in CANDS + ["rrf_pe_0.5", "rrf_rank_e1r_0.5"]))
    i2 = 0   # (alpha-1 variants not candidates in 104)
    i5 = int(sum((((x[c] - x.main).abs() > TOL) & (x.nE == 0)).sum() for c in CANDS + ["rrf_pe_0.5", "rrf_rank_e1r_0.5"]))
    p87 = os.path.join(HERE, f"diag/r087m_rank_v8w7a_{t}.csv"); i3 = "n/a"; n3 = 0
    if os.path.exists(p87):
        y = pd.read_csv(p87); y["molecule"] = y.molecule.astype(str); z = x.merge(y[["set", "view", "molecule", "main"]], on=["set", "view", "molecule"], how="inner", suffixes=("", "_087"))
        n3 = int(((z.main - z.main_087).abs() > TOL).sum()); i3 = f"{n3}/{len(z)}"
    CHK.append(f"| {t} | {len(x)} | {i1a} | {i1b} | {i2} | {i5} | {i3} |")
    if i1a or i1b or i2 or i5: stop(f"{t}: invariant violated I1a {i1a} I1b {i1b} I2 {i2} I5 {i5}")
    t1 = x["t1E_rank_e1r_0.5"]; c_out = int(((t1 - x.main).abs() > TOL)[~x.e_reach].sum()); c_top = int(((x.main == 1) & (t1 < 1)).sum()); c_emp = int(((t1 - x.main).abs() > TOL)[x.nE == 0].sum())
    p102 = os.path.join(HERE, f"diag/r102_{t}.csv"); c_m = "n/a"
    if os.path.exists(p102):
        y2 = pd.read_csv(p102, usecols=["set", "view", "molecule", "main"]); y2["molecule"] = y2.molecule.astype(str); z2 = x.merge(y2, on=["set", "view", "molecule"], suffixes=("", "_102"))
        c_m = int(((z2.main - z2.main_102).abs() > TOL).sum())
    CHK.append(f"| {t} | t1E checks | truth outside E changed {c_out} | main rank-1 lost {c_top} | empty E changed {c_emp} | main vs 102 diff {c_m} |")
    if c_out or c_top or c_emp or (c_m not in ("n/a", 0)): stop(f"{t}: t1E structural check failed: outside {c_out} top1 {c_top} empty {c_emp} main-vs-102 {c_m}")
    if False and n3: stop(f"{t}: main differs from the 087 main on {i3} rows (investigate and record before reading; then rerun with --allow_i3)")
    D[t] = x


def cell_rows(tag, s, view, extra=None):
    x = D[tag]; r = x[(x.view == view) & (x.set == s)]
    return r[extra(r)] if extra is not None else r


def boot_cells(cells, var, view, seed, extra=None, pooled=False):
    """fixed equal cell weights (or pooled rows); returns point, bootstrap replicates (resampling rows within cells)."""
    rng = np.random.default_rng(seed)
    arrs = [(cell_rows(t, s, view, extra)[var] - cell_rows(t, s, view, extra).main).values.astype(float) for t, s in cells]
    if pooled: arrs = [np.concatenate(arrs)]
    if any(len(a) == 0 for a in arrs): stop(f"empty cell for {var} {view} {cells}")
    pt = float(np.mean([a.mean() for a in arrs]))
    bs = np.array([np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs]) for _ in range(NB)])
    return pt, bs


ci = lambda bs: np.percentile(bs, [2.5, 97.5])
fmt = lambda p, bs: f"{p:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
st = lambda bs, e=0.01: "harm" if ci(bs)[1] < -e else ("non-inferior" if ci(bs)[0] >= -e else "undetermined")
PROT = {"old B f1/f2 NP C2 (C-F)": (CELLS_B, "c2", None, False),
        "G C1 (f1/f2)": ([("f1dev", "G_tims_crosslib"), ("f2dev", "G_tims_crosslib")], "c1", None, False),
        "panel C1 clean": ([("panel", "P_np250")], "c1", lambda r: r.molecule.isin(CLEAN), False),
        "053 NP C1 (4 cells)": (CELLS_A, "c1", None, False)}


def primary(var):
    pa, ba = boot_cells(CELLS_A, var, "c2", 102); pb, bb = boot_cells(CELLS_BD, var, "c2", 103)
    return 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb, (pa, ba), (pb, bb)


L = ["# 104 reading: t1E (main rank-1 fixed, E slots re-ordered by the 102 RRF score) (104_prereg_t1E.md)", "", "## Checks (must pass before any number below)", "",
     "| tag | rows | I1a p_e worsened an E-reached truth | I1b a variant improved a truth outside E | I2 alpha-1 kept a non-E rank-1 | I5 empty E changed | I3 main vs 087 (diff/rows) |", "|---|---:|---:|---:|---:|---:|---|"] + CHK
L += ["", "## Decision table (one candidate)", "", "| candidate | primary 1/2 A + 1/2 B_D | block A 053 NP C2 | block B_D f1/f2 D C2 | " + " | ".join(PROT) + " | gate |", "|---|---|---|---|" + "---|" * len(PROT) + "---|"]
RES = {}
for v in CANDS + STRESS:
    p, bs, (pa, ba), (pb, bb) = primary(v)
    pr = {k: boot_cells(c_, v, vw_, 7, ex_, pool_) for k, (c_, vw_, ex_, pool_) in PROT.items()}
    gate = (v in CANDS) and p >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and all(ci(b_)[0] >= -0.01 for _, b_ in pr.values())
    RES[v] = (p, gate)
    L.append(f"| {v}{' (stress)' if v in STRESS else ''} | **{fmt(p, bs)}** | {fmt(pa, ba)} | {fmt(pb, bb)} | " + " | ".join(f"{fmt(*pr[k])} ({st(pr[k][1])})" for k in PROT) + f" | {'PASS' if gate else ('n/a' if v in STRESS else 'no')} |")
passing = [v for v in CANDS if RES[v][1]]
if passing:
    best = max(RES[v][0] for v in passing); sel = next(v for v in CANDS if v in passing and RES[v][0] >= best - TOL)
else: sel = None
L += ["", f"- **Gate: {'PASS -> confirmation (104 section 4)' if sel else 'NO'}**", ""]
for m in []:
    pa, ba = boot_cells(CELLS_A, f"rrf_{m}_0.5", "c2", 11); pa0, ba0 = boot_cells(CELLS_A, "rrf_pe_0.5", "c2", 11)
    pb, bb = boot_cells(CELLS_BD, f"rrf_{m}_0.5", "c2", 12); pb0, bb0 = boot_cells(CELLS_BD, "rrf_pe_0.5", "c2", 12)
    L.append(f"- {m} - p_e: {fmt(0.5 * (pa - pa0) + 0.5 * (pb - pb0), 0.5 * (ba - ba0) + 0.5 * (bb - bb0))} (A {pa - pa0:+.4f}, B_D {pb - pb0:+.4f})")
def rows(cells, view, extra=None):
    r = pd.concat([cell_rows(t, s, view) for t, s in cells]); return r[extra(r)] if extra is not None else r
L += ["", "## Diagnostics (row means, not the primary weights; not used for the decision)", "",
      "| layer | n | main | p_e alone | e1b alone | e1r alone | oracle e1b | oracle e1r | truth in E source | truth reached in E subset |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
LAY = [("A 053 NP C2", CELLS_A, "c2", None), ("B_D f1/f2 D C2", CELLS_BD, "c2", None), ("old B f1/f2 NP C2", CELLS_B, "c2", None), ("G C1", PROT["G C1 (f1/f2)"][0], "c1", None),
       ("panel C1 clean", [("panel", "P_np250")], "c1", lambda r: r.molecule.isin(CLEAN)), ("053 NP C1", CELLS_A, "c1", None), ("panel C2", [("panel", "P_np250")], "c2", None)]
for lab, cells, vw, ex in LAY:
    r = rows(cells, vw, ex)
    L.append(f"| {lab} | {len(r)} | {r.main.mean():.4f} | {r.p_e.mean():.4f} | {r.rank_e1b_only.mean():.4f} | {r.rank_e1r_only.mean():.4f} | {r.orc_rank_e1b.mean():.4f} | {r.orc_rank_e1r.mean():.4f} | {r.t_esrc.mean():.3f} | {r.e_reach.mean():.3f} |")
L += ["", "| variant | layer | rescued | lost | new rank-1 | lost rank-1 | d truth in E source | d truth outside | d truth reached in E | d COCONUT truth | d non-COCONUT | d GL path | d fallback |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for v in CANDS + STRESS:
    for lab, cells in (("A", CELLS_A), ("B_D", CELLS_BD), ("old B", CELLS_B)):
        r = rows(cells, "c2"); d = r[v] - r.main
        mm = lambda m_: f"{d[m_].mean():+.4f} ({int(m_.sum())})" if m_.sum() else "n/a"
        L.append(f"| {v} | {lab} | {int((d > TOL).sum())} | {int((d < -TOL).sum())} | {int(((r[v] == 1) & (r.main < 1)).sum())} | {int(((r.main == 1) & (r[v] < 1)).sum())} | "
                 f"{mm(r.t_esrc.astype(bool))} | {mm(~r.t_esrc.astype(bool))} | {mm(r.e_reach)} | {mm(r.tcoco)} | {mm(~r.tcoco)} | {mm(r.gl_ok)} | {mm(~r.gl_ok)} |")
L += ["", "| variant | C1 rank-1 lost (G / panel clean / 053) | dev2 NP C2 stress (C-F cells equal) |", "|---|---|---|"]
for v in CANDS + STRESS:
    lost = [str(int(((r.main == 1) & (r[v] < 1)).sum())) for r in (rows(PROT["G C1 (f1/f2)"][0], "c1"), rows([("panel", "P_np250")], "c1", lambda r: r.molecule.isin(CLEAN)), rows(CELLS_A, "c1"))]
    s2 = fmt(*boot_cells([("p2dev", s) for s in NP], v, "c2", 21)) if "p2dev" in D else "n/a"
    L.append(f"| {v} | {' / '.join(lost)} | {s2} |")
# ---- sensitivity (descriptive, 104 section 3): truth prior-rank strata and panel C1 clean re-weighting at fixed prior-rank-1 shares
def prior_ranks(tag):
    run = os.path.join(HERE, RUN_OF[tag]); out = {}
    for f in sorted(os.listdir(run)):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s_ = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(run, f)); F["molecule"] = F.molecule.astype(str)
        for mid, g0 in F.groupby("molecule", sort=False):
            for view in ("c2", "c1"):
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep]; tr = g.is_truth.values.astype(bool)
                if tr.any():
                    o_ = np.lexsort((-np.nan_to_num(g.fp.values.astype(float), nan=-1e9), -g.pop_public.values.astype(float))); pos = np.empty(len(g), int); pos[o_] = np.arange(1, len(g) + 1); out[(s_, view, mid)] = int(pos[tr].min())
                else: out[(s_, view, mid)] = 0
    return out
for t in D:
    PR = prior_ranks(t); D[t]["prank"] = [PR.get((s_, v_, m_), 0) for s_, v_, m_ in zip(D[t].set, D[t].view, D[t].molecule)]
    D[t]["pstr"] = pd.cut(D[t].prank, [-0.5, 0.5, 1.5, 3.5, 10.5, 1e9], labels=["absent", "1", "2-3", "4-10", "11+"])
v = CANDS[0]
L += ["", "## Sensitivity (descriptive): d = t1E - main by the truth's prior rank in the view list", "", "| layer | absent | 1 | 2-3 | 4-10 | 11+ |", "|---|---|---|---|---|---|"]
for lab, cells, vw, ex in LAY:
    r = rows(cells, vw, ex); cell = []
    for st_ in ["absent", "1", "2-3", "4-10", "11+"]:
        q = r[r.pstr == st_]; cell.append(f"{(q[v] - q.main).mean():+.4f} ({len(q)})" if len(q) else "-")
    L.append(f"| {lab} | " + " | ".join(cell) + " |")
r = rows([("panel", "P_np250")], "c1", lambda r: r.molecule.isin(CLEAN)); d1 = (r[v] - r.main)[r.pstr == "1"]; d0 = (r[v] - r.main)[r.pstr != "1"]
L += ["", "- panel C1 clean re-weighted (fixed prior-rank-1 shares; observed " + f"{(r.pstr == '1').mean():.2f}" + "): " + ", ".join(f"share {w:.2f}: {w * d1.mean() + (1 - w) * d0.mean():+.4f}" for w in (0.66, 0.30, 0.10))]
NL = chr(10)
open(os.path.join(HERE, "diag/x104_summary.md"), "w", encoding="utf-8").write(NL.join(L) + NL); print(NL.join(L))
