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
ap.add_argument("--analog", default="", help="analog_probe.py parquet: adds the analog-channel variants ana_only / anaw<w> / anamt<w> (2026-10-26)")
ap.add_argument("--lam", type=float, default=0.5, help="prior weight in the fixed rule S (default 0.5 = registered; 2026-10-26 prior-bias check)")
ap.add_argument("--frag", default="", help="frag_probe.py parquet: adds frg_<w> / v7f_<w> / v7ffb_<w> (038)")
ap.add_argument("--analog_view_c2", default="c2", help="analog parquet view used for the c2 view (c2x = the same-library sensitivity)")
ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--min_gl_cover", type=float, default=0.5)
a = ap.parse_args()
bst = lgb.Booster(model_file=a.model); c = dict(w_ice=a.w_ice, booster=bst, feats=bst.feature_name())
from b1_rankfeats import EXTRA_ANA
ANA_MODEL = any(f_ in EXTRA_ANA for f_ in c["feats"])
ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev["molecule"].astype(str)
rows, mism = [], 0
ANA = None
if a.analog:
    ANA = pd.read_parquet(a.analog); ANA["molecule"] = ANA["molecule"].astype(str)
    ANA = {k: g.set_index("smiles") for k, g in ANA.groupby(["set", "view", "molecule"])}
ANA_W = (0.25, 0.5, 1.0, 2.0)
FRG = None
if a.frag:
    FRG = pd.read_parquet(a.frag); FRG["molecule"] = FRG["molecule"].astype(str)
    FRG = {k: dict(zip(g.smiles.astype(str), g.frag.astype(float))) for k, g in FRG.groupby(["set", "view", "molecule"])}
