"""Why does the learned fusion lose where the fixed rule wins? Inference-time probe on a stored run (no retraining).
For a run (b1_features output + runner outputs), a LambdaRank model and a view: the learned / fixed rank of the truth per molecule, the feature
values of the truth and of the learned top-1, LightGBM per-feature contributions (pred_contrib) truth minus learned top-1 on the molecules the
learned model loses (fixed top-1, learned not), learned MRR by the truth's reference count / similarity / in_train, inference-time ablations
(feature groups reset to their 'no reference' values) and the library-priority guard over the learned list.
Usage: python b1_learned_probe.py --run DIR --set S --model rank_v2/lambdarank.txt --w_ice 1 --views c1 c2 --out <md>
"""
import argparse, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_rankfeats import feature_matrix, zlist, term
from b1_locked_eval import runner, view_frame
import lightgbm as lgb

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--set", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--w_ice", type=float, default=1.0); ap.add_argument("--views", nargs="+", default=["c1", "c2"]); ap.add_argument("--min_gl_cover", type=float, default=0.5)
ap.add_argument("--label", default=None); ap.add_argument("--out", required=True)
ap.add_argument("--guards", default="0.8:0.2,0.9:0.2", help="tau:margin pairs of the library-priority guard, applied over the learned list (guard) and over the fixed rule (fguard)")
a = ap.parse_args()
GUARDS = [(float(p.split(":")[0]), float(p.split(":")[1])) for p in a.guards.split(",") if p]
F = pd.read_parquet(f"{a.run}/b1_features_{a.set}.parquet"); F["molecule"] = F.molecule.astype(str)
M = pd.read_csv(f"{a.run}/b1_molecules_{a.set}.csv"); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
gl, glm, _ = runner(a.run, a.set, "gl"); ice, icm, _ = runner(a.run, a.set, "ice"); gl = gl or {}; ice = ice or {}
booster = lgb.Booster(model_file=a.model); feats = booster.feature_name()
label = a.label or f"{os.path.basename(a.run)}/{a.set}/{os.path.basename(os.path.dirname(a.model))}"
md = [f"# learned-fusion probe: {label} (w_ice {a.w_ice}; {len(feats)} features)", ""]
NREF_BINS = [(0, 0), (1, 5), (6, 20), (21, 100), (101, 10**9)]
ABL = {"no_ref (lib_sim/same/nref/in_train=0)": dict(lib=True, cnt=True), "no_counts (lib_nref/in_train=0)": dict(cnt=True), "no_sim (lib_sim/same=0)": dict(lib=True),
       "no_prior (pop/lsid/lpmid/lsynonyms=0)": dict(prior=True)}


def rank_of(sc, t):
    order = np.argsort(-np.asarray(sc, float), kind="stable"); return int(np.flatnonzero(order == t)[0]) + 1


def rr(r): return 1.0 / r if r <= 25 else 0.0


