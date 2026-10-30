"""149 (149_prereg_s2_mist.md): S2 (i) one comparison of the MIST-sourced second engine M with the current E2 recipe C on a fold 3 / 4 cross-fit.
C = e2_common.FEATS from the E tables; M = the same 21 features with fp / fp_rank / fp_z / fp_gap computed from MIST mist_cos (mist_score_v4.py
via e2_mist_inputs.py) with the same formulas. Missing rules: a molecule with no finite mist_cos is "MIST-uncovered" (not in M's training
rows; at evaluation M's order := C's order); inside covered molecules a missing mist_cos -> the molecule's finite minimum - 0.05.
Models: LightGBM binary, e2_train.PARAMS, 800 rounds, rows weighted 1 / group size, groups = e2_common.train_groups; fit on one fold's three
pool dirs, applied to the other fold's v8w7a-unseen evaluation dirs (train_pool_f?b, np061_f?pool). P = v8w7a top 25 (diag/top149_<tag>).
Fusion F_X = e2_engine.fuse_rrf(P, E2_X, 0.5) (K 10). Reading = the registered gate (primary 1/2 A' + 1/2 B_D', +0.01 and lower > 0, both
directions positive, protections lower >= -0.01); membership as reader v3 (fixed table). Outputs: experiments/e2/s2_mist/ (groups csv, summary).
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/e2_s2_mist.py"""
import json, os, sys, time
import numpy as np, pandas as pd, polars as pl, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(1, os.path.join(ROOT, "experiments", "b1_baseline"))
from e2_common import FEATS, view_frame, train_groups, rank_lists
from e2_engine import fuse_rrf
from e2_train import PARAMS
S5 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]; S3 = ["NP_H", "NP_X", "NP_N"]
FOLD = {3: [("train_pool_f3a", S5), ("train_pool_f3b", S5), ("np061_f3pool", S3)], 4: [("train_pool_f4a", S5), ("train_pool_f4b", S5), ("np061_f4pool", S3)]}
EVAL = {3: [("f3b", "train_pool_f3b", S5), ("np061f3", "np061_f3pool", S3)], 4: [("f4b", "train_pool_f4b", S5), ("np061f4", "np061_f4pool", S3)]}
LEDGER = {"f3b": "run_tp_f3b", "f4b": "run_tp_f4b", "np061f3": "run_np061_f3pool", "np061f4": "run_np061_f4pool_p"}   # C1-usable ledgers of the P runs (roster as reader v3)
ROUNDS, NB, OUT = 800, 4000, os.path.join(ROOT, "experiments/e2/s2_mist")
EW, MO, B = os.path.join(ROOT, "experiments/e2/ewin"), os.path.join(ROOT, "experiments/e2/mist_out"), os.path.join(ROOT, "experiments/b1_baseline")


def stop(msg): sys.exit(f"STOP (149): {msg}")


def frames(d, s, view):
    """C frame and M frame of one set / view (same rows); M's fp columns from mist_cos; returns (Xc, Xm, covered molecule set)."""
    E = pd.read_parquet(os.path.join(EW, d, f"ewin_{s}.parquet")); F = pd.read_parquet(os.path.join(EW, d, f"e2f_{s}.parquet"))
    E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str)
    Mi = pd.read_parquet(os.path.join(MO, d, f"mist_e2_{s}.parquet"), columns=["molecule", "official_key", "mist_cos", "status"]); Mi["molecule"] = Mi.molecule.astype(str)
    if Mi.duplicated(["molecule", "official_key"]).any() or len(Mi) != len(E): stop(f"{d} {s}: MIST rows {len(Mi)} vs E rows {len(E)} or duplicates")
    Xc = view_frame(E, F, view)
    if not len(Xc): return Xc, Xc.copy(), set()
    X = Xc.merge(Mi, on=["molecule", "official_key"], how="left", validate="one_to_one")
    if X.status.isna().any(): stop(f"{d} {s} {view}: E rows without a MIST row")
    fin = X.groupby("gk").mist_cos.transform(lambda v: np.isfinite(v).any()); covered = set(X.loc[fin, "molecule"])
    Xm = X.copy(); G = lambda c: Xm.groupby("gk", sort=False)[c]
    Xm["fp"] = Xm.mist_cos.astype(float); Xm["fp"] = Xm.fp.fillna(G("fp").transform("min") - 0.05)
    Xm["fp_rank"] = G("fp").rank(ascending=False, method="min"); Xm["fp_z"] = (Xm.fp - G("fp").transform("mean")) / (G("fp").transform("std").fillna(0.0) + 1e-6)
    Xm["fp_gap"] = Xm.fp - G("fp").transform("max")
    Xm = Xm[Xm.molecule.isin(covered)].drop(columns=["mist_cos", "status"])
    return Xc, Xm, covered


