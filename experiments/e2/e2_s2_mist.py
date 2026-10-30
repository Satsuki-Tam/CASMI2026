"""149 v2 (149_prereg_s2_mist.md + amendment v2 after Codex 149): S2 (i) fixed-recipe development cross-fit comparison of the MIST-sourced second
engine M with the current E2 recipe C (and the descriptive control C_cov = C trained on M's covered groups), fold 3 <-> 4.
C = e2_common.FEATS from the E tables; M = the same 21 features with fp / fp_rank / fp_z / fp_gap computed from MIST mist_cos (mist_score_v4.py via
e2_mist_inputs.py). Missing rules: a molecule with no finite mist_cos in the view frame is MIST-uncovered (not in M's / C_cov's training rows; at
evaluation M's and C_cov's orders := C's order, checked list by list); inside covered molecules a missing mist_cos -> finite minimum - 0.05.
Models: LightGBM binary, e2_train.PARAMS, 800 rounds, rows weighted 1 / group size, groups = e2_common.train_groups; fit on one fold's three pool
dirs, applied to the other fold's v8w7a-unseen evaluation dirs. P = v8w7a top 25 (diag/top149_<tag>). F_X = e2_engine.fuse_rrf(P, E2_X, 0.5).
Every check of the amendment is a STOP: preflight (P teachers / MSG / uniqueness), MIST table validity, E ledger and P completeness (legitimate
empties only), ordered-list identities, expected cells present. Reading = the registered gate. Outputs: experiments/e2/s2_mist/ (refuses to overwrite).
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/e2_s2_mist.py"""
import hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(1, os.path.join(ROOT, "experiments", "b1_baseline"))
from e2_common import FEATS, view_frame, train_groups, rank_lists
from e2_engine import fuse_rrf
from e2_train import PARAMS
from b1_common import ADDUCT_SHIFT, select_queries
from wf_common import neutral_formula
S5 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]; S3 = ["NP_H", "NP_X", "NP_N"]
FOLD = {3: [("train_pool_f3a", S5), ("train_pool_f3b", S5), ("np061_f3pool", S3)], 4: [("train_pool_f4a", S5), ("train_pool_f4b", S5), ("np061_f4pool", S3)]}
EVAL = {3: [("f3b", "train_pool_f3b", S5), ("np061f3", "np061_f3pool", S3)], 4: [("f4b", "train_pool_f4b", S5), ("np061f4", "np061_f4pool", S3)]}
RUN = {"f3b": "run_tp_f3b", "f4b": "run_tp_f4b", "np061f3": "run_np061_f3pool", "np061f4": "run_np061_f4pool_p"}   # P runs (tables, C1 ledgers)
P_TEACH = ["experiments/p1_baseline/run1/p1_molecules.csv", "experiments/b1_baseline/eval_set/p1_molecules.csv", "experiments/b1_baseline/eval_c1/p1_molecules.csv",
           "experiments/b1_baseline/train_pool_f3a/p2_molecules.csv", "experiments/b1_baseline/train_pool_f4a/p2_molecules.csv"]
STATUS = {"ok", "no_qrows", "no_mist_adduct", "no_formula", "mass_mismatch", "no_fp"}
ROUNDS, NB, OUT = 800, 4000, os.path.join(ROOT, "experiments/e2/s2_mist")
EW, MO, B = os.path.join(ROOT, "experiments/e2/ewin"), os.path.join(ROOT, "experiments/e2/mist_out"), os.path.join(ROOT, "experiments/b1_baseline")


