"""W135 142 (142_prereg_w135_calib.md): the two-stage probability on top of the FROZEN 139 selector -- candidate order fixed.
  s_i = softmax(z_i / T) within B (z = the 139 logit), r = P(truth in B | query summary) (L2 logistic, C 1.0, query-level, equal weights),
  p_i = r * s_i, then the 139 policy (frozen q table, k <= min(3, |P| + 1), insert if G > 0). B = 0 -> r = 0 (kept in the denominators).
Modes:
  oof    : the 18 design worlds; base selector refit leave-one-pair-out (as 139 cv) -> out-of-fold logits per B row (s3/oof_rows.parquet)
           and the query table (s3/oof_q.parquet);
  fit    : T (query-equal conditional likelihood of the truth over queries with the truth in B; log grid + golden section on [0.05, 20])
           and the gate r on the out-of-fold logits -> s3/calib_freeze.json (refuses to overwrite);
  nested : descriptive development estimate -- per outer pair, the base refit on the two other pairs, T / r fitted on their inner OOF logits
           (inner leave-one-pair-out), applied to the held-out pair -> s3/nested_queries.parquet;
  apply  : the 12 fold-0 confirmation worlds (eF1-3 / eR1-3 x pi 0.3 / 0): P, the frozen 139 (its own p) and C142 -> s3/confirm_queries.parquet.
Every world passes w135_selector.load_world's checks (manifest, generation meta, product GL, B invariants, one-to-one ids).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_calib.py --mode oof|fit|nested|apply"""
import argparse, hashlib, json, math, os, sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w135_selector as S
ROOT = S.ROOT; S3 = os.path.join(ROOT, "experiments/w135/s3"); os.makedirs(S3, exist_ok=True)
CONF = [f"{b}_p{p}" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3") for p in (30, 0)]
QF = ["log_nb", "zmax", "zgap", "p_gap12", "gl_ok", "lib_max", "log_ncand", "best_analog", "n_peer_struct"]
sha = S.sha
def stop(m): sys.exit(f"STOP (w135_calib): {m}")
pair = lambda w: w.split("_p")[0][-1]


def logits(R, model):
    if not len(R): return np.zeros(0)
    Z = (R[S.FEATS].values.astype(float) - np.asarray(model["mean"])) / np.asarray(model["scale"]); return Z @ np.asarray(model["coef"]) + model["intercept"]


def qsummary(R, Q):
    """query-level summary (QF) from the B rows' logit column z and the query frame; queries without B get NaN rows (r = 0 by rule)."""
    g = R.groupby(["world", "molecule"])
    agg = pd.DataFrame(dict(zmax=g.z.max(), zgap=g.z.apply(lambda v: float(np.sort(v.values)[-1] - np.sort(v.values)[-2]) if len(v) > 1 else 0.0),
                            log_nb=g.log_nb.first(), p_gap12=g.p_gap12.first(), log_ncand=g.log_ncand.first(),
                            best_analog=g.best_analog.first(), n_peer_struct=g.n_peer_struct.first())).reset_index()   # gl_ok / lib_max come from Q
    out = Q.merge(agg, on=["world", "molecule"], how="left")
    if out[["world", "molecule"]].duplicated().any(): stop("duplicate query rows")
    return out


def fit_T(R):
    """T maximising the mean (over queries with the truth in B) of log softmax(z_truth / T)."""
    qs = [(g.z.values.astype(float), int(np.flatnonzero(g.y.values == 1)[0])) for _, g in R.groupby(["world", "molecule"]) if (g.y == 1).any()]
    if not qs: stop("no query with the truth in B")
    def ll(T): return float(np.mean([z[t] / T - (np.max(z / T) + np.log(np.exp(z / T - np.max(z / T)).sum())) for z, t in qs]))
    grid = np.exp(np.linspace(np.log(0.05), np.log(20), 60)); vals = [ll(t) for t in grid]; i = int(np.argmax(vals))
    lo, hi = grid[max(0, i - 1)], grid[min(len(grid) - 1, i + 1)]; gr = (math.sqrt(5) - 1) / 2
    for _ in range(60):
        a_, b_ = hi - gr * (hi - lo), lo + gr * (hi - lo)
        if ll(a_) > ll(b_): hi = b_
        else: lo = a_
    return float((lo + hi) / 2), len(qs)


def fit_gate(Qs):
    from sklearn.linear_model import LogisticRegression
    D = Qs[Qs.n_b > 0]; X = D[QF].values.astype(float); y = D.truth_in_B.astype(int).values
    if y.sum() == 0 or y.sum() == len(y): stop("gate training without both classes")
    mu, sd = X.mean(0), X.std(0); sd = np.where(sd > 0, sd, 1.0)
    clf = LogisticRegression(C=1.0, max_iter=2000).fit((X - mu) / sd, y)
    return dict(mean=mu.tolist(), scale=sd.tolist(), coef=clf.coef_[0].tolist(), intercept=float(clf.intercept_[0]), n=int(len(D)), pos=int(y.sum()))


def gate_r(Qs, gate):
    X = Qs[QF].values.astype(float); z = ((X - np.asarray(gate["mean"])) / np.asarray(gate["scale"])) @ np.asarray(gate["coef"]) + gate["intercept"]
    r = 1.0 / (1.0 + np.exp(-z)); return np.where(Qs.n_b.values > 0, r, 0.0)


def calibrated_p(R, Qs, T, gate):
    R = R.copy(); r = dict(zip(zip(Qs.world, Qs.molecule), gate_r(Qs, gate)))
    R["s"] = R.groupby(["world", "molecule"]).z.transform(lambda v: np.exp(v / T - np.max(v / T)) / np.exp(v / T - np.max(v / T)).sum())
    R["p"] = [r[(w, m)] * s_ for w, m, s_ in zip(R.world, R.molecule, R.s)]; return R


def policy_p(R, Q, qt):
    """the 139 policy (copied from w135_selector.policy) with a given probability column p."""
    best = (R.sort_values(["world", "molecule", "p", "fz", "key"], ascending=[True, True, False, False, True]).groupby(["world", "molecule"]).head(1).set_index(["world", "molecule"])
            if len(R) else pd.DataFrame(columns=["p", "key"]))
    out = []
    for q in Q.itertuples(index=False):
        top = json.loads(q.top25); act, kstar, ph, xk = "keep", 0, float("nan"), ""
        if (q.world, q.molecule) in best.index:
            x = best.loc[(q.world, q.molecule)]; ph = float(x["p"]); xk = str(x["key"]); qq = qt[q.bin]; G = []
            for k in range(1, min(3, len(top) + 1) + 1):
                loss = sum(qq[r - 1] * ((1.0 / r - 1.0 / (r + 1)) if r < 25 else 1.0 / 25) for r in range(k, min(25, len(top)) + 1)); G.append(ph / k - loss)
            kb = int(np.argmax(G))
            if G[kb] > 0: act, kstar = "insert", kb + 1
        new = (top[:kstar - 1] + [xk] + top[kstar - 1:])[:25] if act == "insert" else top[:25]
        rr = lambda lst: next((1.0 / (i + 1) for i, k in enumerate(lst[:25]) if k == q.truth), 0.0)
        out.append(dict(world=q.world, batch=q.batch, pi=q.pi, molecule=q.molecule, fam=q.fam, wclass=q.wclass, used=q.used, truth=q.truth, truth_in_B=q.truth_in_B, n_b=q.n_b,
                        action=act, k=kstar, p_hat=ph, x_key=xk, top25=json.dumps(top), new25=json.dumps(new), rrP=rr(top), rr=rr(new)))
    return pd.DataFrame(out)


def load(worlds):
    Rs, Qs = [], []
    for w in worlds:
        R, Q = S.load_world(w, with_truth=True); Rs.append(R); Qs.append(Q); print(f"  {w}: {len(Q)} queries, {len(R)} rows", flush=True)
    return pd.concat(Rs, ignore_index=True), pd.concat(Qs, ignore_index=True)


def oof_logits(R, Q, worlds):
    out = []
    for f in sorted({pair(w) for w in worlds}):
        tr = [w for w in worlds if pair(w) != f]; te = [w for w in worlds if pair(w) == f]
        model, _ = S.fit(R[R.world.isin(tr)], Q[Q.world.isin(tr)]); Rt = R[R.world.isin(te)].copy(); Rt["z"] = logits(Rt, model); out.append(Rt)
    return pd.concat(out, ignore_index=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", required=True, choices=["oof", "fit", "nested", "apply"]); a = ap.parse_args(); t0 = time.time()
    base = json.load(open(os.path.join(ROOT, "experiments/w135/s2/fit_model.json"))); fz = json.load(open(os.path.join(ROOT, "experiments/w135/s2/fit_freeze.json")))
    if sha(os.path.join(ROOT, "experiments/w135/s2/fit_model.json")) != fz["model_sha256"] or base["feats"] != S.FEATS: stop("139 frozen model mismatch")
    if a.mode == "oof":
        if os.path.exists(os.path.join(S3, "oof_rows.parquet")): stop("oof exists")
        R, Q = load(S.DESIGN); Ro = oof_logits(R, Q, S.DESIGN)
        Ro[["world", "molecule", "key", "z", "y"] + S.FEATS].to_parquet(os.path.join(S3, "oof_rows.parquet"), index=False); Q.to_parquet(os.path.join(S3, "oof_q.parquet"), index=False)
        print(f"oof: {len(Ro)} rows ({time.time()-t0:.0f}s)")
    elif a.mode == "fit":
        if os.path.exists(os.path.join(S3, "calib_freeze.json")): stop("freeze exists")
        Ro = pd.read_parquet(os.path.join(S3, "oof_rows.parquet")); Q = pd.read_parquet(os.path.join(S3, "oof_q.parquet"))
        T, nq = fit_T(Ro); gate = fit_gate(qsummary(Ro, Q))
        fr = dict(T=T, T_queries=nq, gate=gate, qf=QF, base_model_sha256=fz["model_sha256"], oof_rows_sha256=sha(os.path.join(S3, "oof_rows.parquet")), script_sha256=sha(os.path.abspath(__file__)))
        json.dump(fr, open(os.path.join(S3, "calib_freeze.json"), "w"), indent=1); print(json.dumps({k: v for k, v in fr.items() if k != "gate"}), "gate n", gate["n"], "pos", gate["pos"])
    elif a.mode == "nested":
        R, Q = load(S.DESIGN); outs = []
        for f in sorted({pair(w) for w in S.DESIGN}):
            tr = [w for w in S.DESIGN if pair(w) != f]; te = [w for w in S.DESIGN if pair(w) == f]
            Rin, Qin = R[R.world.isin(tr)], Q[Q.world.isin(tr)]; Roi = oof_logits(Rin, Qin, tr)
            T, _ = fit_T(Roi); gate = fit_gate(qsummary(Roi, Qin)); model, qt = S.fit(Rin, Qin)
            Rt = R[R.world.isin(te)].copy(); Rt["z"] = logits(Rt, model); Qt = qsummary(Rt, Q[Q.world.isin(te)])
            outs.append(policy_p(calibrated_p(Rt, Qt, T, gate), Qt, qt).assign(T=T, outer=f))
        pd.concat(outs, ignore_index=True).to_parquet(os.path.join(S3, "nested_queries.parquet"), index=False); print(f"nested done ({time.time()-t0:.0f}s; no score printed)")
    else:
        fr = json.load(open(os.path.join(S3, "calib_freeze.json")))
        if fr["base_model_sha256"] != fz["model_sha256"]: stop("calibration freeze / base mismatch")
        if os.path.exists(os.path.join(S3, "confirm_queries.parquet")): stop("confirm exists")
        R, Q = load(CONF); R["z"] = logits(R, base["model"]); Qs = qsummary(R, Q)
        R139 = R.copy(); R139["p"] = 1.0 / (1.0 + np.exp(-R139.z)); res139 = policy_p(R139, Qs, base["q_table"])
        res142 = policy_p(calibrated_p(R, Qs, fr["T"], fr["gate"]), Qs, base["q_table"])
        m = res142.merge(res139[["world", "molecule", "rr", "action", "k", "x_key", "new25", "p_hat"]], on=["world", "molecule"], suffixes=("", "_139"), validate="one_to_one")
        m.to_parquet(os.path.join(S3, "confirm_queries.parquet"), index=False)
        json.dump(dict(worlds=CONF, freeze_sha256=sha(os.path.join(S3, "calib_freeze.json")), base_model_sha256=fz["model_sha256"], queries_sha256=sha(os.path.join(S3, "confirm_queries.parquet")),
                       script_sha256=sha(os.path.abspath(__file__))), open(os.path.join(S3, "confirm_meta.json"), "w"), indent=1)
        print(f"apply: {len(m)} queries -> s3/confirm_queries.parquet ({time.time()-t0:.0f}s; no score printed)")