FRG_W = (0.25, 0.5, 1.0)
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
            S = z(fp) + (2 * zgl if zgl is not None else 0) + (a.w_ice * zice if zice is not None else 0) + a.lam * pop
            top = np.sort(lib)[::-1]; second = top[1] if len(top) > 1 else 0.0
            fire = bool(lib.max() >= a.tau and lib.max() - second >= a.margin); ins = np.where(lib >= a.tau, 100.0 + lib, S) if fire else S
            gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
            anaf = {}
            if ANA is not None:
                h = ANA.get((s, a.analog_view_c2 if v == "c2" else v, mid))
                for c_ in ("ap", "mean_tan", "ap_x", "mean_tan_x", "ap_ls", "ap_lsmax"):
                    x_ = np.array([float(h[c_].get(sm, 0.0)) if (h is not None and c_ in h.columns) else 0.0 for sm in g.smiles.astype(str)]); anaf[c_] = x_
            if gl_ok:
                X = feature_matrix(fp, glv, icv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,
                                   g[f"lib_same_{v}"].values, g[f"lib_nref_{v}"].values, g.in_tier.values, g[f"in_train_{v}"].values, g.in_coconut.values, g.ppm_err.values,
                                   g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats=c["feats"],
                                   analog=(dict(ap=anaf["ap"], mean_tan=anaf["mean_tan"]) if anaf else None),
                                   frag=(np.array([float(FRG.get((s, v, mid), {}).get(sm, 0.0)) for sm in g.smiles.astype(str)]) if FRG is not None else None))
                score = 2 * z(np.asarray(bst.predict(X), float)) + z(np.asarray(S, float))
            else: score = ins
            order = np.argsort(-np.asarray(score, float), kind="stable")
            if not ANA_MODEL and a.lam == 0.5:   # registered-evaluator parity of the main list (models with the analog block are checked by b1_parity instead)
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
            lib_ = np.nan_to_num(lib, nan=0.0); tw = int(np.argmax(lib_)) if (lib_ > 0).any() else -1   # twin = best library match of the view (2026-10-26)
            def twin_first(tau):   # the twin moved to rank 1 when its similarity >= tau, the main order otherwise / below it
                return order if (tw < 0 or lib_[tw] < tau) else [tw] + [i for i in order if i != tw]
            lib_2nd = float(np.max(np.delete(lib_, tw))) if (tw >= 0 and len(lib_) > 1) else 0.0
            pos_ = {int(i): k for k, i in enumerate(order)}
            def twin_gate(tau, m=0.0, k=None):   # + margin to the best other candidate's library match, + the twin already in the main top-k
                if tw < 0 or lib_[tw] < tau or lib_[tw] - lib_2nd < m or (k is not None and pos_[tw] >= k): return order
                return [tw] + [i for i in order if i != tw]
            def anag(wc, wu):   # GL-coverage-gated weight (034, 11:08): wc on the learned path, wu on the fallback path
                return anav("ap", wc if gl_ok else wu)
            def anav(col, w):   # registered score + w * z(analog feature) within the molecule
                x_ = anaf[col]; zx = (x_ - x_.mean()) / (x_.std() + 1e-9)
                return np.argsort(-(np.asarray(score, float) + w * zx), kind="stable")
            def tdem(theta, w, base_w=0.0):   # 037: demote train candidates without library support (+ optional analog term base_w)
                pen = (trn & (lib_ <= theta)).astype(float)
                sc_ = np.asarray(score, float) - w * pen
                if base_w and anaf: x_ = anaf["ap"]; sc_ = sc_ + base_w * (x_ - x_.mean()) / (x_.std() + 1e-9)
                return np.argsort(-sc_, kind="stable")
            fragf = None
            if FRG is not None:
                hf = FRG.get((s, v, mid), {}); fragf = np.array([float(hf.get(sm, 0.0)) for sm in g.smiles.astype(str)])
            def combo(wa_c, wa_u, wf_c, wf_u):   # 038: analog (covered / fallback) and frag (covered / fallback) weights on the registered score
                sc_ = np.asarray(score, float).copy()
                if anaf:
                    x_ = anaf["ap"]; sc_ = sc_ + (wa_c if gl_ok else wa_u) * (x_ - x_.mean()) / (x_.std() + 1e-9)
                if fragf is not None:
                    sc_ = sc_ + (wf_c if gl_ok else wf_u) * (fragf - fragf.mean()) / (fragf.std() + 1e-9)
                return np.argsort(-sc_, kind="stable")
            def libw(w):   # soft variant: the registered score + w * library similarity (z units per unit similarity)
                return np.argsort(-(np.asarray(score, float) + w * lib_), kind="stable")
            def hedge(base_order, alt, k):   # tail hedge (2026-10-26): main top-(25-k), then the best k by an alternative score among the remaining candidates
                head = list(base_order[:25 - k]); hs = set(head)
                rest = [i for i in np.argsort(-np.asarray(alt, float), kind="stable") if i not in hs]
                return head + rest[:k]
            rows.append(dict(base, truth_group=tgroup, n_cand=len(g), gl_cover_ok=bool(gl_ok), main=rr(order), insurance=rr(ins_order), pool=rr(order, trn | coco), pc=rr(order, ~(trn | coco)),
                             train=rr(order, trn), coconut_only=rr(order, coco & ~trn), nontrain=rr(order, ~trn),
                             **{f"pcd{w:g}": rr(np.argsort(-(np.asarray(score, float) - w * (~(trn | coco)).astype(float)), kind="stable")) for w in (0.5, 1.0, 2.0, 4.0)},
                             **{f"tail{k}_{nm}": rr(hedge(order, alt, k)) for k in (3, 5) for nm, alt in (("fp", fp), ("pop", pop), ("gl", np.nan_to_num(glv, nan=-1e9)), ("lib", lib), ("poolfp", np.where(trn | coco, np.nan_to_num(fp, nan=-1e9), -1e18)))},
                             twin_only=(1.0 if tw >= 0 and tr[tw] else 0.0), twin_sim=(float(lib_[tw]) if tw >= 0 else 0.0),
                             **{f"twin1_t{t:g}": rr(twin_first(t)) for t in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9)},
                             **{f"twin1m_t{t:g}_m{m:g}": rr(twin_gate(t, m=m)) for t in (0.5, 0.6, 0.7, 0.8) for m in (0.05, 0.1)},
                             **{f"twin1k_t{t:g}_k{k}": rr(twin_gate(t, k=k)) for t in (0.5, 0.6, 0.7, 0.8) for k in (3, 10)},
                             **{f"libw{w:g}": rr(libw(w)) for w in (1.0, 2.0, 4.0)},
                             **({f"frg_{w:g}": rr(combo(0, 0, w, w)) for w in FRG_W} if fragf is not None else {}),
                             **({f"v7f_{w:g}": rr(combo(0, 1, w, w)) for w in FRG_W} if fragf is not None else {}),
                             **({f"v7ffb_{w:g}": rr(combo(0, 1, 0, w)) for w in FRG_W} if fragf is not None else {}),
                             **{f"tdem{t:g}_{w:g}": rr(tdem(t, w)) for t in (0.3, 0.5) for w in (0.5, 1.0, 2.0)},
                             **({f"anatdem{t:g}_{w:g}": rr(tdem(t, w, 0.5)) for t in (0.3, 0.5) for w in (0.5, 1.0, 2.0)} if anaf else {}),
                             **({"ana_only": rr(np.lexsort((np.argsort(order), -anaf["ap"])))} if anaf else {}),
                             **({f"anaw{w:g}": rr(anav("ap", w)) for w in ANA_W} if anaf else {}),
                             **({f"anag{wc:g}_{wu:g}": rr(anag(wc, wu)) for wc, wu in ((0.5, 1.0), (0.5, 2.0), (0.25, 1.0), (0.25, 2.0), (0.0, 0.5), (0.0, 1.0))} if anaf else {}),
                             **({f"anamt{w:g}": rr(anav("mean_tan", w)) for w in ANA_W} if anaf else {}),
                             **({f"anaxw{w:g}": rr(anav("ap_x", w)) for w in ANA_W} if anaf and "ap_x" in next(iter(ANA.values())).columns else {}),
                             **({f"anamtx{w:g}": rr(anav("mean_tan_x", w)) for w in ANA_W} if anaf and "mean_tan_x" in next(iter(ANA.values())).columns else {}),
                             **({f"lsw{w:g}": rr(anav("ap_ls", w)) for w in (0.5, 1.0)} if anaf and "ap_ls" in next(iter(ANA.values())).columns else {}),
                             **({f"lsmw{w:g}": rr(anav("ap_lsmax", w)) for w in (0.5, 1.0)} if anaf and "ap_lsmax" in next(iter(ANA.values())).columns else {}), twin_rank=(pos_[tw] + 1 if tw >= 0 else 0), lib_2nd=lib_2nd,
                             truth_rank=(int(np.flatnonzero(tr[order])[0]) + 1 if tr.any() else 0)))