def stop(msg): sys.exit(f"STOP (149 v2): {msg}")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def preflight(man):
    rost = {d: pd.read_csv(os.path.join(B, d, "p2_molecules.csv")) for f in FOLD for d, _ in FOLD[f]}
    allr = pd.concat([r.assign(dir=d) for d, r in rost.items()], ignore_index=True)
    for c in ("molecule", "scorer_key", "identity_group"):
        if allr[c].astype(str).duplicated().any(): stop(f"six dirs: duplicate {c}")
    f3 = pd.concat([rost[d] for d, _ in FOLD[3]]); f4 = pd.concat([rost[d] for d, _ in FOLD[4]])
    for c in ("scorer_key", "identity_group"):
        if set(f3[c].astype(str)) & set(f4[c].astype(str)): stop(f"fold 3 / fold 4 share {c}")
    teach = pd.concat([pd.read_csv(os.path.join(ROOT, p)) for p in P_TEACH], ignore_index=True)
    ev = pd.concat([rost[d] for f in EVAL for _, d, _ in EVAL[f]], ignore_index=True)
    for c in ("scorer_key", "identity_group"):
        if c in teach.columns and set(teach[c].dropna().astype(str)) & set(ev[c].dropna().astype(str)): stop(f"evaluation roster shares {c} with P's teacher rosters")
    msg = set(open(os.path.join(ROOT, "data/external/massspecgym/msg_scorer_keys.txt")).read().split())
    nmsg = {d: int(r.scorer_key.astype(str).isin(msg).sum()) for d, r in rost.items()}
    if any(nmsg.values()): stop(f"MSG overlap {nmsg}")
    ck = set()
    for d in rost:
        m = json.load(open(os.path.join(MO, d, "mist_e2_manifest.json"))); ck.add(m["ckpt_sha256"])
        for s, v in m["sets"].items():
            if sha(os.path.join(MO, d, f"mist_e2_{s}.parquet")) != v["output_sha256"]: stop(f"MIST output {d} {s} differs from its manifest")
    if len(ck) != 1: stop(f"MIST checkpoints differ {ck}")
    man["preflight"] = dict(roster_sizes={d: len(r) for d, r in rost.items()}, msg_overlap=nmsg, msg_keys=len(msg), p_teacher_rosters=P_TEACH, p_teacher_overlap=0,
                            mist_ckpt_sha256=ck.pop(), mist_synthetic_structures_overlap="unverified (mist_msg_aug)", p_model_sha256=sha(os.path.join(B, "rank_v8w7a/lambdarank.txt")))


def mist_table(d, s, E):
    Mi = pd.read_parquet(os.path.join(MO, d, f"mist_e2_{s}.parquet")); Mi["molecule"] = Mi.molecule.astype(str); Mi["official_key"] = Mi.official_key.astype(str)
    if Mi.duplicated(["molecule", "official_key"]).any(): stop(f"{d} {s}: duplicate MIST rows")
    J = E[["molecule", "official_key", "smiles"]].merge(Mi[["molecule", "official_key", "smiles", "mist_cos", "n_q", "status"]], on=["molecule", "official_key"], how="outer", suffixes=("", "_m"), indicator=True)
    if (J._merge != "both").any(): stop(f"{d} {s}: MIST rows != E rows ({int((J._merge != 'both').sum())})")
    if (J.smiles.astype(str) != J.smiles_m.astype(str)).any(): stop(f"{d} {s}: MIST smiles differ from the E representative")
    if not J.status.isin(STATUS).all(): stop(f"{d} {s}: unknown MIST status {set(J.status) - STATUS}")
    c = J.mist_cos.astype(float); ok = J.status == "ok"
    if np.isinf(c).any(): stop(f"{d} {s}: inf mist_cos")
    if not (np.isfinite(c[ok]).all() and c[ok].between(-1, 1).all() and (J.n_q[ok] > 0).all()): stop(f"{d} {s}: ok rows without a finite cos in [-1, 1] / n_q > 0")
    if not (c[~ok].isna().all() and (J.n_q[~ok] == 0).all()): stop(f"{d} {s}: non-ok rows with a cos or n_q > 0")
    return J[["molecule", "official_key", "mist_cos", "status"]]