for view in a.views:
    rows, lost_contrib, lost_feats = [], [], []
    for mid in M.index:
        if view == "c1" and "c1_usable" in M.columns and not bool(M.loc[mid, "c1_usable"]): continue
        g = view_frame(F, M, mid, view)
        if not len(g) or not g.is_truth.any(): rows.append(dict(molecule=mid, reachable=False)); continue
        t = int(np.flatnonzero(g.is_truth.values)[0])
        fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{view}"].values.astype(float)
        glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
        icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
        S = zlist(fp) + 2 * term(glv) + a.w_ice * term(icv) + 0.5 * pop
        gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
        base = dict(lsid=g.lsid.values.astype(float), lpmid=g.lpmid.values.astype(float), lsyn=g.lsynonyms.values.astype(float), same=g[f"lib_same_{view}"].values.astype(float),
                    nref=g[f"lib_nref_{view}"].values.astype(float), intrain=g[f"in_train_{view}"].values.astype(float))

        def X_of(**over):
            v = dict(base); v.update(over); lib_ = v.get("lib", lib); pop_ = v.get("pop", pop)
            return feature_matrix(fp, glv, icv, pop_, v["lsid"], v["lpmid"], v["lsyn"], g["np"].values, g.src_mask.values, g.lotus_refs.values, lib_, v["same"], v["nref"],
                                  g.in_tier.values, v["intrain"], g.in_coconut.values, g.ppm_err.values, g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]),
                                  n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=feats)
        X = X_of(); pred = booster.predict(X); top1 = int(np.argsort(-pred, kind="stable")[0])
        rec = dict(molecule=mid, reachable=True, n=len(g), gl_ok=bool(gl_ok), r_learned=rank_of(pred, t), r_fixed=rank_of(S, t), r_lib=rank_of(lib + 1e-6 * zlist(fp), t),   # lib tie-break by FP as in b1_evaluate
                   t_lib_sim=lib[t], t_lib_nref=base["nref"][t], t_in_train=base["intrain"][t], t_pop=pop[t], lib_max=lib.max(), top1_is_truth=(top1 == t),
                   top1_lib_sim=lib[top1], top1_lib_nref=base["nref"][top1], top1_in_train=base["intrain"][top1], top1_pop=pop[top1])
        zeros = np.zeros(len(g))
        for name, spec in ABL.items():
            kw = {}
            if spec.get("lib"): kw.update(lib=zeros, same=zeros)
            if spec.get("cnt"): kw.update(nref=zeros, intrain=zeros)
            if spec.get("prior"): kw.update(pop=zeros, lsid=zeros, lpmid=zeros, lsyn=zeros)
            rec[f"r_{name}"] = rank_of(booster.predict(X_of(**kw)), t)
        top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
        for tau, mg in GUARDS:
            fire = lib.max() >= tau and lib.max() - second >= mg
            rec[f"r_guard{tau}_{mg}"] = rank_of(np.where(lib >= tau, 100.0 + lib, pred) if fire else pred, t)       # library priority over the LEARNED list
            rec[f"r_fguard{tau}_{mg}"] = rank_of(np.where(lib >= tau, 100.0 + lib, S) if fire else S, t)           # library priority over the FIXED rule (= insurance)
            # switch rule (Codex 012 (c)): one submission function -- GL cover short or library priority fires -> insurance list; otherwise learned
            rec[f"r_switch{tau}_{mg}"] = rec[f"r_fguard{tau}_{mg}"] if (fire or not gl_ok) else rec["r_learned"]
        ins = np.where(lib >= 0.9, 100.0 + lib, S) if (lib.max() >= 0.9 and lib.max() - second >= 0.2) else S
        rec["r_pipeline"] = rec["r_learned"] if gl_ok else rank_of(ins, t)
        rows.append(rec)
        if rec["r_fixed"] == 1 and rec["r_learned"] > 1:
            C = booster.predict(X, pred_contrib=True); lost_contrib.append(C[t, :-1] - C[top1, :-1]); lost_feats.append((X[t], X[top1]))
    R = pd.DataFrame(rows); V = R[R.reachable == True].copy(); nall = len(R)
    for c in [c for c in V.columns if c.startswith("r_")]: V[c.replace("r_", "rr_", 1)] = V[c].map(rr)
    md += [f"## view {view}: {nall} molecules, truth in shortlist {len(V)} (strict MRR over {nall}; GL fallback molecules {int((~V.gl_ok.astype(bool)).sum())})", "",
           "| ranking | MRR (strict) | top-1 |", "|---|---:|---:|"]
    for c in ["rr_learned", "rr_pipeline", "rr_fixed", "rr_lib"] + [f"rr_{k}{tau}_{mg}" for k in ("guard", "fguard", "switch") for tau, mg in GUARDS] + [f"rr_{k}" for k in ABL]:
        md.append(f"| {c[3:]} | {V[c].sum() / nall:.3f} | {(V[c] == 1).sum() / nall:.3f} |")
    md.append("")
    ins_col = f"rr_fguard{GUARDS[0][0]}_{GUARDS[0][1]}"; sw_col = f"rr_switch{GUARDS[0][0]}_{GUARDS[0][1]}"
    md += [f"| truth lib_nref bin | n | learned MRR | fixed MRR | insurance {ins_col[9:]} | switch {sw_col[9:]} | lib-only MRR | truth in_train share |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for lo, hi in NREF_BINS:
        m = (V.t_lib_nref >= lo) & (V.t_lib_nref <= hi); hs = "inf" if hi >= 10**9 else str(hi)
        if m.sum(): md.append(f"| [{lo},{hs}] | {int(m.sum())} | {V.loc[m, 'rr_learned'].mean():.3f} | {V.loc[m, 'rr_fixed'].mean():.3f} | {V.loc[m, ins_col].mean():.3f} | {V.loc[m, sw_col].mean():.3f} | {V.loc[m, 'rr_lib'].mean():.3f} | {V.loc[m, 't_in_train'].mean():.2f} |")
    md.append("")
    md += ["| truth lib_sim bin | n | learned MRR | fixed MRR | lib-only MRR |", "|---|---:|---:|---:|---:|"]
    for lo, hi in [(0, 0.6), (0.6, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 1.01)]:
        m = (V.t_lib_sim >= lo) & (V.t_lib_sim < hi)
        if m.sum(): md.append(f"| [{lo:.2f},{min(hi, 1):.2f}) | {int(m.sum())} | {V.loc[m, 'rr_learned'].mean():.3f} | {V.loc[m, 'rr_fixed'].mean():.3f} | {V.loc[m, 'rr_lib'].mean():.3f} |")
    md.append("")
    lost = V[(V.r_fixed == 1) & (V.r_learned > 1)]; won = V[(V.r_learned == 1) & (V.r_fixed > 1)]
    md += [f"learned loses (fixed top-1, learned not): {len(lost)}; learned wins (learned top-1, fixed not): {len(won)}", ""]
    if len(lost):
        md += [f"lost molecules: learned top-1 has in_train {lost.top1_in_train.mean():.2f} / lib_nref mean {lost.top1_lib_nref.mean():.1f} / lib_sim mean {lost.top1_lib_sim.mean():.3f} / pop mean {lost.top1_pop.mean():.2f}; "
               f"truth has in_train {lost.t_in_train.mean():.2f} / lib_nref mean {lost.t_lib_nref.mean():.1f} / lib_sim mean {lost.t_lib_sim.mean():.3f} / pop mean {lost.t_pop.mean():.2f}", ""]
        C = np.array(lost_contrib); Xt = np.array([x[0] for x in lost_feats]); Xo = np.array([x[1] for x in lost_feats])
        order = np.argsort(C.mean(0))
        md += ["| feature | mean contribution (truth - learned top-1) | truth mean | top-1 mean |", "|---|---:|---:|---:|"]
        md += [f"| {feats[i]} | {C.mean(0)[i]:+.3f} | {Xt[:, i].mean():.3f} | {Xo[:, i].mean():.3f} |" for i in list(order[:8]) + list(order[-4:])]
        md.append("")
    R.to_csv(a.out.replace(".md", f"_{view}.csv"), index=False)
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); print("\n".join(md))