R = pd.DataFrame(rows); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); R.to_csv(a.out + ".csv", index=False)
cols = ["main", "insurance", "pool", "pc", "train", "coconut_only", "nontrain", "twin_only"] + [f"twin1_t{t:g}" for t in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9)] + [f"twin1m_t{t:g}_m{m:g}" for t in (0.5, 0.6, 0.7, 0.8) for m in (0.05, 0.1)] + [f"twin1k_t{t:g}_k{k}" for t in (0.5, 0.6, 0.7, 0.8) for k in (3, 10)] + [f"libw{w:g}" for w in (1.0, 2.0, 4.0)] + [f"tdem{t:g}_{w:g}" for t in (0.3, 0.5) for w in (0.5, 1.0, 2.0)] + ([f"{p_}_{w:g}" for p_ in ("frg", "v7f", "v7ffb") for w in (0.25, 0.5, 1.0)] if a.frag else []) + ([f"anatdem{t:g}_{w:g}" for t in (0.3, 0.5) for w in (0.5, 1.0, 2.0)] if a.analog else []) + (["ana_only"] + [f"anaw{w:g}" for w in ANA_W] + [f"anag{wc:g}_{wu:g}" for wc, wu in ((0.5, 1.0), (0.5, 2.0), (0.25, 1.0), (0.25, 2.0), (0.0, 0.5), (0.0, 1.0))] + [f"anamt{w:g}" for w in ANA_W] + [f"anaxw{w:g}" for w in ANA_W] + [f"anamtx{w:g}" for w in ANA_W] + ["lsw0.5", "lsw1", "lsmw0.5", "lsmw1"] if a.analog else []) + ["pcd0.5", "pcd1", "pcd2", "pcd4"] + [f"tail{k}_{n}" for k in (3, 5) for n in ("fp", "pop", "gl", "lib", "poolfp")]
cols = [c_ for c_ in cols if c_ in R.columns]   # variants absent from this run's inputs are skipped
summ = R.fillna({k: 0.0 for k in cols}).groupby(["set", "view", "truth_group"])[cols].agg(["mean"]).round(4); summ.columns = cols
summ["n"] = R.groupby(["set", "view", "truth_group"]).size()
print(f"parity mismatches vs evaluator top-25: {mism} of {int((R.n_cand > 0).sum())}"); print(summ.to_string())
open(a.out + ".md", "w", encoding="utf-8").write(f"# group filters ({a.run}, {a.model})\n\nparity mismatches vs evaluator top-25: {mism}\n\n```\n" + summ.to_string() + "\n```\n")
