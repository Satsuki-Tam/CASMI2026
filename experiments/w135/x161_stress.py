"""161: source-shift stress test of a verified FH experiment (development units only; descriptive, never e). Question: the W135 population is
COCONUT truths (every C1 / C2 truth is in E's sources), so how does the learned scorer rank a C2 truth that is OUTSIDE E's sources (e.g. a
PubChem-only structure), compared with F?
For every development fold f: load the saved fold model experiments/<exp>/fold-f/model.txt, featurize the fold's units with the workspace
adapter (read-only import), and
  (0) check that the actual predictions reproduce the experiment's verified OOF (STOP otherwise);
  (1) counterfactual: for each C2 query whose truth row is in P and in the E window, rewrite ONLY the truth row as an E-missing P row
      (in_E25 = in_Ewin = 0, e_miss = 1, e2_score = e2_rank = 0, in_coconut = in_pcl = in_bio = in_train_w = 0, lib_sim_w = ana_ap_w = 0,
      rep_E -> P, f_score = 1 / (10 + rP)), recompute the query's F order with the verified tie rule (-f_score, rP, e2_rank, key) -> f_rank,
      re-featurize and re-score with the same model. A C2 truth that is only in E (not in P) would leave U2: its slot is not submitted (RR 0 for both).
  Approximations (stated): the other candidates keep their E ranks / E25 membership and Q counts are unchanged.
Reports mean RR (F, FH) actual vs counterfactual on the targets, and the expected FH - F difference on C2 if a share q of C2 truths were
outside E's sources: (1 - q) * actual + q * counterfactual.
Usage: python -X utf8 experiments/w135/x161_stress.py --ws C:/kaggle/competitions/casmi-harness-v2 --exp baseline-11"""
import argparse, importlib.util, json, os, sys
import numpy as np, pandas as pd


