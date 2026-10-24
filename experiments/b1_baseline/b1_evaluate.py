"""B1 step 2 -- fixed-rule evaluation of the unified candidate table under the class-1 (C1) and class-2 (C2) scenario views.

Inputs: <run>/b1_features_<set>.parquet, <run>/b1_molecules_<set>.csv, <run>/work/{gl,ice}_<set>.json (runner outputs with status ok),
        --eval_csv (selection table with window_external for the strict class-2 mask).
Views : C2 -> lib_sim_c2 / in_train_c2 (every reference of the truth removed, truth's train membership hidden); strict = truth reachable
             only via train structures counts 0 (window_external False).
        C1 -> lib_sim_c1 / in_train_c1 (truth's other-library references kept); reported on molecules with c1_possible (truth has
             other-library spectra) and on all molecules.
Scores: z within the molecule's shortlist (ddof=1 over finite values); a model term is dropped when it has < 2 finite values on the
        list; a candidate missing a score that the rest of the list has gets the list minimum (penalised, never 'average').
Rules : prior | fp | fp+0.15pop | lib only | S(w_gl,w_ice,lam) = z(fp)+w_gl z(gl)+w_ice z(ice)+lam pop | S + beta*lib_sim |
        lib-priority(tau, margin): if the best library match >= tau and beats the second identity by >= margin, candidates with
        lib_sim >= tau lead (by lib_sim), the rest follow by S; otherwise S.
Usage: python -X utf8 b1_evaluate.py --run DIR --eval_csv CSV [--sets A_timstof B_nplib] [--out DIR]
"""
import argparse, json, os
import numpy as np, pandas as pd

rng = np.random.default_rng(20261024)
LAM = 0.15


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.full_like(x, np.nan)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0: out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    elif ok.sum() >= 1: out[ok] = 0.0
    if ok.any(): out[~ok] = np.nanmin(out[ok]) if ok.sum() else 0.0
    else: out[:] = 0.0
    return out


def rr(scores, is_t):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    if not is_t.any(): return 0.0, None
    rank = int(np.sum(s >= s[is_t][0])); return (1.0 / rank if rank <= 25 else 0.0), rank


def boot(v, n=20000):
    v = np.asarray(v, float); idx = rng.integers(0, len(v), (n, len(v))); return [float(q) for q in np.quantile(v[idx].mean(1), [.025, .975])]


