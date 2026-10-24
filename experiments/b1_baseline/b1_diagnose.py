"""Failure-mode diagnostic for a B1 run/set (CPU only).

Where is MRR lost: window -> external reach -> shortlist -> ranking (class-2 view, strict); when the truth is in the shortlist but not
first under the fixed rule S = z(FP) + 2 z(GL) + z(ICE) + 0.5 pop, which component ranks it where, which term pushes the winner above
the truth, what the winner looks like (library structure? same formula? similarity to the truth?), and the oracle / rerank ceilings.
Class-1 view: how often the best library match is the truth, the confidence margin, and the false-confident cases (libpri risk).

Usage: python -X utf8 b1_diagnose.py --run experiments/b1_baseline/run1_v2 --eval_csv experiments/b1_baseline/eval_set/p1_molecules.csv --sets A_timstof B_nplib
Writes <run>/results/diagnose_<set>.md and diagnose_<set>_molecules.csv.
"""
import argparse, json, os
import numpy as np, pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdMolDescriptors, rdFingerprintGenerator

RDLogger.DisableLog("rdApp.*")
GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
W = dict(fp=1.0, gl=2.0, ice=1.0, pop=0.5)   # the fixed rule S(2,1,0.5)


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.full_like(x, np.nan)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    elif ok.sum() >= 1: out[ok] = 0.0
    if ok.any(): out[~ok] = np.nanmin(out[ok]) if ok.sum() else 0.0
    else: out[:] = 0.0
    return out


def term(vals, available):
    v = np.asarray(vals, float)
    return z(v) if available and np.isfinite(v).sum() >= 2 else None


def rank_of(scores, is_t):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    return int(np.sum(s >= s[is_t][0])) if is_t.any() else None


_fc, _mc = {}, {}


def mol(smi):
    if smi not in _mc: _mc[smi] = Chem.MolFromSmiles(smi)
    return _mc[smi]


def formula(smi):
    if smi not in _fc:
        m = mol(smi); _fc[smi] = rdMolDescriptors.CalcMolFormula(m) if m is not None else None
    return _fc[smi]


def tanimoto(a, b):
    ma, mb = mol(a), mol(b)
    if ma is None or mb is None: return np.nan
    return float(DataStructs.TanimotoSimilarity(GEN.GetFingerprint(ma), GEN.GetFingerprint(mb)))


def load(run, s, model):
    p = f"{run}/work/{model}_{s}.json"
    try: ok = json.load(open(p + ".meta.json")).get("status") == "ok"
    except Exception: ok = False
    return (json.load(open(p)) if ok else {}), ok


def vals(d, mid, smiles):
    dm = d.get(mid) or {}
    return np.array([np.nan if dm.get(sm) is None else float(dm[sm]) for sm in smiles], float)


def components(g, mid, gl, gl_ok, ice, ice_ok):
    terms = {"fp": z(g.fp.values.astype(float)), "gl": term(vals(gl, mid, g.smiles), gl_ok), "ice": term(vals(ice, mid, g.smiles), ice_ok),
             "pop": g.pop_public.values.astype(float)}
    terms = {k: v for k, v in terms.items() if v is not None}
    S = sum(W[k] * v for k, v in terms.items())
    return terms, S


def pct(a, b): return f"{100.0 * a / b:.0f}%" if b else "-"


