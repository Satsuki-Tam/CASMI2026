"""145 kernel parity check v2 (Codex 145 Q4): the generated E2 pipeline (experiments/b1_e2k/b1_pipeline.py) run in the panel C1 evaluation mode
with --e2_dump 1, against
 (0) population: the test file's molecule ids = submission ids = submission_pref ids; the E2 dump molecules = the development table molecules
     (both restricted to the test ids; an empty window on one side only is a failure); e2_failed = 0 in the manifest;
 (1) the development E-window / feature tables of the same molecules: identical official-key sets; numeric C1 columns equal (NaN on both
     sides or finite and |diff| <= 1e-4; NaN on one side, or inf, is a failure); flags identical;
 (2) the E2 order computed from the dump and from the development tables (same model): identical ordered top 25;
 (3) F recomputed offline from the run's own P list (submission_pref.csv, SMILES -> official key through b1_candidates.parquet) and the
     development E2 order with e2_engine.fuse_rrf (alpha 0.5; --hedge 1 adds insert2): identical ordered keys for every molecule;
 (4) P against the reference run (--p_ref, e.g. the PC v8w7a run of the same evaluation test): identical ordered official-key lists.
PASS = (0)-(4) all hold. No performance number is printed.
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/e2k_parity_check.py --run DIR --ewin experiments/e2/ewin/panel_np250 --set P_np250 --model M
               --test eval_test/test.parquet --p_ref REF/submission.csv --p_ref_cand REF/b1_candidates.parquet [--hedge 0]"""
import argparse, json, os, sys
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "experiments", "b1_baseline"))
from e2_engine import fuse_rrf, insert2
from e2_common import FEATS, view_frame, rank_lists


def orders(E, F, booster):
    X = view_frame(E, F, "c1"); p = booster.predict(X[FEATS])
    if not np.isfinite(p).all(): raise SystemExit("STOP: non-finite E2 prediction")
    R = rank_lists(X, p); return {m: g.official_key.astype(str).tolist() for m, g in R.groupby("molecule", sort=False)}


def same_num(a, b, tol=1e-4):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if np.isinf(a).any() or np.isinf(b).any(): return False
    na, nb = np.isnan(a), np.isnan(b)
    if (na != nb).any(): return False
    return bool((np.abs(a[~na] - b[~nb]) <= tol).all())


def keymap(cand_path):
    c = pd.read_parquet(cand_path, columns=["molecule", "key", "smiles"]); c["molecule"] = c.molecule.astype(str)
    return {m: dict(zip(g.smiles.astype(str), g.key.astype(str))) for m, g in c.groupby("molecule")}


