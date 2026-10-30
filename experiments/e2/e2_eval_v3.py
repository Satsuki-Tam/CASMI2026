"""144 reader v3 (Codex 145 corrections; same registered lists, gates and constants as e2_eval.py v2 -- that file is kept unchanged as the record).
Changes: (1) the expected (set, view, molecule) groups come from the selection CSV + the C1-usable ledgers of the P runs (b1_molecules_<set>.csv,
as x102_summary); a group without a P list is kept with P = [] (the kernel keeps the placeholder: F = H = P = []); (2) F0 == P and "empty E2 ->
F == P" are checked on ORDERED official-key lists; H keeps F's top 1 (ordered check); (3) E2 predictions must be finite, P keys unique with
ranks 1..n; (4) E-source membership is query-independent: t_coco = truth official key in the v2-pool COCONUT keys or the COCONUT store's
official keys (x145_coco_okeys.py), t_pclbio = in the E key v2 PubChemLite / BIO official keys, t_esrc = C1 or t_coco or t_pclbio; the
view-window reach is a separate column (t_reach); (5) the H gate also requires A and B_D lower >= -0.01 for H - P; (6) a manifest ties the
inputs (P top tables, E / F tables, model, code) by sha256. The decision rules are those of 144 v2 (registered before any E2 number).
Outputs: <out>/e2_eval_groups.csv, <out>/e2_eval_summary.md, <out>/e2_eval_manifest.json."""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(1, os.path.join(ROOT, "experiments", "b1_baseline"))
from e2_common import FEATS, view_frame, rank_lists
from e2_engine import fuse_rrf, insert2
S5 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]; S3 = ["NP_H", "NP_X", "NP_N"]; NP = S5[:4]
TAGS = {"np053f1dev": ("np053_f1dev", "p2_molecules.csv", S3, "run_np053_f1dev"), "np053f2dev": ("np053_f2dev", "p2_molecules.csv", S3, "run_np053_f2dev"),
        "f1dev": ("eval_set_f1", "p2_molecules.csv", S5, "run_f1dev"), "f2dev": ("eval_set_f2", "p2_molecules.csv", S5, "run_f2dev"),
        "panel": ("panel_np250", "p1_molecules.csv", ["P_np250"], "run_panel_fe")}
LISTS = ["P", "E2", "F", "F0", "H", "pe", "Fpe", "Hp", "F1"]; ALPHA, NB, TOL = 0.5, 4000, 1e-12
CELLS_A = [("np053f1dev", "NP_H"), ("np053f1dev", "NP_N"), ("np053f2dev", "NP_H"), ("np053f2dev", "NP_N")]
CELLS_BD = [("f1dev", "D_np_single"), ("f2dev", "D_np_single")]; CELLS_B = [(t, s) for t in ("f1dev", "f2dev") for s in NP]


