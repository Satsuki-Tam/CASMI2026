"""145 kernel parity check: the generated E2 pipeline (experiments/b1_e2k/b1_pipeline.py) run in the panel C1 evaluation mode with --e2_dump 1,
against (1) the development E-window / feature tables of the same molecules (C1 columns, exact up to 1e-4), (2) the E2 order computed from
those tables, (3) F recomputed offline from the run's own P list (submission_pref.csv, SMILES -> official key through b1_candidates.parquet)
and the development E2 order with e2_engine.fuse_rrf. Also reports P against a reference run (same lists?) and the run's F / P scores.
PASS = every molecule identical in (1)-(3).
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/e2k_parity_check.py --run DIR --ewin experiments/e2/ewin/panel_np250 --set P_np250 --model M [--p_ref CSV]"""
import argparse, json, os, sys
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "experiments", "b1_baseline"))
from e2_engine import fuse_rrf
from e2_common import FEATS, view_frame, rank_lists


def orders(E, F, booster):
    X = view_frame(E, F, "c1"); R = rank_lists(X, booster.predict(X[FEATS]))
    return {m: g.official_key.astype(str).tolist() for m, g in R.groupby("molecule", sort=False)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--ewin", required=True); ap.add_argument("--set", required=True)
    ap.add_argument("--model", required=True); ap.add_argument("--p_ref", default=""); a = ap.parse_args()
    E1 = pd.read_parquet(f"{a.run}/e2_ewin.parquet"); F1 = pd.read_parquet(f"{a.run}/e2_feats.parquet")
    E0 = pd.read_parquet(f"{a.ewin}/ewin_{a.set}.parquet"); F0 = pd.read_parquet(f"{a.ewin}/e2f_{a.set}.parquet")
    for D in (E1, F1, E0, F0): D["molecule"] = D.molecule.astype(str); D["set"] = a.set; D["official_key"] = D.official_key.astype(str)
    COLS = ["fp", "ppm_err", "lib_sim_c1", "lib_same_c1", "lib_nref_c1"]; BCOLS = ["in_train_c1", "in_coconut", "in_pcl", "in_bio", "is_truth"]; FC = ["frag"] + [f"ana_{f}_c1" for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan")]
    bad = dict(mol_missing=0, keys=0, cols=0, order=0, fuse=0, fuse_unmapped=0); worst = {c: 0.0 for c in COLS + FC}
    m1, m0 = set(E1.molecule), set(E0.molecule); bad["mol_missing"] = len(m0 ^ m1)
    for m in sorted(m0 & m1):
        e1 = E1[E1.molecule == m].set_index("official_key"); e0 = E0[E0.molecule == m].set_index("official_key")
        if set(e1.index) != set(e0.index): bad["keys"] += 1; continue
        e1 = e1.loc[e0.index]; f1 = F1[F1.molecule == m].set_index("official_key").loc[e0.index]; f0 = F0[F0.molecule == m].set_index("official_key").loc[e0.index]
        d = {c: float(np.nanmax(np.abs(e1[c].astype(float).values - e0[c].astype(float).values))) for c in COLS}
        d.update({c: float(np.nanmax(np.abs(f1[c].astype(float).values - f0[c].astype(float).values))) for c in FC})
        for c, v in d.items(): worst[c] = max(worst[c], v)
        if any(v > 1e-4 for v in d.values()) or any((e1[c].astype(bool).values != e0[c].astype(bool).values).any() for c in BCOLS): bad["cols"] += 1
    b = lgb.Booster(model_file=a.model); O1 = orders(E1, F1, b); O0 = orders(E0, F0, b)
    bad["order"] = sum(O1.get(m, [])[:25] != O0.get(m, [])[:25] for m in m0 & m1)
    cand = pd.read_parquet(f"{a.run}/b1_candidates.parquet", columns=["molecule", "key", "smiles"]); cand["molecule"] = cand.molecule.astype(str)
    s2k = {m: dict(zip(g.smiles.astype(str), g.key.astype(str))) for m, g in cand.groupby("molecule")}
    e2s = {m: dict(zip(g.smiles.astype(str), g.official_key.astype(str))) for m, g in E0.groupby("molecule")}
    pref = pd.read_csv(f"{a.run}/submission_pref.csv", dtype=str, keep_default_na=False).set_index("molecule_id").smiles
    sub = pd.read_csv(f"{a.run}/submission.csv", dtype=str, keep_default_na=False).set_index("molecule_id").smiles
    n_changed = 0
    for m in pref.index:
        if pref[m] == "CCO": bad["fuse"] += int(sub[m] != pref[m]); continue
        mp = {**e2s.get(m, {}), **s2k.get(m, {})}
        pk = [mp.get(x) for x in pref[m].split(";")]; fk = [mp.get(x) for x in sub[m].split(";")]
        if None in pk or None in fk: bad["fuse_unmapped"] += 1; continue
        el = O0.get(m, []); er = {k: i + 1 for i, k in enumerate(el)}
        if fuse_rrf(pk, er, el[:25], 0.5) != fk: bad["fuse"] += 1
        n_changed += int(sub[m] != pref[m])
    rep = dict(molecules=len(m0 & m1), worst={k: round(v, 8) for k, v in worst.items()}, bad=bad, lists_changed_by_F=n_changed)
    if a.p_ref:
        ref = pd.read_csv(a.p_ref, dtype=str, keep_default_na=False).set_index("molecule_id").smiles
        rep["p_vs_ref_identical"] = int(sum(ref.get(m) == pref[m] for m in pref.index)); rep["p_vs_ref_n"] = len(pref)
    sc = os.path.join(a.run, "eval_scores.json")
    if os.path.exists(sc): j = json.load(open(sc)); rep["scores"] = dict(F=j.get("official_mrr25"), P=j.get("official_mrr25_pref"))
    ok = not any(bad.values()); print(json.dumps(rep, indent=1)); print("E2K_PARITY_" + ("PASS" if ok else "FAIL")); sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
