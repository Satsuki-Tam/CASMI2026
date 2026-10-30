"""144 (v2, after Codex 143) E2 step 4: development reading of the fusion F of P and E2, registered in reports/agent_review/144_prereg_e2.md
before any E2 number was read. P = v8w7a main order, top 25 per (set, view, molecule) (experiments/b1_baseline/diag/top102_<tag>.parquet,
gen_eval2fd --dump_top); E2 = e2_lgb.txt on the view window of the same molecule (e2_common). Paired on exactly P's groups.
Lists (constants fixed): P; E2 (E window only); F = identity RRF, candidates P top 25 | E2 top 25, s = 1/(10 + r_P) + 0.5/(10 + r_E)
(r_E = E2 rank in the whole view window; a missing side contributes 0; ties -> P rank, E2 rank, key; cut at 25); F0 = the same with
weight 0 (must equal P: technical check); H = F with E2's top 1 moved / inserted at position 2 when it is not already F's top 1 or 2
(F's top 1 kept, other relative order kept, cut at 25); controls / descriptive: pe = P restricted to the view's E window, Fpe = RRF(P, pe)
(source re-weighting alone), Hp = P with the same insertion, F1 = RRF with weight 1.
Reading = the 102 registration (x102_summary.py): primary 1/2 A + 1/2 B_D (A = 053 NP_H / NP_N C2 of both folds, B_D = f1 / f2 D C2),
gate primary >= +0.005 and lower > 0, A / B_D lower >= -0.01, protections lower >= -0.01 (old B, E-outside truths C2 pooled, G C1,
panel C1 clean, 053 NP C1); bootstrap = rows (molecules) resampled inside cells, 4000 draws, 102's seeds.
Outputs: <out>/e2_eval_groups.csv, <out>/e2_eval_summary.md."""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, polars as pl, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
from e2_common import FEATS, view_frame, rank_lists
S5 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]; S3 = ["NP_H", "NP_X", "NP_N"]; NP = S5[:4]
TAGS = {"np053f1dev": ("np053_f1dev", "p2_molecules.csv", S3), "np053f2dev": ("np053_f2dev", "p2_molecules.csv", S3),
        "f1dev": ("eval_set_f1", "p2_molecules.csv", S5), "f2dev": ("eval_set_f2", "p2_molecules.csv", S5), "panel": ("panel_np250", "p1_molecules.csv", ["P_np250"])}
LISTS = ["P", "E2", "F", "F0", "H", "pe", "Fpe", "Hp", "F1"]; K, ALPHA, NB, TOL = 10.0, 0.5, 4000, 1e-12
CELLS_A = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N"), ("np053f2dev", "NP_H"), ("np053f2dev", "NP_N")]
CELLS_BD = [("f1dev", "D_np_single"), ("f2dev", "D_np_single")]; CELLS_B = [(t, s) for t in ("f1dev", "f2dev") for s in NP]


def rrf(p, e_rank, e_top, w):
    pr = {k: i + 1 for i, k in enumerate(p)}; cand = list(dict.fromkeys(list(p) + (list(e_top) if w else [])))
    s = lambda k: (1.0 / (K + pr[k]) if k in pr else 0.0) + (w / (K + e_rank[k]) if (w and k in e_rank) else 0.0)
    return sorted(cand, key=lambda k: (-s(k), pr.get(k, 99), e_rank.get(k, 1e9), k))[:25]


def insert2(L, e1):
    if e1 is None or not L or e1 in L[:2]: return L[:25]
    return ([L[0], e1] + [k for k in L[1:] if k != e1])[:25]


def rr(L, t):
    L = L[:25]; return 1.0 / (L.index(t) + 1) if t in L else 0.0