def frames(d, s, view):
    """C frame, M frame (covered molecules only), covered set, candidate coverage counts."""
    E = pd.read_parquet(os.path.join(EW, d, f"ewin_{s}.parquet")); F = pd.read_parquet(os.path.join(EW, d, f"e2f_{s}.parquet"))
    E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str); E["official_key"] = E.official_key.astype(str); F["official_key"] = F.official_key.astype(str)
    Mi = mist_table(d, s, E); Xc = view_frame(E, F, view)
    if not len(Xc): return Xc, Xc.copy(), set(), (0, 0)
    X = Xc.merge(Mi, on=["molecule", "official_key"], how="left", validate="one_to_one")
    if X.status.isna().any(): stop(f"{d} {s} {view}: E rows without a MIST row")
    fin = np.isfinite(X.mist_cos.astype(float)); X["fin"] = fin
    covered = set(X.loc[fin, "molecule"]); Xm = X[X.molecule.isin(covered)].copy()
    fmin = Xm.assign(c=Xm.mist_cos.where(Xm.fin)).groupby("gk").c.transform("min")
    Xm["fp"] = Xm.mist_cos.where(Xm.fin, fmin - 0.05).astype(float)
    G = lambda c: Xm.groupby("gk", sort=False)[c]
    Xm["fp_rank"] = G("fp").rank(ascending=False, method="min"); Xm["fp_z"] = (Xm.fp - G("fp").transform("mean")) / (G("fp").transform("std").fillna(0.0) + 1e-6)
    Xm["fp_gap"] = Xm.fp - G("fp").transform("max")
    if not np.isfinite(Xm[["fp", "fp_rank", "fp_z", "fp_gap"]].to_numpy(float)).all(): stop(f"{d} {s} {view}: non-finite MIST-derived features")
    return Xc, Xm.drop(columns=["mist_cos", "status", "fin"]), covered, (int(fin.sum()), len(X))


def fit(fold, log, counts):
    parts = {"C": [], "M": [], "Ccov": []}; seen = set()
    for d, sets in FOLD[fold]:
        for s in sets:
            for v in ("c1", "c2"):
                Xc, Xm, cov, cc = frames(d, s, v)
                Xc = Xc[~Xc.molecule.isin(seen)] if len(Xc) else Xc; Xm = Xm[~Xm.molecule.isin(seen)] if len(Xm) else Xm
                tc = train_groups(Xc) if len(Xc) else Xc; tm = train_groups(Xm) if len(Xm) else Xm
                tcc = tc[tc.molecule.isin(cov)] if len(tc) else tc
                for arm, T_ in (("C", tc), ("M", tm), ("Ccov", tcc)):
                    if len(T_): parts[arm].append(T_.assign(gk=f"{d}|{v}|" + T_.gk))
                counts.append(dict(fit_fold=fold, dir=d, set=s, view=v, window_groups=int(Xc.gk.nunique()) if len(Xc) else 0, covered_groups=len(cov & set(Xc.molecule)) if len(Xc) else 0,
                                   cand_covered=cc[0], cand_total=cc[1], fit_C=int(tc.gk.nunique()) if len(tc) else 0, fit_M=int(tm.gk.nunique()) if len(tm) else 0, fit_Ccov=int(tcc.gk.nunique()) if len(tcc) else 0))
            seen |= set(pd.read_parquet(os.path.join(EW, d, f"ewin_{s}.parquet"), columns=["molecule"]).molecule.astype(str))
    out = {}
    for arm, P_ in parts.items():
        X = pd.concat(P_, ignore_index=True); w = (1.0 / X.groupby("gk").gk.transform("size")).values
        out[arm] = lgb.train(PARAMS, lgb.Dataset(X[FEATS], X.is_truth.astype(int), weight=w), num_boost_round=ROUNDS)
        out[arm].save_model(os.path.join(OUT, "models", f"fit{fold}_{arm}.txt")); log(f"  fit fold {fold} {arm}: groups {X.gk.nunique()} rows {len(X)} weight {w.sum():.1f}")
    return out