def fit(fold, log):
    parts_c, parts_m, seen = [], [], set()
    for d, sets in FOLD[fold]:
        for s in sets:
            for v in ("c1", "c2"):
                Xc, Xm, cov = frames(d, s, v)
                if not len(Xc): continue
                Xc = Xc[~Xc.molecule.isin(seen)]; Xm = Xm[~Xm.molecule.isin(seen)]
                tc = train_groups(Xc) if len(Xc) else Xc; tm = train_groups(Xm) if len(Xm) else Xm
                for T_, P_ in ((tc, parts_c), (tm, parts_m)):
                    if len(T_): T_ = T_.assign(gk=f"{d}|{v}|" + T_.gk); P_.append(T_)
            seen |= set(pd.read_parquet(os.path.join(EW, d, f"ewin_{s}.parquet"), columns=["molecule"]).molecule.astype(str))
    out = {}
    for name, parts in (("C", parts_c), ("M", parts_m)):
        X = pd.concat(parts, ignore_index=True); w = (1.0 / X.groupby("gk").gk.transform("size")).values
        out[name] = lgb.train(PARAMS, lgb.Dataset(X[FEATS], X.is_truth.astype(int), weight=w), num_boost_round=ROUNDS)
        log(f"  fit fold {fold} {name}: groups {X.gk.nunique()} rows {len(X)}")
    return out