def stop(msg): sys.exit(f"STOP (144 check): {msg}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ewin", default="experiments/e2/ewin"); ap.add_argument("--top", default="experiments/b1_baseline/diag")
    a = ap.parse_args(); P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p); out = P_(a.out); os.makedirs(out, exist_ok=True); t0 = time.time()
    m = lgb.Booster(model_file=P_(a.model))
    if m.feature_name() != FEATS: stop("model features differ from e2_common.FEATS")
    clean = set(pd.read_csv(P_("experiments/fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
    pool = pl.read_parquet(P_("data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"]); POOL_COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
    ESRC_X = set(pd.read_parquet(P_("experiments/b1_baseline/diag/e_window_keys_v2.parquet")).key.astype(str))
    rows = []
    for tag, (d, csv, sets) in TAGS.items():
        T = pd.read_parquet(f"{P_(a.top)}/top102_{tag}.parquet"); T["molecule"] = T.molecule.astype(str)
        ev = pd.read_csv(P_(f"experiments/b1_baseline/{d}/{csv}")); truth = dict(zip(ev.molecule.astype(str), ev.scorer_key.astype(str)))
        for s in sets:
            E = pd.read_parquet(P_(f"{a.ewin}/{d}/ewin_{s}.parquet")); F = pd.read_parquet(P_(f"{a.ewin}/{d}/e2f_{s}.parquet"))
            E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str)
            tin = {r.molecule for r in E[E.is_truth & E.in_coconut].itertuples(index=False)}
            for v in ("c1", "c2"):
                Pv = T[(T.set == s) & (T.view == v)].sort_values(["molecule", "rank"])
                if not len(Pv): continue
                X = view_frame(E, F, v); R = rank_lists(X, m.predict(X[FEATS])) if len(X) else X
                EL = {g: grp.official_key.astype(str).tolist() for g, grp in R.groupby("molecule", sort=False)} if len(R) else {}
                for mid, grp in Pv.groupby("molecule", sort=False):
                    if mid not in truth: stop(f"{tag} {s} {mid}: no truth key")
                    t = truth[mid]; p = grp.okey.astype(str).tolist()[:25]; el = EL.get(mid, []); er = {k: i + 1 for i, k in enumerate(el)}; e1 = el[0] if el else None
                    L = dict(P=p, E2=el[:25], F=rrf(p, er, el[:25], ALPHA), F0=rrf(p, er, el[:25], 0.0), F1=rrf(p, er, el[:25], 1.0))
                    L["H"] = insert2(L["F"], e1); L["Hp"] = insert2(p, e1); L["pe"] = [k for k in p if k in er]
                    per = {k: i + 1 for i, k in enumerate(L["pe"])}; L["Fpe"] = rrf(p, per, L["pe"], ALPHA)
                    tcoco = (t in POOL_COCO) or (mid in tin)
                    rows.append(dict(tag=tag, set=s, view=v, molecule=mid, tkey=t, tcoco=tcoco, t_esrc=(v == "c1") or tcoco or (t in ESRC_X), truth_in_e=t in er,
                                     e2_rank=er.get(t, np.nan), p_rank=(p.index(t) + 1) if t in p else np.nan, n_e=len(el), e1_in_p=(e1 in p) if e1 else False,
                                     panel_clean=(tag == "panel" and mid in clean), **{l: rr(L[l], t) for l in LISTS}))
            print(f"  {tag} {s} ({time.time()-t0:.0f}s)", flush=True)
    G = pd.DataFrame(rows); G.to_csv(f"{out}/e2_eval_groups.csv", index=False)
    # ---- checks before any performance number
    exp = {(tg, s_, v_, m_) for tg in TAGS for (s_, v_, m_) in zip(*[pd.read_parquet(f"{P_(a.top)}/top102_{tg}.parquet")[c].astype(str) for c in ("set", "view", "molecule")])}
    got = list(zip(G.tag, G.set, G.view, G.molecule))
    if len(got) != len(set(got)) or set(got) != exp: stop(f"groups differ from P's: missing {len(exp - set(got))}, extra {len(set(got) - exp)}, dup {len(got) - len(set(got))}")
    if (np.abs(G.F0 - G.P) > TOL).any(): stop(f"F0 != P on {int((np.abs(G.F0 - G.P) > TOL).sum())} groups")
    if (np.abs(G.F - G.P)[G.n_e == 0] > TOL).any(): stop("empty E2 list changed F")
    for c in LISTS:
        if not (np.isfinite(G[c]).all() and G[c].between(0, 1).all()): stop(f"{c} outside [0, 1]")
    CHK = f"groups {len(G)} = P's; F0 == P on all; empty-E2 groups {int((G.n_e == 0).sum())} unchanged; values in [0, 1]"
    cell = lambda tg, s, vw, ex=None: (lambda r: r[ex(r)] if ex is not None else r)(G[(G.tag == tg) & (G.set == s) & (G.view == vw)])

    def boot(cells, var, vw, seed, ex=None, pooled=False, base="P"):
        rng = np.random.default_rng(seed); arrs = [(cell(t_, s_, vw, ex)[var] - cell(t_, s_, vw, ex)[base]).values.astype(float) for t_, s_ in cells]
        if pooled: arrs = [np.concatenate(arrs)]
        if any(len(x) == 0 for x in arrs): stop(f"empty cell {var} {vw} {cells}")
        return float(np.mean([x.mean() for x in arrs])), np.array([np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in arrs]) for _ in range(NB)])
    ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p_, bs: f"{p_:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
    stt = lambda bs, e=0.01: "harm" if ci(bs)[1] < -e else ("non-inferior" if ci(bs)[0] >= -e else "undetermined")
    PROT = {"old B f1/f2 NP C2 (C-F)": (CELLS_B, "c2", None, False), "E-outside truths C2 (A + old B, pooled)": (CELLS_A + CELLS_B, "c2", lambda r: ~r.t_esrc.astype(bool), True),
            "G C1 (f1/f2)": ([("f1dev", "G_tims_crosslib"), ("f2dev", "G_tims_crosslib")], "c1", None, False),
            "panel C1 clean": ([("panel", "P_np250")], "c1", lambda r: r.panel_clean.astype(bool), False), "053 NP C1 (4 cells)": (CELLS_A, "c1", None, False)}

    def primary(var, base="P"):
        pa, ba = boot(CELLS_A, var, "c2", 102, base=base); pb, bb = boot(CELLS_BD, var, "c2", 103, base=base)
        return 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb, (pa, ba), (pb, bb)
    L_ = [f"# 144 E2 reading (model {a.model}; {time.strftime('%Y-%m-%d %H:%M')})", "", f"Checks: {CHK}", "", "## Decision table (vs P; 102 registration)", "",
          "| list | primary 1/2 A + 1/2 B_D | A 053 NP C2 | B_D f1/f2 D C2 | " + " | ".join(PROT) + " | gate |", "|---|---|---|---|" + "---|" * len(PROT) + "---|"]
    RES = {}
    for v in ["F", "H", "Fpe", "Hp", "F1", "E2", "pe"]:
        p_, bs, (pa, ba), (pb, bb) = primary(v); pr = {k: boot(c_, v, vw_, 7, ex_, pool_) for k, (c_, vw_, ex_, pool_) in PROT.items()}
        gate = p_ >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and all(ci(b_)[0] >= -0.01 for _, b_ in pr.values()); RES[v] = (p_, bs, gate, pr)
        L_.append(f"| {v}{'' if v in ('F', 'H') else ' (descriptive)'} | **{fmt(p_, bs)}** | {fmt(pa, ba)} | {fmt(pb, bb)} | " + " | ".join(f"{fmt(*pr[k])} ({stt(pr[k][1])})" for k in PROT) + f" | {'PASS' if gate else 'no'} |")
    ph, bh, (pha, bha), (phb, bhb) = primary("H", base="F")
    hgate = ph > 0 and ci(bh)[0] >= -0.005 and all(ci(b_)[0] >= -0.01 for _, b_ in RES["H"][3].values())
    L_ += ["", f"- **F gate: {'PASS' if RES['F'][2] else 'no'}**; H - F primary {fmt(ph, bh)} (A {pha:+.4f}, B_D {phb:+.4f}); **H gate (H - F point > 0, lower >= -0.005, H protections vs P): {'PASS' if hgate else 'no'}**"]
    # Public diagnostic path (Codex 143): E-source C2 rescue same sign in both folds + real rescues
    def esrc_fold(f):
        cells = [c for c in CELLS_A + CELLS_B if c[0] in (("np053f1dev", "f1dev") if f == 1 else ("np053f2dev", "f2dev"))]
        r = pd.concat([cell(t_, s_, "c2") for t_, s_ in cells]); r = r[r.t_esrc.astype(bool)]; return float((r.F - r.P).mean()), len(r)
    g1, n1 = esrc_fold(1); g2, n2 = esrc_fold(2); ra = pd.concat([cell(t_, s_, "c2") for t_, s_ in CELLS_A + CELLS_B])
    resc = int(((ra.F == 1) & (ra.P < 1)).sum()); lost1 = int(((ra.P == 1) & (ra.F < 1)).sum())
    diag_ok = g1 > 0 and g2 > 0 and resc >= 10
    L_ += [f"- Public diagnostic path: E-source C2 F - P fold 1 {g1:+.4f} (n {n1}), fold 2 {g2:+.4f} (n {n2}); new rank-1 {resc} / lost rank-1 {lost1} (A + old B C2) -> **{'eligible' if diag_ok else 'not eligible'}**"]
    # ---- diagnostics (not used for the decision)
    def rows_(cells, vw, ex=None):
        r = pd.concat([cell(t_, s_, vw) for t_, s_ in cells]); return r[ex(r)] if ex is not None else r
    LAY = [("A 053 NP C2", CELLS_A, "c2", None), ("B_D f1/f2 D C2", CELLS_BD, "c2", None), ("old B f1/f2 NP C2", CELLS_B, "c2", None), ("G C1", PROT["G C1 (f1/f2)"][0], "c1", None),
           ("panel C1 clean", [("panel", "P_np250")], "c1", lambda r: r.panel_clean.astype(bool)), ("053 NP C1", CELLS_A, "c1", None), ("f1/f2 NP C1", CELLS_B, "c1", None), ("panel C2", [("panel", "P_np250")], "c2", None)]
    L_ += ["", "## Diagnostics (row means; not used for the decision)", "", "| layer | n | " + " | ".join(LISTS) + " | oracle max(P, E2) | truth in E source | truth in E2 window | truth in E2 top 25 |", "|---|---:|" + "---:|" * (len(LISTS) + 4)]
    for lab, cells, vw, ex in LAY:
        try: r = rows_(cells, vw, ex)
        except ValueError: continue
        if not len(r): continue
        L_.append(f"| {lab} | {len(r)} | " + " | ".join(f"{r[l].mean():.4f}" for l in LISTS) + f" | {np.maximum(r.P, r.E2).mean():.4f} | {r.t_esrc.mean():.3f} | {r.truth_in_e.mean():.3f} | {(r.e2_rank <= 25).mean():.3f} |")
    L_ += ["", "| list | layer | rescued | lost | new rank-1 | lost rank-1 | d truth in E source (n) | d truth outside (n) | d COCONUT truth | d non-COCONUT |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for v in ["F", "H", "Fpe"]:
        for lab, cells in (("A", CELLS_A), ("B_D", CELLS_BD), ("old B", CELLS_B)):
            r = rows_(cells, "c2"); dd = r[v] - r.P; mm = lambda m_: f"{dd[m_].mean():+.4f} ({int(m_.sum())})" if m_.sum() else "n/a"
            L_.append(f"| {v} | {lab} | {int((dd > TOL).sum())} | {int((dd < -TOL).sum())} | {int(((r[v] == 1) & (r.P < 1)).sum())} | {int(((r.P == 1) & (r[v] < 1)).sum())} | "
                      f"{mm(r.t_esrc.astype(bool))} | {mm(~r.t_esrc.astype(bool))} | {mm(r.tcoco.astype(bool))} | {mm(~r.tcoco.astype(bool))} |")
    # mixture sensitivity on A + old B C2 rows: g = mean F - P on E-source truths, c = on E-outside truths
    r = rows_(CELLS_A + CELLS_B, "c2"); g_ = float((r.F - r.P)[r.t_esrc.astype(bool)].mean()); c_ = float((r.F - r.P)[~r.t_esrc.astype(bool)].mean())
    be = (-c_ / (g_ - c_)) if (g_ > 0 > c_) else float("nan")
    L_ += ["", f"- Mixture sensitivity (A + old B C2): E-source g {g_:+.4f}, E-outside c {c_:+.4f}; break-even E-source share w* = {be:.3f} (w g + (1 - w) c = 0); not an estimate of the hidden w.",
           f"- F - Fpe (E2's ordering beyond source re-weighting), primary weights: {fmt(*[x - y for x, y in zip(primary('F')[:2], primary('Fpe')[:2])])}",
           f"- Rank-1 complementarity, C2 A + old B: P right & E2 wrong {int(((r.P == 1) & (r.E2 < 1)).sum())}, E2 right & P wrong {int(((r.E2 == 1) & (r.P < 1)).sum())}, both {int(((r.P == 1) & (r.E2 == 1)).sum())}; "
           f"truths found by E2 outside P's top 25: {int(((r.p_rank.isna()) & (r.e2_rank <= 25)).sum())}"]
    open(f"{out}/e2_eval_summary.md", "w", encoding="utf-8").write("\n".join(L_) + "\n"); print("\n".join(L_)); print(f"E2_EVAL_DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
