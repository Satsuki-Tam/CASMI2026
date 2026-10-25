"""Failure analysis of the registered main output (blend21 + GL-cover fallback) on one view of a frozen feature table: for every molecule
whose truth is not ranked first, which candidates sit above it (training structure / COCONUT-only / PubChem-tier-only), how their
library similarity, FP, GLACIER and prior compare with the truth's, and whether the library priority or the GL fallback was in play.
Scores are recomputed with the registered evaluator's formulas and checked against its own top-25 (scores_for) for every molecule.
Usage: python -X utf8 panel_c1_failures.py --run run_rk_panel --set P_np250 --model rank_v4b/lambdarank.txt --view c1 --out diag/fail_rk_old_c1
"""
import argparse, os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z, term
from b1_rankfeats import feature_matrix
import lightgbm as lgb

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--set", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--view", default="c1"); ap.add_argument("--eval_csv", default="panel_np250/p1_molecules.csv"); ap.add_argument("--out", required=True)
ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--min_gl_cover", type=float, default=0.5)
a = ap.parse_args(); v = a.view
bst = lgb.Booster(model_file=a.model); c = dict(w_ice=0.0, booster=bst, feats=bst.feature_name())
F = pd.read_parquet(f"{a.run}/b1_features_{a.set}.parquet"); F["molecule"] = F["molecule"].astype(str)
M = pd.read_csv(f"{a.run}/b1_molecules_{a.set}.csv").set_index("molecule"); M.index = M.index.astype(str)
gl, _, _ = E.runner(a.run, a.set, "gl"); gl = gl or {}
ev = pd.read_csv(a.eval_csv); ledger = ev[ev.set == a.set].molecule.astype(str).tolist()
if v == "c1": ledger = [m for m in ledger if m in M.index and bool(M.loc[m, "c1_usable"])]
rows, mism = [], 0
for mid in ledger:
    g = E.view_frame(F, M, mid, v)
    if len(g) == 0 or mid not in M.index: rows.append(dict(molecule=mid, truth_rank=np.nan, status="no candidates")); continue
    fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{v}"].values.astype(float)
    glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
    zfp = z(fp); zgl = term(glv, True); S = zfp + (2 * zgl if zgl is not None else 0) + 0.5 * pop
    top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
    fire = bool(lib.max() >= a.tau and lib.max() - second >= a.margin); ins = np.where(lib >= a.tau, 100.0 + lib, S) if fire else S
    gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
    if gl_ok:
        X = feature_matrix(fp, glv, np.full(len(g), np.nan), pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                           g[f"lib_same_{v}"].values, g[f"lib_nref_{v}"].values, g.in_tier.values, g[f"in_train_{v}"].values, g.in_coconut.values, g.ppm_err.values, g.fp_rank_window.values,
                           float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=c["feats"])
        main = bst.predict(X); score = 2 * z(np.asarray(main, float)) + z(np.asarray(S, float))
    else: main = ins; score = ins
    order = np.argsort(-np.asarray(score, float), kind="stable")
    ref, _ = E.scores_for(v, g, mid, gl, {}, True, False, c, M, a.tau, a.margin, a.min_gl_cover)
    if [str(g.smiles.values[i]) for i in order[:25]] != ref["blend21"]: mism += 1
    tr = np.flatnonzero(g.is_truth.values.astype(bool))
    if len(tr) == 0: rows.append(dict(molecule=mid, truth_rank=np.nan, status="truth not in shortlist")); continue
    pos = {int(i): k for k, i in enumerate(order)}; t = min(tr, key=lambda i: pos[int(i)]); rk = pos[int(t)] + 1
    grp = np.where(g[f"in_train_{v}"].values.astype(bool), "train", np.where(g.in_coconut.values.astype(bool), "coconut_only", "pc_only"))
    above = order[:rk - 1]; d = int(order[0]) if rk > 1 else None
    zf = zfp; zg = zgl if zgl is not None else np.full(len(g), np.nan)
    rows.append(dict(molecule=mid, status="ok", truth_rank=rk, rr=(1.0 / rk if rk <= 25 else 0.0), gl_cover_ok=bool(gl_ok), libpri_fired=fire, truth_group=grp[t],
                     truth_lib=lib[t], truth_zfp=zf[t], truth_zgl=zg[t], truth_pop=pop[t], mol_lib_max=float(lib.max()),
                     n_above=len(above), above_train=int((grp[above] == "train").sum()), above_coconut=int((grp[above] == "coconut_only").sum()), above_pc=int((grp[above] == "pc_only").sum()),
                     top_group=(grp[d] if d is not None else ""), top_lib=(lib[d] if d is not None else np.nan), top_zfp=(zf[d] if d is not None else np.nan),
                     top_zgl=(zg[d] if d is not None else np.nan), top_pop=(pop[d] if d is not None else np.nan), top_lib_gt_truth=(bool(lib[d] > lib[t]) if d is not None else False)))
R = pd.DataFrame(rows); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); R.to_csv(a.out + ".csv", index=False)
ok = R[R.status == "ok"]; miss = ok[ok.truth_rank > 1]
L = [f"# {a.view.upper()} failures: {a.run} / {a.set} / {a.model} (blend21 + GL fallback)", "",
     f"molecules {len(R)} | scored {len(ok)} | MRR {ok.rr.sum() / len(R):.4f} | truth rank 1: {int((ok.truth_rank == 1).sum())} | rank 2-25: {int(((ok.truth_rank > 1) & (ok.truth_rank <= 25)).sum())} | >25: {int((ok.truth_rank > 25).sum())} | "
     f"no truth in shortlist: {int((R.status != 'ok').sum())} | parity mismatches vs evaluator top-25: {mism}", "",
     "| top decoy group | n molecules | lost RR | decoy lib > truth lib | libpri fired | GL fallback | median truth lib | median decoy lib |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
for gname, gg in miss.groupby("top_group"):
    L.append(f"| {gname} | {len(gg)} | {float((1 - gg.rr).sum()):.2f} | {int(gg.top_lib_gt_truth.sum())} | {int(gg.libpri_fired.sum())} | {int((gg.gl_cover_ok.astype(str) == "False").sum())} | {gg.truth_lib.median():.3f} | {gg.top_lib.median():.3f} |")
L += ["", "| truth library similarity | n | MRR | rank 1 share | molecules with a train decoy on top |", "|---|---:|---:|---:|---:|"]
for lo, hi in ((0, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)):
    s = ok[(ok.truth_lib >= lo) & (ok.truth_lib < hi)]
    if len(s): L.append(f"| [{lo}, {min(hi, 1.0)}) | {len(s)} | {s.rr.mean():.3f} | {(s.truth_rank == 1).mean():.2f} | {int((s.top_group == 'train').sum())} |")
open(a.out + ".md", "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))