def analyse(run, s, md):
    F = pd.read_parquet(f"{run}/b1_features_{s}.parquet"); M = pd.read_csv(f"{run}/b1_molecules_{s}.csv").set_index("molecule")
    gl, gl_ok = load(run, s, "gl"); ice, ice_ok = load(run, s, "ice")
    c1u = M["c1_usable"].fillna(False).astype(bool).to_dict() if "c1_usable" in M.columns else {}
    recs = []
    for mid, g0 in F.groupby("molecule", sort=False):
        rec = dict(molecule=mid, n_window=len(g0))
        # ---------------- class-2 view (the view's shortlist; no candidate without any external source once train membership is hidden)
        keep = g0.in_short_c2.values.astype(bool) & (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
        g = g0[keep].reset_index(drop=True); rec["c2_n"] = len(g)
        is_t = g.is_truth.values.astype(bool); rec["c2_truth_in_short"] = bool(is_t.any())
        if is_t.any():
            terms, S = components(g, mid, gl, gl_ok, ice, ice_ok)
            ranks = {k: rank_of(v, is_t) for k, v in terms.items()}; ranks["S"] = rank_of(S, is_t)
            rec.update({f"c2_rank_{k}": v for k, v in ranks.items()})
            rec["c2_oracle_top1"] = any(r == 1 for k, r in ranks.items() if k != "S")
            rec["c2_rr"] = 1.0 / ranks["S"] if ranks["S"] <= 25 else 0.0
            ti = int(np.flatnonzero(is_t)[0]); ts = g.smiles[ti]
            rec["c2_n_same_formula"] = int(sum(formula(x) == formula(ts) for x in g.smiles))
            rec["c2_t_pop"] = float(terms["pop"][ti]); rec["c2_t_in_coconut"] = bool(g.in_coconut[ti])
            if ranks["S"] > 1:
                wi = int(np.argmax(np.nan_to_num(S, nan=-1e18))); ws = g.smiles[wi]
                contrib = {k: W[k] * (v[wi] - v[ti]) for k, v in terms.items()}      # > 0: this term pushes the winner above the truth
                rec["c2_blame"] = max(contrib, key=contrib.get); rec.update({f"c2_d_{k}": float(v) for k, v in contrib.items()})
                rec["c2_w_same_formula"] = formula(ts) == formula(ws); rec["c2_w_tanimoto"] = tanimoto(ts, ws)
                rec["c2_w_in_train"] = bool(g.in_train_c2[wi]); rec["c2_w_in_coconut"] = bool(g.in_coconut[wi]); rec["c2_w_pop"] = float(terms["pop"][wi])
                # the truth's similarity to the whole top-5 (is the error a near-isomer crowd?)
                top5 = np.argsort(-np.nan_to_num(S, nan=-1e18))[:5]
                rec["c2_top5_max_tanimoto"] = float(np.nanmax([tanimoto(ts, g.smiles[j]) for j in top5 if j != ti] or [np.nan]))
        # ---------------- class-1 view (library references of the truth kept; duplicates of the query removed)
        if c1u.get(mid, False):
            g1 = g0[g0.in_short_c1.values.astype(bool)].reset_index(drop=True); is_t1 = g1.is_truth.values.astype(bool)
            rec["c1_truth_in_short"] = bool(is_t1.any())
            if is_t1.any():
                lib = g1.lib_sim_c1.values.astype(float); fpz = z(g1.fp.values.astype(float))
                rec["c1_rank_lib"] = rank_of(lib + 1e-6 * fpz, is_t1)
                srt = np.sort(lib)[::-1]; rec["c1_lib_max"] = float(srt[0]); rec["c1_lib_margin"] = float(srt[0] - (srt[1] if len(srt) > 1 else 0.0))
                rec["c1_truth_lib"] = float(lib[is_t1][0])
                terms1, S1 = components(g1, mid, gl, gl_ok, ice, ice_ok); rec["c1_rank_S"] = rank_of(S1, is_t1)
                # libpri(0.8, 0.2) decision for this molecule
                pri = (srt[0] >= 0.8) and (rec["c1_lib_margin"] >= 0.2); rec["c1_libpri_fires"] = bool(pri)
                if pri: v = np.where(lib >= 0.8, 100.0 + lib, S1); rec["c1_rank_libpri"] = rank_of(v, is_t1)
                else: rec["c1_rank_libpri"] = rec["c1_rank_S"]
                if rec["c1_rank_lib"] > 1:
                    wi = int(np.argmax(lib)); ti1 = int(np.flatnonzero(is_t1)[0])
                    rec["c1_w_tanimoto"] = tanimoto(g1.smiles[ti1], g1.smiles[wi]); rec["c1_w_in_train"] = bool(g1.in_train_c1[wi])
                    rec["c1_w_same_formula"] = formula(g1.smiles[ti1]) == formula(g1.smiles[wi])
        recs.append(rec)
    D = pd.DataFrame(recs).set_index("molecule").reindex(M.index)
    keep_m = [c for c in ("group", "lib", "n_query", "n_adducts", "n_unique", "truth_in_window", "reach_external_b1", "c1_usable", "truth_lib_sim_c1") if c in M.columns]
    D = D.join(M[keep_m])
    reach = D.reach_external_b1.fillna(False).astype(bool).values; N = len(D)
    inshort = D.c2_truth_in_short.fillna(False).astype(bool).values
    rank = D.c2_rank_S.values.astype(float)
    rr = np.where(inshort & reach, D.c2_rr.fillna(0.0).values, 0.0)
    md.append(f"## {s} (N={N}; GL {'ok' if gl_ok else 'missing'}; ICE {'ok' if ice_ok else 'missing'})\n")
    # ---- funnel (class-2, strict)
    stages = [("truth in B1 window", D.truth_in_window.fillna(False).astype(bool).values),
              ("reachable via PubChem/COCONUT (strict denominator)", reach),
              ("truth in class-2 shortlist", reach & inshort),
              ("rank 1 under S(2,1,0.5)", reach & inshort & (rank == 1)),
              ("rank 2-5", reach & inshort & (rank >= 2) & (rank <= 5)),
              ("rank 6-25", reach & inshort & (rank >= 6) & (rank <= 25)),
              ("rank > 25", reach & inshort & (rank > 25))]
    md.append("### Class-2 funnel (strict: unreachable = 0)\n\n| stage | molecules | share of N | MRR mass lost here (of N) |\n|---|---:|---:|---:|")
    lost_unreach = (~reach).sum() / N; lost_noshort = (reach & ~inshort).sum() / N
    for name, m in stages:
        lost = ""
        if name.startswith("reachable"): lost = f"{lost_unreach:.3f} (unreachable)"
        elif name.startswith("truth in class-2"): lost = f"{lost_noshort:.3f} (not shortlisted)"
        elif name.startswith("rank 2-5"): lost = f"{np.sum(1 - rr[m]) / N:.3f}"
        elif name.startswith("rank 6-25"): lost = f"{np.sum(1 - rr[m]) / N:.3f}"
        elif name.startswith("rank > 25"): lost = f"{m.sum() / N:.3f}"
        md.append(f"| {name} | {int(m.sum())} | {pct(m.sum(), N)} | {lost} |")
    md.append(f"\nstrict MRR@25 = {rr.sum() / max(reach.sum(), 1):.3f} over {int(reach.sum())} reachable; all-N MRR (unreachable counted 0) = {rr.sum() / N:.3f}; "
              f"top-1 (reachable) = {np.sum(rank[reach & inshort] == 1) / max(reach.sum(), 1):.3f}\n")
    # ---- component ranks among reachable truths in the shortlist
    sub = D[reach & inshort]
    md.append("### Where each component ranks the truth (reachable, truth in shortlist)\n\n| component | n | truth top-1 | top-5 | top-25 | median rank |\n|---|---:|---:|---:|---:|---:|")
    for k in ("fp", "gl", "ice", "pop", "S"):
        c = f"c2_rank_{k}"
        if c not in sub.columns or sub[c].isna().all(): continue
        r = sub[c].dropna().values.astype(float)
        md.append(f"| {k} | {len(r)} | {pct((r == 1).sum(), len(r))} | {pct((r <= 5).sum(), len(r))} | {pct((r <= 25).sum(), len(r))} | {np.median(r):.0f} |")
    oracle = sub.c2_oracle_top1.fillna(False).astype(bool).values
    md.append(f"\noracle 'pick the right component per molecule' top-1 = {pct(oracle.sum(), len(sub))} vs S top-1 {pct((sub.c2_rank_S == 1).sum(), len(sub))}; "
              f"truth in S top-5 = {pct((sub.c2_rank_S <= 5).sum(), len(sub))} (rerank ceiling), top-25 = {pct((sub.c2_rank_S <= 25).sum(), len(sub))}; "
              f"median shortlist size {sub.c2_n.median():.0f}, median candidates with the truth's formula {sub.c2_n_same_formula.median():.0f}\n")
    # ---- what beats the truth
    err = sub[sub.c2_rank_S > 1]
    if len(err):
        md.append("### When S is wrong: which term pushes the winner above the truth\n\n| blamed term | errors | share | mean push (score units) | winner is a library structure | winner in COCONUT | truth in COCONUT | winner Tanimoto to truth (median) | winner Tanimoto >= 0.7 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for k, e in err.groupby("c2_blame"):
            md.append(f"| {k} | {len(e)} | {pct(len(e), len(err))} | {e[f'c2_d_{k}'].mean():.2f} | {pct(e.c2_w_in_train.sum(), len(e))} | {pct(e.c2_w_in_coconut.sum(), len(e))} | "
                      f"{pct(e.c2_t_in_coconut.sum(), len(e))} | {e.c2_w_tanimoto.median():.2f} | {pct((e.c2_w_tanimoto >= 0.7).sum(), len(e))} |")
        md.append(f"\nall errors: {len(err)}; winner has the truth's formula in {pct(err.c2_w_same_formula.sum(), len(err))}; winner pop > truth pop in "
                  f"{pct((err.c2_w_pop > err.c2_t_pop).sum(), len(err))}; max Tanimoto of the S top-5 to the truth: median {err.c2_top5_max_tanimoto.median():.2f}\n")
        md.append("mean push per term over all errors (positive = hurts the truth): " + ", ".join(f"{k} {err[f'c2_d_{k}'].mean():+.2f}" for k in ("fp", "gl", "ice", "pop") if f"c2_d_{k}" in err.columns) + "\n")
    # ---- strata
    md.append("### Strict MRR by stratum\n\n| stratum | value | n (reachable) | strict MRR | top-1 |\n|---|---|---:|---:|---:|")
    strata = [c for c in ("group", "lib", "n_adducts", "n_query") if c in D.columns]
    D["_rr"] = rr; D["_top1"] = (rank == 1) & inshort
    for c in strata:
        col = D[c]
        if c in ("n_query",): col = pd.cut(col, [0, 1, 3, 10, 1e9], labels=["1", "2-3", "4-10", ">10"])
        for v, e in D[reach].groupby(col[reach], observed=True):
            if len(e) < 5: continue
            md.append(f"| {c} | {v} | {len(e)} | {e._rr.mean():.3f} | {e._top1.mean():.3f} |")
    q = pd.qcut(D.n_unique[reach], 4, duplicates="drop")
    for v, e in D[reach].groupby(q, observed=True): md.append(f"| window size (unique structures) | {v} | {len(e)} | {e._rr.mean():.3f} | {e._top1.mean():.3f} |")
    # ---- class-1 view
    c1 = D[D.c1_usable.fillna(False).astype(bool)] if "c1_usable" in D.columns else D.iloc[0:0]
    if len(c1):
        ok1 = c1.c1_truth_in_short.fillna(False).astype(bool); c1s = c1[ok1]
        md.append(f"\n### Class-1 view ({len(c1)} usable molecules; truth in shortlist {int(ok1.sum())})\n")
        md.append(f"best library match is the truth: {pct((c1s.c1_rank_lib == 1).sum(), len(c1s))}; S(2,1,0.5) top-1: {pct((c1s.c1_rank_S == 1).sum(), len(c1s))}; "
                  f"libpri(0.8,0.2) fires in {pct(c1s.c1_libpri_fires.sum(), len(c1s))} and is top-1 in {pct((c1s.c1_rank_libpri == 1).sum(), len(c1s))}; "
                  f"MRR lib-only {np.mean(np.where(c1s.c1_rank_lib <= 25, 1 / c1s.c1_rank_lib, 0)):.3f}, S {np.mean(np.where(c1s.c1_rank_S <= 25, 1 / c1s.c1_rank_S, 0)):.3f}, "
                  f"libpri {np.mean(np.where(c1s.c1_rank_libpri <= 25, 1 / c1s.c1_rank_libpri, 0)):.3f}\n")
        md.append("| truth library similarity | n | lib top-1 | S top-1 | libpri top-1 |\n|---|---:|---:|---:|---:|")
        for v, e in c1s.groupby(pd.cut(c1s.c1_truth_lib, [-1, 0.4, 0.6, 0.8, 0.9, 1.01], labels=["<0.4", "0.4-0.6", "0.6-0.8", "0.8-0.9", ">=0.9"]), observed=True):
            md.append(f"| {v} | {len(e)} | {pct((e.c1_rank_lib == 1).sum(), len(e))} | {pct((e.c1_rank_S == 1).sum(), len(e))} | {pct((e.c1_rank_libpri == 1).sum(), len(e))} |")
        fc = c1s[(c1s.c1_lib_max >= 0.8) & (c1s.c1_rank_lib > 1)]
        md.append(f"\nfalse-confident library hits (lib max >= 0.8 but the best match is not the truth): {len(fc)} of {int((c1s.c1_lib_max >= 0.8).sum())} confident cases; "
                  f"of these, margin >= 0.2: {int((fc.c1_lib_margin >= 0.2).sum())}; winner Tanimoto to truth median {fc.c1_w_tanimoto.median() if len(fc) else float('nan'):.2f}; "
                  f"winner is itself a library structure: {pct(fc.c1_w_in_train.sum(), len(fc))}\n")
    D.drop(columns=["_rr", "_top1"]).to_csv(f"{run}/results/diagnose_{s}_molecules.csv")
    return D


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True)
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); a = ap.parse_args()
    os.makedirs(f"{a.run}/results", exist_ok=True)
    for s in a.sets:
        md = [f"# B1 failure diagnostic: {a.run} / {s}", ""]
        analyse(a.run, s, md)
        open(f"{a.run}/results/diagnose_{s}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
        print("\n".join(md))


if __name__ == "__main__":
    main()