def term(vals, available):
    """z of a model's scores if the list has >= 2 finite values, else None (term dropped)."""
    v = np.asarray(vals, float)
    return z(v) if available and np.isfinite(v).sum() >= 2 else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True)
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"]); ap.add_argument("--out", default=None)
    a = ap.parse_args(); out = a.out or f"{a.run}/results"; os.makedirs(out, exist_ok=True)
    ev = pd.read_csv(a.eval_csv).set_index("molecule")
    md = ["# B1 fixed-rule evaluation", ""]; allres = {}
    for s in a.sets:
        F = pd.read_parquet(f"{a.run}/b1_features_{s}.parquet"); M = pd.read_csv(f"{a.run}/b1_molecules_{s}.csv").set_index("molecule")

        def load(model):
            p = f"{a.run}/work/{model}_{s}.json"
            try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
            except Exception: ok = False
            return (json.load(open(p)) if ok else {}), ok
        gl, gl_ok = load("gl"); ice, ice_ok = load("ice")
        print(f"{s}: molecules {len(M)} | shortlist rows {len(F)} | GL {gl_ok} | ICE {ice_ok}")
        rows = []
        gl = gl or {}; ice = ice or {}
        for mid, g0 in F.groupby("molecule", sort=False):
            rec = dict(molecule=mid, n=len(g0), truth_in_shortlist=False, gl_cov=0.0, ice_cov=0.0)
            for view in ("c2", "c1"):
                # the view's own shortlist (per-view library slot; Codex 006) and, in the class-2 view, no candidate that exists in no external
                # source once its train membership is hidden (otherwise 'no source flags' identifies the truth)
                keep = g0[f"in_short_{view}"].values.astype(bool) if f"in_short_{view}" in g0.columns else np.ones(len(g0), bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
                g = g0[keep].reset_index(drop=True)
                if len(g) == 0:
                    rec[f"{view}:n"] = 0; continue
                is_t = g.is_truth.values.astype(bool); fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float)
                glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
                zfp = z(fp); zgl = term(glv, gl_ok); zice = term(icv, ice_ok)
                rec[f"{view}:n"] = len(g)
                if view == "c2": rec["truth_in_shortlist"] = bool(is_t.any()); rec["gl_cov"] = float(np.isfinite(glv).mean()); rec["ice_cov"] = float(np.isfinite(icv).mean())

                def S(w_gl=1.0, w_ice=1.0, lam=LAM, zfp=zfp, zgl=zgl, zice=zice, pop=pop):
                    v = zfp.copy()
                    if zgl is not None: v = v + w_gl * zgl
                    if zice is not None: v = v + w_ice * zice
                    return v + lam * pop
                lib = g[f"lib_sim_{view}"].values.astype(float)
                res = {"prior": pop + 1e-9 * zfp, "fp": zfp, "fp+0.15pop": zfp + LAM * pop, "lib": lib + 1e-6 * zfp,
                       "S(1,1,0.15)": S(1, 1, LAM), "S(2,1,0.15)": S(2, 1, LAM), "S(2,1,0)": S(2, 1, 0.0), "S(1,1,0)": S(1, 1, 0.0), "S(2,1,0.5)": S(2, 1, 0.5),
                       # ICE contribution (Codex 008 / ICE repaired on B): no ICE term, double ICE, GL-only, FP-only fusion
                       "S(2,0,0.5)": S(2, 0, 0.5), "S(2,2,0.5)": S(2, 2, 0.5), "S(0,1,0.5)": S(0, 1, 0.5), "S(1,0,0.5)": S(1, 0, 0.5),
                       # prior-weight regime (panel diagnostic 2026-10-24: the public pipelines lean on the documentation prior on test-like natural products)
                       "S(2,1,1)": S(2, 1, 1.0), "S(2,1,2)": S(2, 1, 2.0), "S(2,1,4)": S(2, 1, 4.0), "S(2,0,1)": S(2, 0, 1.0), "S(2,0,2)": S(2, 0, 2.0),
                       # forward-free (Codex 011): FP + lambda * prior only, the prior diagnostic that avoids MSG-contaminated forward models
                       "S(0,0,0.15)": S(0, 0, 0.15), "S(0,0,0.5)": S(0, 0, 0.5), "S(0,0,1)": S(0, 0, 1.0), "S(0,0,2)": S(0, 0, 2.0), "S(0,0,4)": S(0, 0, 4.0)}
                base = S(2, 1, LAM)
                for beta in (1.0, 2.0, 4.0): res[f"S(2,1,0.15)+{beta:g}lib"] = base + beta * lib
                top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
                base5 = S(2, 1, 0.5)
                res["S(2,1,0.5)+1lib"] = base5 + 1.0 * lib
                # negative library evidence (Codex 008 Q4): a library structure with comparable (same-adduct) references that do not match the query loses prior weight
                nsame = g[f"lib_nsame_{view}"].values.astype(float) if f"lib_nsame_{view}" in g.columns else g[f"lib_nref_{view}"].values.astype(float)
                neg = g[f"in_train_{view}"].values.astype(bool) & (nsame >= 1) & (g[f"lib_same_{view}"].values.astype(float) < 0.3)
                for dec in (0.5, 0.0): res[f"S(2,1,0.5)negev{dec:g}"] = S(2, 1, 0.5, pop=np.where(neg, dec * pop, pop))
                for tau, margin in ((0.5, 0.1), (0.6, 0.1), (0.7, 0.1), (0.8, 0.2), (0.9, 0.2)):
                    pri = (lib.max() >= tau) and (lib.max() - second >= margin)
                    v = base5.copy()
                    if pri: v = np.where(lib >= tau, 100.0 + lib, v)
                    res[f"libpri(tau={tau},m={margin})>S(2,1,0.5)"] = v
                # consistency rule: promote the best library match only if it is also among the top-3 of S
                for tau in (0.6, 0.8):
                    v = base5.copy(); i = int(np.argmax(lib)); rank_i = int(np.sum(base5 >= base5[i]))
                    if lib[i] >= tau and lib[i] - second >= 0.1 and rank_i <= 3: v[i] = 100.0
                    res[f"libpri(tau={tau})&S-top3>S(2,1,0.5)"] = v
                for name, sc in res.items():
                    r, rank = rr(sc, is_t); rec[f"{view}:{name}"] = r; rec[f"{view}:{name}@rank"] = rank
                rec[f"{view}:lib_max"] = float(lib.max()); rec[f"{view}:truth_lib"] = float(lib[is_t][0]) if is_t.any() else None
            rows.append(rec)
        D = pd.DataFrame(rows).set_index("molecule").reindex(M.index)
        mcols = [c for c in ("group", "lib", "n_query", "n_adducts", "ce_known", "n_unique", "truth_in_window", "c1_possible", "c1_usable", "truth_other_lib_refs", "lib_max_c1", "lib_max_c2", "reach_external_b1") if c in M.columns]
        D = D.join(M[mcols])
        D = D.join(ev[["window_external", "db_present_external"]], how="left")
        # strict class-2 mask: the B1 windows' own external reach when available (Codex 006), else the selection-time flag
        if "reach_external_b1" in D.columns: D["window_external"] = D["reach_external_b1"].fillna(False).astype(bool)
        if "c1_usable" in D.columns: D["c1_possible"] = D["c1_usable"].fillna(False).astype(bool)
        rules = sorted({c.split(":", 1)[1] for c in D.columns if c.startswith("c2:") and not c.endswith("@rank") and c.split(":", 1)[1] not in ("lib_max", "truth_lib", "n")},
                       key=lambda x: ["prior", "fp", "fp+0.15pop", "lib"].index(x) if x in ("prior", "fp", "fp+0.15pop", "lib") else 10)
        for c in [c for c in D.columns if (":" in c) and not c.endswith(("@rank", "lib_max", "truth_lib", ":n"))]: D[c] = D[c].fillna(0.0)
        reach = D.window_external.fillna(False).astype(bool).values; c1ok = D.c1_possible.fillna(False).astype(bool).values
        N = len(D); res = dict(set=s, n=N, n_reachable=int(reach.sum()), n_c1_possible=int(c1ok.sum()), gl_ok=gl_ok, ice_ok=ice_ok, rules={})
        md += [f"## {s} (N={N}; truth in shortlist {int(D.truth_in_shortlist.fillna(False).sum())}; reachable via external DB {int(reach.sum())}; class-1 possible {int(c1ok.sum())}; "
               f"GL {'ok' if gl_ok else 'missing'} cover {D.gl_cov.mean():.2f}; ICE {'ok' if ice_ok else 'missing'} cover {D.ice_cov.mean():.2f})", "",
               "| rule | C2 MRR@25 (all) | C2 strict | C2 top-1 | C1 MRR@25 (c1-possible) | C1 top-1 | C1 all | fit/tune/eval (C2 strict) |", "|---|---:|---:|---:|---:|---:|---:|---|"]
        ref2 = D["c2:S(2,1,0.15)"].values.astype(float) * reach
        for rname in rules:
            v2 = D[f"c2:{rname}"].values.astype(float); v1 = D[f"c1:{rname}"].values.astype(float)
            s2 = v2 * reach; d = s2 - ref2
            byg = D.assign(_s=s2).groupby("group")["_s"].mean()
            r = dict(c2_all=float(v2.mean()), c2_strict=float(s2.mean()), c2_strict_ci=boot(s2), c2_top1_strict=float(((D[f"c2:{rname}@rank"] == 1) & reach).mean()),
                     c1_possible=float(v1[c1ok].mean()) if c1ok.any() else None, c1_possible_ci=boot(v1[c1ok]) if c1ok.sum() > 1 else None,
                     c1_top1_possible=float((D[f"c1:{rname}@rank"].values[c1ok] == 1).mean()) if c1ok.any() else None, c1_all=float(v1.mean()),
                     delta_vs_S21_strict=float(d.mean()), delta_ci=boot(d), by_group_c2_strict={k: float(v) for k, v in byg.items()})
            res["rules"][rname] = r
            c1p = f"{r['c1_possible']:.3f}" if r["c1_possible"] is not None else "-"; c1t = f"{r['c1_top1_possible']:.3f}" if r["c1_top1_possible"] is not None else "-"
            md.append(f"| {rname} | {r['c2_all']:.3f} | {r['c2_strict']:.3f} [{r['c2_strict_ci'][0]:.3f},{r['c2_strict_ci'][1]:.3f}] | {r['c2_top1_strict']:.3f} | {c1p} | {c1t} | {r['c1_all']:.3f} | "
                      + " / ".join(f"{byg.get(k, float('nan')):.3f}" for k in ("fit", "tune", "eval")) + " |")
        # library-search diagnostics on the class-1-possible molecules
        if c1ok.any():
            tl = D.loc[c1ok, "c1:truth_lib"].astype(float); lm = D.loc[c1ok, "c1:lib_max"].astype(float)
            md += ["", f"C1 diagnostics (n={int(c1ok.sum())}): truth library similarity median {tl.median():.3f} (p25 {tl.quantile(.25):.3f}); truth is the best library match in {int((tl >= lm - 1e-9).sum())} molecules; "
                   f"lib-only rule MRR {D.loc[c1ok, 'c1:lib'].mean():.3f}; molecules with lib_max >= 0.6: {int((lm >= 0.6).sum())}"]
        md.append("")
        D.to_csv(f"{out}/b1_per_molecule_{s}.csv"); allres[s] = res
        print("\n".join(md[-(len(rules) + 8):]))
    json.dump(allres, open(f"{out}/b1_results.json", "w"), indent=1); open(f"{out}/b1_results.md", "w", encoding="utf-8").write("\n".join(md))
    print("saved", out)


if __name__ == "__main__":
    main()
