"""v2 ONE-TIME holdout reading (docs/g0_spec.md section 5 of casmi-harness-v2): the frozen final candidate's test predictions on the fold-0
e-worlds at pi3 0.3 (596 units) vs the fixed references F (the submitted RRF reproduced in the world: Q2 f_top25) and P (P's own order).
Refuses to run a second time (marker experiments/w135/x162_hold/READ_ONCE.json; no overwrite), and refuses unless the experiment is VERIFIED
in the workspace ledger with matching artifact hashes. Labels and the uid mapping are read from OUTSIDE the workspace (fh2_export_map, fh2_src).
Gate (registered, section 8 (2)): candidate - F >= +0.01 and the e-pair bootstrap lower bound > 0 (pairs e1 / e2 / e3, 4000 draws, seed 20261030).
Usage: python -X utf8 experiments/w135/x162_hold_read.py --ws C:/kaggle/competitions/casmi-harness-v2 --exp <frozen experiment id> --i_have_user_ok"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
SEED, NB = 20261030, 4000
HOLD = [f"{b}_p30" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3")]


def rr_of(order_keys, t):
    return next((1.0 / (i + 1) for i, k in enumerate(order_keys[:25]) if k == t), 0.0)


def boot(d, units):
    u, inv = np.unique(units, return_inverse=True); s = np.bincount(inv, weights=d); c = np.bincount(inv).astype(float)
    rng = np.random.default_rng(SEED); bs = np.empty(NB)
    for i in range(NB):
        k = rng.integers(0, len(u), len(u)); bs[i] = s[k].sum() / c[k].sum()
    lo, hi = np.percentile(bs, [2.5, 97.5]); return float(lo), float(hi), int(len(u))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ws", required=True); ap.add_argument("--exp", required=True); ap.add_argument("--i_have_user_ok", action="store_true"); a = ap.parse_args()
    if not a.i_have_user_ok: sys.exit("STOP: the one-time holdout read needs the user's explicit OK (pass --i_have_user_ok only after it)")
    od = os.path.join(HERE, "x162_hold"); marker = os.path.join(od, "READ_ONCE.json")
    if os.path.exists(marker): sys.exit(f"STOP: the holdout was already read ({marker})")
    # the experiment must be verified with matching artifacts
    led = [json.loads(l) for l in open(os.path.join(a.ws, "state/experiments.jsonl"), encoding="utf-8") if l.strip()]
    rec = [r for r in led if r.get("id") == a.exp]
    if not rec or not rec[-1].get("verified"): sys.exit(f"STOP: {a.exp} is not a verified experiment")
    E = os.path.join(a.ws, "experiments", a.exp); arts = rec[-1].get("artifact_hashes") or {}
    for f in ("test.npy", "test_ids.npy"):
        if f in arts and sha(os.path.join(E, f)) != arts[f]: sys.exit(f"STOP: {f} differs from the ledger")
    test = np.load(os.path.join(E, "test.npy")); tids = np.load(os.path.join(E, "test_ids.npy")).astype(str)
    with np.load(os.path.join(a.ws, "data/folds/test_slots.npz"), allow_pickle=False) as Z: S = {k: Z[k] for k in Z.files}
    skeys = S["cand_keys"]; svalid = S["cand_valid"]; sids = S["test_ids"].astype(str)
    if list(sids) != list(tids): sys.exit("STOP: test ids differ from the pinned test slots")
    M = pd.read_parquet(os.path.join(HERE, "fh2_export_map", "map_hold_ids.parquet")).set_index("uid")
    rows = []
    Qs = {w: pd.read_parquet(os.path.join(HERE, "fh2_src", f"Q2_{w}.parquet"), columns=["molecule", "truth", "wclass", "f_top25"]).assign(molecule=lambda d: d.molecule.astype(str)).set_index("molecule") for w in HOLD}
    Us = {w: pd.read_parquet(os.path.join(HERE, "fh2_src", f"U2_{w}.parquet"), columns=["molecule", "key", "in_P", "rP"]).assign(molecule=lambda d: d.molecule.astype(str)) for w in HOLD}
    for i, u in enumerate(tids):
        w, m = M.loc[u, "world"], str(M.loc[u, "molecule"]); q = Qs[w].loc[m]; t = str(q.truth)
        ks = [str(k) for k in skeys[i]]; s = test[i]
        v = np.flatnonzero(svalid[i] & (s > -1e8)); cand = [ks[j] for j in v[np.lexsort((v, -s[v]))]] if len(v) else []
        Pm = Us[w][(Us[w].molecule == m) & (Us[w].in_P == 1)].sort_values("rP").key.astype(str).tolist()
        rows.append(dict(uid=u, world=w, pair="e" + w[2], wclass=str(q.wclass), FH=rr_of(cand, t), F=rr_of(json.loads(q.f_top25), t), P=rr_of(Pm, t)))
    D = pd.DataFrame(rows); out = dict(experiment=a.exp, n=int(len(D)), populations=[])
    for name, m in [("e pi0.3 all (596)", np.ones(len(D), bool))] + [(f"e pi0.3 {c}", (D.wclass == c).values) for c in ("C1", "C2", "C3")]:
        d = D[m]; row = dict(population=name, n=int(len(d)), FH=float(d.FH.mean()), F=float(d.F.mean()), P=float(d.P.mean()))
        for ref in ("F", "P"):
            lo, hi, nu = boot((d.FH - d[ref]).values, d.pair.values); row[f"diff_vs_{ref}"] = float((d.FH - d[ref]).mean()); row[f"pair_ci_vs_{ref}"] = [lo, hi]; row["pair_units"] = nu
        out["populations"].append(row)
        print(f"{name:20s} n {row['n']:4d} FH {row['FH']:.4f} F {row['F']:.4f} P {row['P']:.4f} | vs F {row['diff_vs_F']:+.4f} [{row['pair_ci_vs_F'][0]:+.4f}, {row['pair_ci_vs_F'][1]:+.4f}] | vs P {row['diff_vs_P']:+.4f}")
    g = out["populations"][0]; out["gate_pass"] = bool(g["diff_vs_F"] >= 0.01 and g["pair_ci_vs_F"][0] > 0)
    print("HOLDOUT GATE", "PASS" if out["gate_pass"] else "FAIL", "(candidate - F >= +0.01 and e-pair lower > 0)")
    os.makedirs(od, exist_ok=True); json.dump(out, open(os.path.join(od, f"hold_{a.exp}.json"), "w"), indent=1)
    json.dump(dict(experiment=a.exp, test_sha256=sha(os.path.join(E, "test.npy")), script_sha256=sha(os.path.abspath(__file__))), open(marker, "w"), indent=1)


if __name__ == "__main__":
    main()