def main():
    t0 = time.time(); os.makedirs(OUT, exist_ok=True); log = lambda *x: print(*x, flush=True)
    pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"]); COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
    COCO |= set(pd.read_parquet(os.path.join(ROOT, "experiments/e2/coco_store_okeys.parquet")).official_key.dropna().astype(str))
    ESRC_X = set(pd.read_parquet(os.path.join(B, "diag/e_window_keys_v2.parquet")).key.astype(str))
    models = {3: fit(3, log), 4: fit(4, log)}; rows = []; cover = {}
    for ev_fold, mfold in ((3, 4), (4, 3)):   # evaluation fold <- models fitted on the other fold
        for tag, d, sets in EVAL[ev_fold]:
            T = pd.read_parquet(os.path.join(B, "diag", f"top149_{tag}.parquet")); T["molecule"] = T.molecule.astype(str)
            ev = pd.read_csv(os.path.join(B, d, "p2_molecules.csv")); ev["molecule"] = ev.molecule.astype(str); truth = dict(zip(ev.molecule, ev.scorer_key.astype(str)))
            for s in sets:
                for v in ("c1", "c2"):
                    Xc, Xm, cov = frames(d, s, v)
                    RC = rank_lists(Xc, models[mfold]["C"].predict(Xc[FEATS])) if len(Xc) else Xc
                    RM = rank_lists(Xm, models[mfold]["M"].predict(Xm[FEATS])) if len(Xm) else Xm
                    for R_ in (RC, RM):
                        if len(R_) and not np.isfinite(R_.score).all(): stop("non-finite prediction")
                    LC = {g: x.official_key.astype(str).tolist() for g, x in RC.groupby("molecule", sort=False)} if len(RC) else {}
                    LM = {g: x.official_key.astype(str).tolist() for g, x in RM.groupby("molecule", sort=False)} if len(RM) else {}
                    cover[(tag, s, v)] = (len(cov), Xc.molecule.nunique() if len(Xc) else 0)
                    led = pd.read_csv(os.path.join(B, LEDGER[tag], f"b1_molecules_{s}.csv")); led["molecule"] = led.molecule.astype(str); led = led.set_index("molecule")
                    roster = [x for x in ev[ev.set == s].molecule if v == "c2" or (x in led.index and bool(led.loc[x, "c1_usable"]))]
                    PL = {x: g.sort_values("rank").okey.astype(str).tolist()[:25] for x, g in T[(T.set == s) & (T.view == v)].groupby("molecule", sort=False)}
                    if set(PL) - set(roster): stop(f"{tag} {s} {v}: P groups outside the roster")
                    for x in roster:
                        p = PL.get(x, []); t = truth[x]   # no P list -> P = F = [] (kernel placeholder), E2 alone still recorded
                        ec = LC.get(x, []); em = LM.get(x, ec)   # MIST-uncovered -> M := C
                        rc = {k: i + 1 for i, k in enumerate(ec)}; rm = {k: i + 1 for i, k in enumerate(em)}
                        FC, FM = (fuse_rrf(p, rc, ec[:25], 0.5), fuse_rrf(p, rm, em[:25], 0.5)) if p else ([], [])
                        rr = lambda L: 1.0 / (L.index(t) + 1) if t in L[:25] else 0.0
                        rows.append(dict(eval_fold=ev_fold, tag=tag, set=s, view=v, molecule=x, tkey=t, covered=x in cov, p_empty=not p, t_esrc=(v == "c1") or (t in COCO) or (t in ESRC_X),
                                         P=rr(p), E2C=rr(ec), E2M=rr(em), FC=rr(FC), FM=rr(FM)))
                log(f"  eval fold {ev_fold} {tag} {s} ({time.time()-t0:.0f}s)")
    G = pd.DataFrame(rows); G.to_csv(os.path.join(OUT, "s2_mist_groups.csv"), index=False)
    cell = lambda f, tag, s, vw: G[(G.eval_fold == f) & (G.tag == tag) & (G.set == s) & (G.view == vw)]
    A = [(3, "np061f3", "NP_H"), (3, "np061f3", "NP_N"), (4, "np061f4", "NP_H"), (4, "np061f4", "NP_N")]; BD = [(3, "f3b", "D_np_single"), (4, "f4b", "D_np_single")]
    OB = [(f, t, s) for f, t in ((3, "f3b"), (4, "f4b")) for s in S5[:4]]; GC1 = [(3, "f3b", "G_tims_crosslib"), (4, "f4b", "G_tims_crosslib")]
    NPC1 = [(3, "np061f3", s) for s in S3] + [(4, "np061f4", s) for s in S3] + OB

    def boot(cells, vw, seed, ex=None, pooled=False, a="FM", b="FC"):
        rng = np.random.default_rng(seed); arrs = []
        for c in cells:
            r = cell(*c, vw); r = r[ex(r)] if ex is not None else r
            if len(r): arrs.append((r[a] - r[b]).values.astype(float))
        if pooled: arrs = [np.concatenate(arrs)] if arrs else []
        if not arrs: return float("nan"), np.array([np.nan])
        return float(np.mean([x.mean() for x in arrs])), np.array([np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in arrs]) for _ in range(NB)])
    ci = lambda bs: np.nanpercentile(bs, [2.5, 97.5]); fmt = lambda p_, bs: f"{p_:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
    pa, ba = boot(A, "c2", 149); pb, bb = boot(BD, "c2", 150); prim, bprim = 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb
    dirs = {f: 0.5 * boot([c for c in A if c[0] == f], "c2", 7)[0] + 0.5 * boot([c for c in BD if c[0] == f], "c2", 8)[0] for f in (3, 4)}
    PROT = {"old B' C2": (OB, "c2", None, False), "E-outside C2 (A' + old B')": (A + OB, "c2", lambda r: ~r.t_esrc.astype(bool), True), "G C1": (GC1, "c1", None, False), "NP C1": (NPC1, "c1", None, False)}
    pr = {k: boot(c_, vw_, 11, ex_, pool_) for k, (c_, vw_, ex_, pool_) in PROT.items()}
    gate = prim >= 0.01 and ci(bprim)[0] > 0 and all(v_ > 0 for v_ in dirs.values()) and all(ci(b_)[0] >= -0.01 for _, b_ in pr.values())
    L = [f"# 149 S2 (i) MIST (M) vs current E2 recipe (C) - registered reading ({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"- primary 1/2 A' + 1/2 B_D' (F_M - F_C, C2): **{fmt(prim, bprim)}** (A' {fmt(pa, ba)}, B_D' {fmt(pb, bb)})",
         f"- direction point estimates: fold 3 eval (4->3 models) {dirs[3]:+.4f}, fold 4 eval (3->4 models) {dirs[4]:+.4f}"]
    L += [f"- protection {k}: {fmt(*v_)}" for k, v_ in pr.items()]
    L += [f"- **gate: {'PASS' if gate else 'no'}**", "", "## Descriptive", ""]
    for lab, cells, vw in (("A' C2", A, "c2"), ("B_D' C2", BD, "c2"), ("old B' C2", OB, "c2"), ("G C1", GC1, "c1"), ("NP C1", NPC1, "c1")):
        r = pd.concat([cell(*c, vw) for c in cells]) if cells else G.iloc[:0]
        if not len(r): continue
        d_ = r.FM - r.FC
        L.append(f"- {lab}: n {len(r)}, MIST-covered {r.covered.mean():.3f} | P {r.P.mean():.4f}, E2C {r.E2C.mean():.4f}, E2M {r.E2M.mean():.4f}, FC {r.FC.mean():.4f}, FM {r.FM.mean():.4f} | "
                 f"sum(+) {d_[d_ > 0].sum():.2f}, sum(-) {d_[d_ < 0].sum():.2f} | oracle mean(max(E2C, E2M) - E2C) {np.maximum(r.E2C, r.E2M).mean() - r.E2C.mean():+.4f} | P wrong rows: FM - FC {d_[r.P < 1].mean():+.4f}")
    open(os.path.join(OUT, "s2_mist_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L)); print(f"S2_MIST_DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