def stop(msg): sys.exit(f"STOP (144 v3 check): {msg}")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def rr(L, t):
    L = L[:25]; return 1.0 / (L.index(t) + 1) if t in L else 0.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ewin", default="experiments/e2/ewin"); ap.add_argument("--top", default="experiments/b1_baseline/diag"); ap.add_argument("--coco_okeys", default="experiments/e2/coco_store_okeys.parquet")
    a = ap.parse_args(); P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p); out = P_(a.out); os.makedirs(out, exist_ok=True); t0 = time.time()
    m = lgb.Booster(model_file=P_(a.model))
    if m.feature_name() != FEATS: stop("model features differ from e2_common.FEATS")
    man = dict(model=sha(P_(a.model)), code={f: sha(os.path.join(HERE, f)) for f in ("e2_eval_v3.py", "e2_common.py", "e2_engine.py")}, inputs={})
    B = os.path.join(ROOT, "experiments/b1_baseline")
    clean = set(pd.read_csv(P_("experiments/fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
    pool = pl.read_parquet(P_("data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"]); POOL_COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
    COCO_STORE = set(pd.read_parquet(P_(a.coco_okeys)).official_key.dropna().astype(str)); COCO = POOL_COCO | COCO_STORE
    ESRC_X = set(pd.read_parquet(P_("experiments/b1_baseline/diag/e_window_keys_v2.parquet")).key.astype(str))
    man["inputs"].update(coco_okeys=sha(P_(a.coco_okeys)), e_keys_v2=sha(P_("experiments/b1_baseline/diag/e_window_keys_v2.parquet")))
    rows = []; n_emptyP = 0; n_nonfinite = 0
    for tag, (d, csv, sets, run) in TAGS.items():
        tp = f"{P_(a.top)}/top102_{tag}.parquet"; man["inputs"][f"top102_{tag}"] = sha(tp)
        T = pd.read_parquet(tp); T["molecule"] = T.molecule.astype(str)
        ev = pd.read_csv(os.path.join(B, d, csv)); ev["molecule"] = ev.molecule.astype(str); truth = dict(zip(ev.molecule, ev.scorer_key.astype(str)))
        for s in sets:
            led = pd.read_csv(os.path.join(B, run, f"b1_molecules_{s}.csv")); led["molecule"] = led.molecule.astype(str); led = led.set_index("molecule")
            mols = ev[ev.set == s].molecule.tolist()
            if any(x not in led.index for x in mols): stop(f"{tag} {s}: selected molecule without a ledger row")
            exp = [(v, x) for x in mols for v in ("c2", "c1") if v == "c2" or bool(led.loc[x, "c1_usable"])]
            got = set(zip(T[T.set == s].view, T[T.set == s].molecule))
            if got - set(exp): stop(f"{tag} {s}: P groups outside the expected roster ({len(got - set(exp))})")
            pe_, pf_ = P_(f"{a.ewin}/{d}/ewin_{s}.parquet"), P_(f"{a.ewin}/{d}/e2f_{s}.parquet"); man["inputs"][f"{d}/{s}"] = [sha(pe_), sha(pf_)]
            E = pd.read_parquet(pe_); F = pd.read_parquet(pf_); E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str)
            em = pd.read_csv(P_(f"{a.ewin}/{d}/ewin_molecules_{s}.csv")); em["molecule"] = em.molecule.astype(str); built = set(em.molecule)
            for v in ("c1", "c2"):
                X = view_frame(E, F, v)
                if len(X):
                    pr = m.predict(X[FEATS]); n_nonfinite += int((~np.isfinite(pr)).sum()); R = rank_lists(X, pr)
                    EL = {g: grp.official_key.astype(str).tolist() for g, grp in R.groupby("molecule", sort=False)}
                else: EL = {}
                Pv = T[(T.set == s) & (T.view == v)]
                PL = {}
                for x, g in Pv.groupby("molecule", sort=False):
                    g = g.sort_values("rank"); ks = g.okey.astype(str).tolist()
                    if g["rank"].tolist() != list(range(1, len(g) + 1)) or len(set(ks)) != len(ks): stop(f"{tag} {s} {v} {x}: P ranks / keys")
                    PL[x] = ks[:25]
                for vv, x in exp:
                    if vv != v: continue
                    if x not in built: stop(f"{tag} {s} {x}: molecule absent from the E-window ledger (a missing table must not pass as an empty E)")
                    t = truth[x]; p = PL.get(x, []); n_emptyP += int(not p); el = EL.get(x, []); er = {k: i + 1 for i, k in enumerate(el)}; e1 = el[0] if el else None
                    if p:
                        L = dict(P=p, E2=el[:25], F=fuse_rrf(p, er, el[:25], ALPHA), F0=fuse_rrf(p, er, el[:25], 0.0), F1=fuse_rrf(p, er, el[:25], 1.0))
                        L["H"] = insert2(L["F"], e1); L["Hp"] = insert2(p, e1); L["pe"] = [k for k in p if k in er]
                        per = {k: i + 1 for i, k in enumerate(L["pe"])}; L["Fpe"] = fuse_rrf(p, per, L["pe"], ALPHA)
                        if L["F0"] != p: stop(f"{tag} {s} {v} {x}: F0 != P (ordered)")
                        if not el and L["F"] != p: stop(f"{tag} {s} {v} {x}: empty E2 changed F (ordered)")
                        if L["H"][:1] != L["F"][:1]: stop(f"{tag} {s} {v} {x}: H changed F's top 1")
                    else:   # no P list: the kernel keeps the placeholder -> every fused list = P = []
                        L = {l: [] for l in LISTS}; L["E2"] = el[:25]
                    tco = t in COCO; tpb = t in ESRC_X
                    rows.append(dict(tag=tag, set=s, view=v, molecule=x, tkey=t, t_coco=tco, t_pclbio=tpb, t_esrc=(v == "c1") or tco or tpb, t_reach=t in er,
                                     e2_rank=er.get(t, np.nan), p_rank=(p.index(t) + 1) if t in p else np.nan, n_e=len(el), p_empty=not p,
                                     panel_clean=(tag == "panel" and x in clean), **{l: rr(L[l], t) for l in LISTS}))
            print(f"  {tag} {s} ({time.time()-t0:.0f}s)", flush=True)
    if n_nonfinite: stop(f"{n_nonfinite} non-finite E2 predictions")
    G = pd.DataFrame(rows); G.to_csv(f"{out}/e2_eval_groups.csv", index=False)
    for c in LISTS:
        if not (np.isfinite(G[c]).all() and G[c].between(0, 1).all()): stop(f"{c} outside [0, 1]")
    CHK = f"groups {len(G)} (roster from the selection CSVs + C1 ledgers); P empty in {n_emptyP}; F0 == P ordered on all; empty-E2 groups {int((G.n_e == 0).sum())} unchanged; predictions finite"
    cell = lambda tg, s, vw, ex=None: (lambda r: r[ex(r)] if ex is not None else r)(G[(G.tag == tg) & (G.set == s) & (G.view == vw)])

    def boot(cells, var, vw, seed, ex=None, pooled=False, base="P"):
        rng = np.random.default_rng(seed); arrs = [(cell(t_, s_, vw, ex)[var] - cell(t_, s_, vw, ex)[base]).values.astype(float) for t_, s_ in cells]
        if pooled: arrs = [np.concatenate(arrs)]
        if any(len(x_) == 0 for x_ in arrs): stop(f"empty cell {var} {vw} {cells}")
        return float(np.mean([x_.mean() for x_ in arrs])), np.array([np.mean([x_[rng.integers(0, len(x_), len(x_))].mean() for x_ in arrs]) for _ in range(NB)])
    ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p_, bs: f"{p_:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
    stt = lambda bs, e=0.01: "harm" if ci(bs)[1] < -e else ("non-inferior" if ci(bs)[0] >= -e else "undetermined")
    PROT = {"old B f1/f2 NP C2 (C-F)": (CELLS_B, "c2", None, False), "E-outside truths C2 (A + old B, pooled)": (CELLS_A + CELLS_B, "c2", lambda r: ~r.t_esrc.astype(bool), True),
            "G C1 (f1/f2)": ([("f1dev", "G_tims_crosslib"), ("f2dev", "G_tims_crosslib")], "c1", None, False),
            "panel C1 clean": ([("panel", "P_np250")], "c1", lambda r: r.panel_clean.astype(bool), False), "053 NP C1 (4 cells)": (CELLS_A, "c1", None, False)}

    def primary(var, base="P"):
        pa, ba = boot(CELLS_A, var, "c2", 102, base=base); pb, bb = boot(CELLS_BD, var, "c2", 103, base=base)
        return 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb, (pa, ba), (pb, bb)
    L_ = [f"# 144 E2 reading, reader v3 (model {a.model}; {time.strftime('%Y-%m-%d %H:%M')})", "", f"Checks: {CHK}", "", "## Decision table (vs P; 102 registration)", "",
          "| list | primary 1/2 A + 1/2 B_D | A 053 NP C2 | B_D f1/f2 D C2 | " + " | ".join(PROT) + " | gate |", "|---|---|---|---|" + "---|" * len(PROT) + "---|"]
    RES = {}
    for v in ["F", "H", "Fpe", "Hp", "F1", "E2", "pe"]:
        p_, bs, (pa, ba), (pb, bb) = primary(v); pr = {k: boot(c_, v, vw_, 7, ex_, pool_) for k, (c_, vw_, ex_, pool_) in PROT.items()}
        gate = p_ >= 0.005 and ci(bs)[0] > 0 and ci(ba)[0] >= -0.01 and ci(bb)[0] >= -0.01 and all(ci(b_)[0] >= -0.01 for _, b_ in pr.values()); RES[v] = (p_, bs, gate, pr, ba, bb)
        L_.append(f"| {v}{'' if v in ('F', 'H') else ' (descriptive)'} | **{fmt(p_, bs)}** | {fmt(pa, ba)} | {fmt(pb, bb)} | " + " | ".join(f"{fmt(*pr[k])} ({stt(pr[k][1])})" for k in PROT) + f" | {'PASS' if gate else 'no'} |")
    ph, bh, (pha, bha), (phb, bhb) = primary("H", base="F")
    hgate = ph > 0 and ci(bh)[0] >= -0.005 and ci(RES["H"][4])[0] >= -0.01 and ci(RES["H"][5])[0] >= -0.01 and all(ci(b_)[0] >= -0.01 for _, b_ in RES["H"][3].values())
    L_ += ["", f"- **F gate: {'PASS' if RES['F'][2] else 'no'}**; H - F primary {fmt(ph, bh)} (A {pha:+.4f}, B_D {phb:+.4f}); **H gate (H - F point > 0, lower >= -0.005; H - P: A, B_D and the protections lower >= -0.01): {'PASS' if hgate else 'no'}**"]
    def esrc_fold(f):
        cells = [c for c in CELLS_A + CELLS_B if c[0] in (("np053f1dev", "f1dev") if f == 1 else ("np053f2dev", "f2dev"))]
        r = pd.concat([cell(t_, s_, "c2") for t_, s_ in cells]); r = r[r.t_esrc.astype(bool)]; return float((r.F - r.P).mean()), len(r)
    g1, n1 = esrc_fold(1); g2, n2 = esrc_fold(2); ra = pd.concat([cell(t_, s_, "c2") for t_, s_ in CELLS_A + CELLS_B])
    resc = int(((ra.F == 1) & (ra.P < 1)).sum()); resc_id = int(ra[(ra.F == 1) & (ra.P < 1)].tkey.nunique()); lost1 = int(((ra.P == 1) & (ra.F < 1)).sum())
    diag_ok = g1 > 0 and g2 > 0 and resc_id >= 10
    L_ += [f"- Public diagnostic path: E-source (fixed membership) C2 F - P fold 1 {g1:+.4f} (n {n1}), fold 2 {g2:+.4f} (n {n2}); new rank-1 {resc} groups / {resc_id} identities, lost rank-1 {lost1} (A + old B C2) -> **{'eligible' if diag_ok else 'not eligible'}**"]
    def rows_(cells, vw, ex=None):
        r = pd.concat([cell(t_, s_, vw) for t_, s_ in cells]); return r[ex(r)] if ex is not None else r
    LAY = [("A 053 NP C2", CELLS_A, "c2", None), ("B_D f1/f2 D C2", CELLS_BD, "c2", None), ("old B f1/f2 NP C2", CELLS_B, "c2", None), ("G C1", PROT["G C1 (f1/f2)"][0], "c1", None),
           ("panel C1 clean", [("panel", "P_np250")], "c1", lambda r: r.panel_clean.astype(bool)), ("053 NP C1", CELLS_A, "c1", None), ("f1/f2 NP C1", CELLS_B, "c1", None), ("panel C2", [("panel", "P_np250")], "c2", None)]
    L_ += ["", "## Diagnostics (row means; not used for the decision)", "", "| layer | n | " + " | ".join(LISTS) + " | oracle max(P, E2) | t_esrc | t_coco | t_reach (view window) | truth in E2 top 25 |", "|---|---:|" + "---:|" * (len(LISTS) + 5)]
    for lab, cells, vw, ex in LAY:
        try: r = rows_(cells, vw, ex)
        except ValueError: continue
        if not len(r): continue
        L_.append(f"| {lab} | {len(r)} | " + " | ".join(f"{r[l].mean():.4f}" for l in LISTS) + f" | {np.maximum(r.P, r.E2).mean():.4f} | {r.t_esrc.mean():.3f} | {r.t_coco.mean():.3f} | {r.t_reach.mean():.3f} | {(r.e2_rank <= 25).mean():.3f} |")
    L_ += ["", "| list | layer | rescued | lost | new rank-1 | lost rank-1 | d truth E-source (n) | d truth outside (n) | d COCONUT truth (n) | d E-source not reached (n) |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for v in ["F", "H", "Fpe"]:
        for lab, cells in (("A", CELLS_A), ("B_D", CELLS_BD), ("old B", CELLS_B)):
            r = rows_(cells, "c2"); dd = r[v] - r.P; mm = lambda m_: f"{dd[m_].mean():+.4f} ({int(m_.sum())})" if m_.sum() else "n/a"
            L_.append(f"| {v} | {lab} | {int((dd > TOL).sum())} | {int((dd < -TOL).sum())} | {int(((r[v] == 1) & (r.P < 1)).sum())} | {int(((r.P == 1) & (r[v] < 1)).sum())} | "
                      f"{mm(r.t_esrc.astype(bool))} | {mm(~r.t_esrc.astype(bool))} | {mm(r.t_coco.astype(bool))} | {mm(r.t_esrc.astype(bool) & ~r.t_reach.astype(bool))} |")
    r = rows_(CELLS_A + CELLS_B, "c2"); g_ = float((r.F - r.P)[r.t_esrc.astype(bool)].mean()); c_ = float((r.F - r.P)[~r.t_esrc.astype(bool)].mean())
    rc = r[~r.t_esrc.astype(bool) & (r.P > 0)]; c2_ = float((rc.F - rc.P).mean()) if len(rc) else float("nan")
    be = (-c_ / (g_ - c_)) if (g_ > 0 > c_) else float("nan"); be2 = (-c2_ / (g_ - c2_)) if (g_ > 0 > c2_) else float("nan")
    d_ = [x - y for x, y in zip(primary('F')[:2], primary('Fpe')[:2])]
    L_ += ["", f"- Mixture sensitivity (A + old B C2): E-source g {g_:+.4f}, E-outside c {c_:+.4f} (all E-outside rows) / {c2_:+.4f} (E-outside rows that P reaches, n {len(rc)}); "
           f"break-even E-source share w* = {be:.3f} / {be2:.3f}; not an estimate of the hidden w.",
           f"- F - Fpe (E2's ordering beyond source re-weighting), primary weights: {fmt(*d_)}",
           f"- Rank-1 complementarity, C2 A + old B: P right & E2 wrong {int(((r.P == 1) & (r.E2 < 1)).sum())}, E2 right & P wrong {int(((r.E2 == 1) & (r.P < 1)).sum())}, both {int(((r.P == 1) & (r.E2 == 1)).sum())}; "
           f"truths found by E2 outside P's top 25: {int(((r.p_rank.isna()) & (r.e2_rank <= 25)).sum())}"]
    open(f"{out}/e2_eval_summary.md", "w", encoding="utf-8").write("\n".join(L_) + "\n"); man["seconds"] = round(time.time() - t0)
    json.dump(man, open(f"{out}/e2_eval_manifest.json", "w"), indent=1); print("\n".join(L_)); print(f"E2_EVAL_V3_DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
