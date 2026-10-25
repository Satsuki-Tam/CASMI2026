"""Per-molecule RR of the registered main output and of its candidate-group filters (the Public probe definitions), on frozen tables.

For each molecule of a set/view: blend21 (+ GL-cover fallback; recomputed with the registered evaluator's formulas and checked against its
own top-25), insurance, and the FULL-order filters of blend21 used by the probe kernels: pool (training structure of the view or COCONUT),
pc (neither), train (training structure of the view), coconut_only, nontrain; an empty filtered list scores 0 (the kernels write CCO).
Also records the truth's group (train / coconut_only / pc / absent) so that mixtures of strata can be matched to Public observations.
Usage: python -X utf8 group_filter_eval.py --run run_v3_panel --set P_np250 --model rank_v4b/lambdarank.txt --eval_csv panel_np250/p1_molecules.csv --out diag/gf_<name>
"""
import argparse, os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b1_locked_eval as E
from b1_evaluate import z, term
from b1_rankfeats import feature_matrix
import lightgbm as lgb

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--eval_csv", required=True); ap.add_argument("--out", required=True); ap.add_argument("--w_ice", type=float, default=0.0)
ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--min_gl_cover", type=float, default=0.5)
a = ap.parse_args()
bst = lgb.Booster(model_file=a.model); c = dict(w_ice=a.w_ice, booster=bst, feats=bst.feature_name())
ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev["molecule"].astype(str)
rows, mism = [], 0
for s in a.sets:
    F = pd.read_parquet(f"{a.run}/b1_features_{s}.parquet"); F["molecule"] = F["molecule"].astype(str)
    M = pd.read_csv(f"{a.run}/b1_molecules_{s}.csv").set_index("molecule"); M.index = M.index.astype(str)
    gl, _, _ = E.runner(a.run, s, "gl"); gl = gl or {}
    ice = {}
    if a.w_ice > 0: ice, _, _ = E.runner(a.run, s, "ice"); ice = ice or {}
    for v in ("c1", "c2"):
        ledger = ev[ev.set == s].molecule.tolist()
        if v == "c1": ledger = [m for m in ledger if m in M.index and bool(M.loc[m, "c1_usable"])]
        for mid in ledger:
            g = E.view_frame(F, M, mid, v) if mid in M.index else pd.DataFrame()
            base = dict(set=s, view=v, molecule=mid)
            if len(g) == 0: rows.append(dict(base, truth_group="absent", n_cand=0)); continue
            fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib = g[f"lib_sim_{v}"].values.astype(float)
            glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            icv = np.array([np.nan if (ice.get(mid) or {}).get(sm) is None else float((ice.get(mid) or {}).get(sm)) for sm in g.smiles], float)
            zgl = term(glv, True); zice = term(icv, bool(ice) and a.w_ice > 0)
            S = z(fp) + (2 * zgl if zgl is not None else 0) + (a.w_ice * zice if zice is not None else 0) + 0.5 * pop
            top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
            fire = bool(lib.max() >= a.tau and lib.max() - second >= a.margin); ins = np.where(lib >= a.tau, 100.0 + lib, S) if fire else S
            gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
            if gl_ok:
                X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                   g[f"lib_same_{v}"].values, g[f"lib_nref_{v}"].values, g.in_tier.values, g[f"in_train_{v}"].values, g.in_coconut.values, g.ppm_err.values,
                                   g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=c["feats"])
                score = 2 * z(np.asarray(bst.predict(X), float)) + z(np.asarray(S, float))
            else: score = ins
            order = np.argsort(-np.asarray(score, float), kind="stable")
            ref, _ = E.scores_for(v, g, mid, gl, ice, True, bool(ice) and a.w_ice > 0, c, M, a.tau, a.margin, a.min_gl_cover)
            if [str(g.smiles.values[i]) for i in order[:25]] != ref["blend21"]: mism += 1
            tr = g.is_truth.values.astype(bool); trn = g[f"in_train_{v}"].values.astype(bool); coco = g.in_coconut.values.astype(bool)
            grp = np.where(trn, "train", np.where(coco, "coconut_only", "pc"))
            tgroup = grp[np.flatnonzero(tr)[0]] if tr.any() else "absent"
            def rr(sc_order, keep=None):
                o = [i for i in sc_order if keep is None or keep[i]][:25]
                for k, i in enumerate(o):
                    if tr[i]: return 1.0 / (k + 1)
                return 0.0
            ins_order = np.argsort(-np.asarray(ins, float), kind="stable")
            def hedge(base_order, alt, k):   # tail hedge (2026-10-26): main top-(25-k), then the best k by an alternative score among the remaining candidates
                head = list(base_order[:25 - k]); hs = set(head)
                rest = [i for i in np.argsort(-np.asarray(alt, float), kind="stable") if i not in hs]
                return head + rest[:k]
            rows.append(dict(base, truth_group=tgroup, n_cand=len(g), gl_cover_ok=bool(gl_ok), main=rr(order), insurance=rr(ins_order), pool=rr(order, trn | coco), pc=rr(order, ~(trn | coco)),
                             train=rr(order, trn), coconut_only=rr(order, coco & ~trn), nontrain=rr(order, ~trn),
                             **{f"pcd{w:g}": rr(np.argsort(-(np.asarray(score, float) - w * (~(trn | coco)).astype(float)), kind="stable")) for w in (0.5, 1.0, 2.0, 4.0)},
                             **{f"tail{k}_{nm}": rr(hedge(order, alt, k)) for k in (3, 5) for nm, alt in (("fp", fp), ("pop", pop), ("gl", np.nan_to_num(glv, nan=-1e9)), ("lib", lib), ("poolfp", np.where(trn | coco, np.nan_to_num(fp, nan=-1e9), -1e18)))},
                             truth_rank=(int(np.flatnonzero(tr[order])[0]) + 1 if tr.any() else 0)))
R = pd.DataFrame(rows); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); R.to_csv(a.out + ".csv", index=False)
cols = ["main", "insurance", "pool", "pc", "train", "coconut_only", "nontrain", "pcd0.5", "pcd1", "pcd2", "pcd4"] + [f"tail{k}_{n}" for k in (3, 5) for n in ("fp", "pop", "gl", "lib", "poolfp")]
summ = R.fillna({k: 0.0 for k in cols}).groupby(["set", "view", "truth_group"])[cols].agg(["mean"]).round(4); summ.columns = cols
summ["n"] = R.groupby(["set", "view", "truth_group"]).size()
print(f"parity mismatches vs evaluator top-25: {mism} of {int((R.n_cand > 0).sum())}"); print(summ.to_string())
open(a.out + ".md", "w", encoding="utf-8").write(f"# group filters ({a.run}, {a.model})\n\nparity mismatches vs evaluator top-25: {mism}\n\n```\n" + summ.to_string() + "\n```\n")