def main():
    ap = argparse.ArgumentParser()
    for k in ("run", "ewin", "set", "model", "test", "p_ref", "p_ref_cand"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--hedge", type=int, default=0); a = ap.parse_args()
    bad = {}; note = lambda k, n=1: bad.__setitem__(k, bad.get(k, 0) + n)
    test_ids = set(pd.read_parquet(a.test, columns=["molecule_id"]).molecule_id.astype(str))
    sub = pd.read_csv(f"{a.run}/submission.csv", dtype=str, keep_default_na=False).set_index("molecule_id").smiles
    pref = pd.read_csv(f"{a.run}/submission_pref.csv", dtype=str, keep_default_na=False).set_index("molecule_id").smiles
    for name, s in (("submission", sub), ("submission_pref", pref)):
        if not s.index.is_unique or set(s.index) != test_ids: note(f"population_{name}")
    man = json.load(open(f"{a.run}/b1_run_manifest.json")); e2m = man.get("e2") or {}
    if e2m.get("e2_failed", -1) != 0: note("e2_failed", int(e2m.get("e2_failed", -1)))
    if e2m.get("hedge") != a.hedge: note("hedge_flag")
    E1 = pd.read_parquet(f"{a.run}/e2_ewin.parquet"); F1 = pd.read_parquet(f"{a.run}/e2_feats.parquet")
    E0 = pd.read_parquet(f"{a.ewin}/ewin_{a.set}.parquet"); F0 = pd.read_parquet(f"{a.ewin}/e2f_{a.set}.parquet")
    for D in (E1, F1, E0, F0): D["molecule"] = D.molecule.astype(str); D["set"] = a.set; D["official_key"] = D.official_key.astype(str)
    E0 = E0[E0.molecule.isin(test_ids)]; F0 = F0[F0.molecule.isin(test_ids)]
    if set(E1.molecule) != set(E0.molecule): note("population_e2_tables", len(set(E1.molecule) ^ set(E0.molecule)))
    if set(F1.molecule) != set(E1.molecule): note("population_e2_feats")
    COLS = ["fp", "ppm_err", "lib_sim_c1", "lib_same_c1", "lib_nref_c1"]; BCOLS = ["in_train_c1", "in_coconut", "in_pcl", "in_bio", "is_truth"]
    FC = ["frag"] + [f"ana_{f}_c1" for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan")]; ok_mols = 0
    for m in sorted(set(E1.molecule) & set(E0.molecule)):
        e1 = E1[E1.molecule == m].set_index("official_key"); e0 = E0[E0.molecule == m].set_index("official_key")
        if not (e1.index.is_unique and e0.index.is_unique) or set(e1.index) != set(e0.index): note("keys"); continue
        e1 = e1.loc[e0.index]; f1 = F1[F1.molecule == m].set_index("official_key"); f0 = F0[F0.molecule == m].set_index("official_key")
        if set(f1.index) != set(e0.index) or set(f0.index) != set(e0.index): note("feat_keys"); continue
        f1 = f1.loc[e0.index]; f0 = f0.loc[e0.index]
        bad_m = [c for c in COLS if not same_num(e1[c], e0[c])] + [c for c in FC if not same_num(f1[c], f0[c])] + [c for c in BCOLS if (e1[c].astype(bool).values != e0[c].astype(bool).values).any()]
        if bad_m: note("columns"); note("columns_" + "_".join(sorted(set(bad_m)))[:60])
        else: ok_mols += 1
    b = lgb.Booster(model_file=a.model); O1 = orders(E1, F1, b); O0 = orders(E0, F0, b)
    nord = sum(O1.get(m, [])[:25] != O0.get(m, [])[:25] for m in set(E1.molecule) | set(E0.molecule))
    if nord: note("e2_order", nord)
    s2k = keymap(f"{a.run}/b1_candidates.parquet"); e2s = {m: dict(zip(g.smiles.astype(str), g.official_key.astype(str))) for m, g in E0.groupby("molecule")}
    nfuse = nunm = nchg = 0
    for m in sorted(test_ids):
        if pref[m] == "CCO":
            if sub[m] != pref[m]: nfuse += 1
            continue
        mp = {**e2s.get(m, {}), **s2k.get(m, {})}
        pk = [mp.get(x) for x in pref[m].split(";")]; fk = [mp.get(x) for x in sub[m].split(";")]
        if None in pk or None in fk: nunm += 1; continue
        el = O0.get(m, []); er = {k: i + 1 for i, k in enumerate(el)}; want = fuse_rrf(pk, er, el[:25], 0.5)
        if a.hedge: want = insert2(want, el[0] if el else None)
        if want != fk: nfuse += 1
        nchg += int(sub[m] != pref[m])
    if nfuse: note("fusion", nfuse)
    if nunm: note("fusion_unmapped", nunm)
    ref = pd.read_csv(a.p_ref, dtype=str, keep_default_na=False).set_index("molecule_id").smiles; rk = keymap(a.p_ref_cand)
    if set(ref.index) != test_ids: note("p_ref_population")
    np_diff = 0
    for m in sorted(test_ids & set(ref.index)):
        if pref[m] == "CCO" or ref[m] == "CCO":
            np_diff += int(pref[m] != ref[m]); continue
        a_ = [s2k.get(m, {}).get(x) for x in pref[m].split(";")]; b_ = [rk.get(m, {}).get(x) for x in ref[m].split(";")]
        if None in a_ or None in b_ or a_ != b_: np_diff += 1
    if np_diff: note("p_vs_ref", np_diff)
    rep = dict(test_molecules=len(test_ids), e2_table_molecules=len(set(E1.molecule)), molecules_all_columns_equal=ok_mols, lists_changed_by_fusion=nchg,
               e2_manifest={k: e2m.get(k) for k in ("e2_failed", "e2_nonempty", "molecules", "hedge", "index_unmapped_rows", "index_keys", "e2_seconds")}, failures=bad)
    ok = not bad; print(json.dumps(rep, indent=1)); print("E2K_PARITY_" + ("PASS" if ok else "FAIL")); sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