def main():
    import lightgbm as lgb
    ap = argparse.ArgumentParser(); ap.add_argument("--ws", required=True); ap.add_argument("--exp", default="baseline-11"); a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.ws, "src"))
    spec = importlib.util.spec_from_file_location("adapter_x161", os.path.join(a.ws, "experiments", a.exp, "source", "adapter.py"))
    if not os.path.exists(spec.origin): spec = importlib.util.spec_from_file_location("adapter_x161", os.path.join(a.ws, "src", "adapter.py"))
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    import metrics as MET
    with np.load(os.path.join(a.ws, "data/folds/validation.npz"), allow_pickle=False) as Z: V = {k: Z[k] for k in Z.files}
    meta = {k[6:]: v for k, v in V.items() if k.startswith("meta__")}
    ids = V["ids"].astype(str); fold = V["fold"]; y = V["y"]
    oof = np.load(os.path.join(a.ws, "experiments", a.exp, "oof.npy")); oof_ids = np.load(os.path.join(a.ws, "experiments", a.exp, "oof_ids.npy")).astype(str)
    if list(oof_ids) != list(ids): sys.exit("STOP: oof ids differ from validation ids")
    Ud, Qd = A.load(a.ws, A.DEV_SUB, features_only=False); keys_of = A.slot_keys(Ud)
    units = pd.read_parquet(os.path.join(a.ws, "data/raw", A.DEV_SUB, "units_dev.parquet")).set_index("uid")
    rr_true = MET.reciprocal_ranks(y, oof, meta)
    res = []
    for f in sorted(set(fold.tolist())):
        bst = lgb.Booster(model_file=os.path.join(a.ws, "experiments", a.exp, f"fold-{f}", "model.txt"))
        va = list(ids[fold == f]); vi = np.flatnonzero(fold == f)
        R = A.featurize(Ud, Qd, va); s = bst.predict(R[A.FEATS].values.astype(float)) if len(R) else np.zeros(0)
        M = A.to_slots(va, R, s, keys_of); rr0 = MET.reciprocal_ranks(y[vi], M, {k: v[vi] for k, v in meta.items()})
        if not np.allclose(rr0, rr_true[vi], atol=1e-12): sys.exit(f"STOP: fold {f} predictions do not reproduce the verified OOF")
        Uc = Ud[Ud.uid.isin(set(va))].copy(); targets = []
        for u in va:
            if units.loc[u, "wclass"] != "C2": continue
            g = Uc[Uc.uid == u]; t = g[g.y == 1]
            if len(t) != 1: continue
            ti = t.index[0]
            if int(t.in_Ewin.iloc[0]) != 1: continue
            if int(t.in_P.iloc[0]) != 1: targets.append((u, "E-only")); continue   # leaves U2 in the counterfactual: its slot is set to not-submitted below
            Uc.loc[ti, ["in_E25", "in_Ewin", "e2_score", "e2_rank", "in_coconut", "in_pcl", "in_bio", "in_train_w", "lib_sim_w", "ana_ap_w"]] = 0
            Uc.loc[ti, "e_miss"] = 1; Uc.loc[ti, "f_score"] = 1.0 / (10 + float(t.rP.iloc[0]))
            if Uc.loc[ti, "rep"] == "E": Uc.loc[ti, "rep"] = "P"
            g = Uc[Uc.uid == u]; pool = g[g.in_F_pool == 1].assign(_k=lambda d: d.key.astype(str)).sort_values(["f_score", "rP", "e2_rank", "_k"], ascending=[False, True, True, True])
            Uc.loc[g.index, "f_rank"] = 26; Uc.loc[pool.index[:25], "f_rank"] = np.arange(1, min(25, len(pool)) + 1)
            targets.append((u, "P"))
        Rc = A.featurize(Uc, Qd, va); sc = bst.predict(Rc[A.FEATS].values.astype(float)) if len(Rc) else np.zeros(0)
        Mc = A.to_slots(va, Rc, sc, keys_of) if len(Rc) else np.full((len(va), A.K), A.PAD); pos = {u: i for i, u in enumerate(va)}
        for u, kind in targets:
            if kind == "E-only": Mc[pos[u], list(keys_of[u]).index(str(y[vi[pos[u]]]))] = -1e9
        rrc = MET.reciprocal_ranks(y[vi], Mc, {k: v[vi] for k, v in meta.items()})
        for u, kind in targets:
            i = pos[u]; g0 = Ud[(Ud.uid == u) & (Ud.y == 1)]; gc = Uc[(Uc.uid == u) & (Uc.y == 1)]
            fr0 = int(g0.f_rank.iloc[0]); frc = int(gc.f_rank.iloc[0]) if len(gc) else 26
            res.append(dict(uid=u, kind=kind, pi=int(units.loc[u, "pi"]), primary=bool(V["meta__primary"][vi[i]]),
                            F=1.0 / fr0 if fr0 <= 25 else 0.0, FH=float(rr0[i]), F_cf=1.0 / frc if frc <= 25 else 0.0, FH_cf=float(rrc[i])))
        print(f"fold {f}: OOF reproduced; C2 targets {len(targets)}", flush=True)
    D = pd.DataFrame(res); out = {}
    for name, m in (("PRIMARY pi0.3 C2 targets", D.primary), ("pi0 C2 targets", D.pi == 0)):
        d = D[m]; row = {k: float(d[k].mean()) for k in ("F", "FH", "F_cf", "FH_cf")}; row["n"] = int(len(d)); row["e_only"] = int((d.kind == "E-only").sum())
        row["diff_actual"] = row["FH"] - row["F"]; row["diff_cf"] = row["FH_cf"] - row["F_cf"]; out[name] = row
        print(f"{name:26s} n {row['n']:4d} (E-only {row['e_only']}) | actual F {row['F']:.4f} FH {row['FH']:.4f} diff {row['diff_actual']:+.4f} | "
              f"truth outside E sources: F {row['F_cf']:.4f} FH {row['FH_cf']:.4f} diff {row['diff_cf']:+.4f}")
        print("    expected FH - F on these C2 truths if a share q were outside E's sources: " +
              ", ".join(f"q={q:.1f} {(1 - q) * row['diff_actual'] + q * row['diff_cf']:+.4f}" for q in (0.0, 0.1, 0.2, 0.3, 0.5)))
    od = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x161"); os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, f"stress_{a.exp}.json"), "w"), indent=1); D.to_csv(os.path.join(od, f"stress_{a.exp}.csv"), index=False)


if __name__ == "__main__":
    main()