def main():
    t0 = time.time(); log = lambda *x: print(*x, flush=True)
    if os.path.exists(OUT): stop(f"{OUT} exists (refusing to overwrite)")
    os.makedirs(os.path.join(OUT, "models")); man = dict(code={f: sha(os.path.join(HERE, f)) for f in ("e2_s2_mist.py", "e2_common.py", "e2_engine.py", "e2_train.py", "e2_mist_inputs.py")}, inputs={})
    preflight(man); log("preflight PASS", json.dumps(man["preflight"])[:300])
    pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"]); COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
    COCO |= set(pd.read_parquet(os.path.join(ROOT, "experiments/e2/coco_store_okeys.parquet")).official_key.dropna().astype(str))
    ESRC_X = set(pd.read_parquet(os.path.join(B, "diag/e_window_keys_v2.parquet")).key.astype(str))
    meta = pl.read_parquet(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet"), columns=["row", "inchikey14", "ingest_lib", "adduct", "ce_mean"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy().astype(float)
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    ts = pd.read_parquet(os.path.join(ROOT, "data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet"), columns=["key", "smiles"]).drop_duplicates("key")
    k2s = dict(zip(ts.key.astype(str), ts.smiles.astype(str))); _fcache = {}
    def formula(smi):
        if smi not in _fcache: _fcache[smi] = neutral_formula(smi) if smi else None
        return _fcache[smi]
    counts = []; models = {3: fit(3, log, counts), 4: fit(4, log, counts)}; pd.DataFrame(counts).to_csv(os.path.join(OUT, "fit_counts.csv"), index=False)
    rows = []
    for ev_fold, mfold in ((3, 4), (4, 3)):
        for tag, d, sets in EVAL[ev_fold]:
            tp = os.path.join(B, "diag", f"top149_{tag}.parquet"); man["inputs"][f"top149_{tag}"] = sha(tp)
            T = pd.read_parquet(tp); T["molecule"] = T.molecule.astype(str); T["okey"] = T.okey.astype(str)
            ev = pd.read_csv(os.path.join(B, d, "p2_molecules.csv")); ev["molecule"] = ev.molecule.astype(str); truth = dict(zip(ev.molecule, ev.scorer_key.astype(str))); libm = dict(zip(ev.molecule, ev.lib))
            for s in sets:
                led = pd.read_csv(os.path.join(B, RUN[tag], f"b1_molecules_{s}.csv")); led["molecule"] = led.molecule.astype(str); led = led.set_index("molecule")
                Fp = pd.read_parquet(os.path.join(B, RUN[tag], f"b1_features_{s}.parquet")); Fp["molecule"] = Fp.molecule.astype(str)
                em = pd.read_csv(os.path.join(EW, d, f"ewin_molecules_{s}.csv")); em["molecule"] = em.molecule.astype(str); em = em.set_index("molecule")
                E_all = pd.read_parquet(os.path.join(EW, d, f"ewin_{s}.parquet"), columns=["molecule", "official_key", "smiles", "is_truth"]); E_all["molecule"] = E_all.molecule.astype(str)
                ecount = E_all.groupby("molecule").size(); ESMI = dict(zip(zip(E_all.molecule, E_all.official_key.astype(str)), E_all.smiles.astype(str)))
                mols = ev[ev.set == s].molecule.tolist()
                for x in mols:   # E ledger completeness: listed with n_e = table rows, or legitimately without a query
                    if x in em.index:
                        if int(em.loc[x, "n_e"]) != int(ecount.get(x, 0)): stop(f"{tag} {s} {x}: E ledger n_e != table rows")
                    else:
                        qr = [int(r) for r in ik_rows.get(x, []) if lib_of_row[r] == libm[x] and add_of_row[r] in ADDUCT_SHIFT]
                        if select_queries(sorted(qr), 8, lambda r: add_of_row[r], lambda r: float(ce_of_row[r])): stop(f"{tag} {s} {x}: not in the E ledger although it has queries")
                for v in ("c1", "c2"):
                    if any(x not in led.index for x in mols): stop(f"{tag} {s}: selected molecules missing from the P ledger")
                    roster = [x for x in mols if v == "c2" or bool(led.loc[x, "c1_usable"])]
                    Xc, Xm, cov, cc = frames(d, s, v)
                    RC = rank_lists(Xc, models[mfold]["C"].predict(Xc[FEATS])) if len(Xc) else Xc
                    RM = rank_lists(Xm, models[mfold]["M"].predict(Xm[FEATS])) if len(Xm) else Xm
                    RK = rank_lists(Xc[Xc.molecule.isin(cov)], models[mfold]["Ccov"].predict(Xc[Xc.molecule.isin(cov)][FEATS])) if len(cov) else Xc.iloc[:0]
                    for R_ in (RC, RM, RK):
                        if len(R_) and not np.isfinite(R_.score).all(): stop("non-finite prediction")
                    L_ = lambda R_: {g: x_.official_key.astype(str).tolist() for g, x_ in R_.groupby("molecule", sort=False)} if len(R_) else {}
                    LC, LM, LK = L_(RC), L_(RM), L_(RK)
                    PL = {}
                    for x, g in T[(T.set == s) & (T.view == v)].groupby("molecule", sort=False):
                        g = g.sort_values("rank"); ks = g.okey.tolist()
                        if g["rank"].tolist() != list(range(1, len(g) + 1)) or len(set(ks)) != len(ks) or len(ks) > 25: stop(f"{tag} {s} {v} {x}: P ranks / keys")
                        PL[x] = ks
                    if set(PL) - set(roster): stop(f"{tag} {s} {v}: P groups outside the roster")
                    for x in roster:
                        if x not in PL:   # legitimate empty P only: no eligible row in the P table for this view
                            g0 = Fp[Fp.molecule == x]; keep = g0[f"in_short_{v}"].astype(bool)
                            if v == "c2": keep &= (g0.in_tier | g0.in_coconut | g0.in_train_c2).astype(bool)
                            if int((keep & g0.official_key.notna()).sum()): stop(f"{tag} {s} {v} {x}: P list missing although eligible candidates exist")
                        if ecount.get(x, 0) and x not in LC and v == "c1": stop(f"{tag} {s} {v} {x}: E rows but no E2 list")
                        p = PL.get(x, []); t = truth[x]; ec = LC.get(x, [])
                        if x in cov:
                            if x not in LM or x not in LK: stop(f"{tag} {s} {v} {x}: covered molecule without M / C_cov rows")
                            emm, ekk = LM[x], LK[x]
                        else:
                            emm, ekk = ec, ec
                        rmap = lambda el: {k: i + 1 for i, k in enumerate(el)}
                        if p:
                            if fuse_rrf(p, rmap(ec), ec[:25], 0.0) != p: stop(f"{tag} {s} {v} {x}: F0 != P (ordered)")
                            FC, FM, FK = fuse_rrf(p, rmap(ec), ec[:25], 0.5), fuse_rrf(p, rmap(emm), emm[:25], 0.5), fuse_rrf(p, rmap(ekk), ekk[:25], 0.5)
                        else:
                            FC = FM = FK = []
                        if x not in cov and not (emm == ec and FM == FC): stop(f"{tag} {s} {v} {x}: uncovered molecule but M differs from C")
                        rr = lambda L: 1.0 / (L.index(t) + 1) if t in L[:25] else 0.0
                        tsmi = ESMI.get((x, t)) or k2s.get(t); tf = formula(tsmi) if tsmi else None
                        def wf(el):   # truth's rank among the same-formula candidates of the list (descriptive)
                            if t not in el: return "absent", np.nan
                            if tf is None: return "no_formula", np.nan
                            same = [k for k in el if formula(ESMI.get((x, k))) == tf]
                            return "ok", float(same.index(t) + 1)
                        stc, wfc = wf(ec); stm, wfm = wf(emm)
                        rows.append(dict(eval_fold=ev_fold, tag=tag, set=s, view=v, molecule=x, tkey=t, covered=x in cov, p_empty=not p, t_esrc=(v == "c1") or (t in COCO) or (t in ESRC_X),
                                         P=rr(p), E2C=rr(ec), E2M=rr(emm), E2Ccov=rr(ekk), FC=rr(FC), FM=rr(FM), FCcov=rr(FK), wf_state_C=stc, wf_rank_C=wfc, wf_state_M=stm, wf_rank_M=wfm))
                    counts.append(dict(eval_tag=tag, set=s, view=v, roster=len(roster), covered=len(cov & set(roster)), cand_covered=cc[0], cand_total=cc[1], p_lists=len(PL)))
                log(f"  eval fold {ev_fold} {tag} {s} ({time.time()-t0:.0f}s)")
    G = pd.DataFrame(rows); G.to_csv(os.path.join(OUT, "s2_mist_groups.csv"), index=False); pd.DataFrame(counts).to_csv(os.path.join(OUT, "counts.csv"), index=False)
    cell = lambda f, tag, s, vw: G[(G.eval_fold == f) & (G.tag == tag) & (G.set == s) & (G.view == vw)]
    A = [(3, "np061f3", "NP_H"), (3, "np061f3", "NP_N"), (4, "np061f4", "NP_H"), (4, "np061f4", "NP_N")]; BD = [(3, "f3b", "D_np_single"), (4, "f4b", "D_np_single")]
    OB = [(f, t, s) for f, t in ((3, "f3b"), (4, "f4b")) for s in S5[:4]]; GC1 = [(3, "f3b", "G_tims_crosslib"), (4, "f4b", "G_tims_crosslib")]
    NPC1 = [(3, "np061f3", s) for s in S3] + [(4, "np061f4", s) for s in S3] + OB
    for cells, vw in ((A, "c2"), (BD, "c2"), (OB, "c2"), (GC1, "c1")):
        for c in cells:
            if not len(cell(*c, vw)): stop(f"expected cell {c} {vw} is empty")

    def boot(cells, vw, seed, ex=None, pooled=False, a="FM", b="FC"):
        rng = np.random.default_rng(seed); arrs = []
        for c in cells:
            r = cell(*c, vw); r = r[ex(r)] if ex is not None else r; arrs.append((r[a] - r[b]).values.astype(float))
        if pooled: arrs = [np.concatenate(arrs)]
        if any(len(x_) == 0 for x_ in arrs): stop(f"empty cell in {cells} {vw}")
        return float(np.mean([x_.mean() for x_ in arrs])), np.array([np.mean([x_[rng.integers(0, len(x_), len(x_))].mean() for x_ in arrs]) for _ in range(NB)])
    ci = lambda bs: np.percentile(bs, [2.5, 97.5]); fmt = lambda p_, bs: f"{p_:+.4f} [{ci(bs)[0]:+.4f}, {ci(bs)[1]:+.4f}]"
    pa, ba = boot(A, "c2", 149); pb, bb = boot(BD, "c2", 150); prim, bprim = 0.5 * pa + 0.5 * pb, 0.5 * ba + 0.5 * bb
    dirs = {f: 0.5 * boot([c for c in A if c[0] == f], "c2", 7)[0] + 0.5 * boot([c for c in BD if c[0] == f], "c2", 8)[0] for f in (3, 4)}
    npc1 = [c for c in NPC1 if len(cell(*c, "c1"))]
    PROT = {"old B' C2 (8 cells)": (OB, "c2", None, False), "E-outside C2 (A' + old B', pooled)": (A + OB, "c2", lambda r: ~r.t_esrc.astype(bool), True),
            "G C1 (2 cells)": (GC1, "c1", None, False), "NP C1 (pooled identities)": (npc1, "c1", None, True)}
    pr = {k: boot(c_, vw_, 11, ex_, pool_) for k, (c_, vw_, ex_, pool_) in PROT.items()}
    gate = prim >= 0.01 and ci(bprim)[0] > 0 and all(v_ > 0 for v_ in dirs.values()) and all(ci(b_)[0] >= -0.01 for _, b_ in pr.values())
    pk, bk = boot(A, "c2", 151, a="FM", b="FCcov"); pk2, bk2 = boot(BD, "c2", 152, a="FM", b="FCcov")
    L = [f"# 149 v2 S2 (i) MIST (M) vs current E2 recipe (C): fixed-recipe development cross-fit comparison ({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"- primary 1/2 A' + 1/2 B_D' (F_M - F_C, C2): **{fmt(prim, bprim)}** (A' {fmt(pa, ba)}, B_D' {fmt(pb, bb)})",
         f"- direction point estimates: fold 3 eval (4->3 models) {dirs[3]:+.4f}, fold 4 eval (3->4 models) {dirs[4]:+.4f}"]
    L += [f"- protection {k}: {fmt(*v_)}" for k, v_ in pr.items()]
    L += [f"- **gate: {'PASS' if gate else 'no'}**", "", "## Descriptive (not used for the decision)", "",
          f"- F_M - F_Ccov (same covered training groups): A' {fmt(pk, bk)}, B_D' {fmt(pk2, bk2)}"]
    for lab, cells, vw in (("A' C2", A, "c2"), ("B_D' C2", BD, "c2"), ("old B' C2", OB, "c2"), ("G C1", GC1, "c1"), ("NP C1", npc1, "c1")):
        r = pd.concat([cell(*c, vw) for c in cells])
        d_ = r.FM - r.FC; okw = (r.wf_state_C == "ok") & (r.wf_state_M == "ok")
        L.append(f"- {lab}: n {len(r)}, MIST-covered {r.covered.mean():.3f}, P empty {int(r.p_empty.sum())} | P {r.P.mean():.4f}, E2C {r.E2C.mean():.4f}, E2M {r.E2M.mean():.4f}, E2Ccov {r.E2Ccov.mean():.4f}, "
                 f"FC {r.FC.mean():.4f}, FM {r.FM.mean():.4f}, FCcov {r.FCcov.mean():.4f} | sum(+) {d_[d_ > 0].sum():.2f}, sum(-) {d_[d_ < 0].sum():.2f} | "
                 f"oracle max(E2C, E2M) - E2C {np.maximum(r.E2C, r.E2M).mean() - r.E2C.mean():+.4f} | P-wrong rows FM - FC {d_[r.P < 1].mean():+.4f} | "
                 f"same-formula truth rank C -> M (both ok, n {int(okw.sum())}): median {r.wf_rank_C[okw].median():.1f} -> {r.wf_rank_M[okw].median():.1f}, M better {int((r.wf_rank_M[okw] < r.wf_rank_C[okw]).sum())} / worse {int((r.wf_rank_M[okw] > r.wf_rank_C[okw]).sum())}")
    cs = pd.DataFrame(counts); cand = cs.dropna(subset=["cand_total"]) if "cand_total" in cs else cs
    L.append(f"- MIST candidate coverage (all frames): {int(cand.cand_covered.sum())} / {int(cand.cand_total.sum())}; MSG overlap of the rosters: 0 (preflight; sensitivity trivial)")
    open(os.path.join(OUT, "s2_mist_summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    man["seconds"] = round(time.time() - t0); man["models"] = {f: sha(os.path.join(OUT, "models", f)) for f in sorted(os.listdir(os.path.join(OUT, "models")))}
    json.dump(man, open(os.path.join(OUT, "s2_mist_manifest.json"), "w"), indent=1); print("\n".join(L)); print(f"S2_MIST_DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
