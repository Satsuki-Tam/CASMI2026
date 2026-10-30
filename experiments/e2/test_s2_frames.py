"""Technical checks of e2_s2_mist.frames / mist_table on artificial tables (Codex 149 Q2): one finite candidate, partial missing, all mass_mismatch,
negative-only (no_mist_adduct), inf, unknown status. Expected: covered sets, finite-min fill, STOP on inf / bad status / smiles mismatch."""
import os, sys, tempfile
import numpy as np, pandas as pd
sys.path.insert(0, r"C:\kaggle\CASMI\experiments\e2"); sys.path.insert(1, r"C:\kaggle\CASMI\experiments\b1_baseline")
import e2_s2_mist as S
tmp = tempfile.mkdtemp()   # artificial tables only (no project data); S.EW = os.path.join(tmp, "ewin"); S.MO = os.path.join(tmp, "mist"); os.makedirs(os.path.join(S.EW, "d"), exist_ok=True); os.makedirs(os.path.join(S.MO, "d"), exist_ok=True)
def mk(mol, keys, cos, status, nq=None, inf_at=None, smiles_bad=False):
    E = pd.DataFrame(dict(set="X", molecule=mol, official_key=keys, smiles=[f"C{k}" for k in keys], is_truth=[i == 0 for i in range(len(keys))], fp=np.linspace(1, -1, len(keys)),
                          fp_rank_e=range(1, len(keys) + 1), n_e=len(keys), ppm_err=1.0, in_train_c1=False, in_train_c2=False, in_coconut=True, in_pcl=False, in_bio=False,
                          lib_sim_c1=0.0, lib_sim_c2=0.0, lib_same_c1=0.0, lib_same_c2=0.0, lib_nref_c1=0, lib_nref_c2=0))
    F = pd.DataFrame(dict(set="X", molecule=mol, official_key=keys, frag=0.1, **{f"ana_{f}_{v}": 0.1 for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan") for v in ("c1", "c2")}))
    M = pd.DataFrame(dict(set="X", molecule=mol, smiles=[f"C{k}" + ("x" if smiles_bad else "") for k in keys], official_key=keys, mist_cos=cos, n_q=nq if nq is not None else [1 if s == "ok" else 0 for s in status], status=status))
    if inf_at is not None: M.loc[inf_at, "mist_cos"] = np.inf
    return E, F, M
cases = {
    "one_finite": mk("m1", ["a", "b", "c"], [0.8, np.nan, np.nan], ["ok", "no_formula", "mass_mismatch"]),
    "all_mismatch": mk("m2", ["a", "b"], [np.nan, np.nan], ["mass_mismatch", "mass_mismatch"]),
    "neg_only": mk("m3", ["a", "b"], [np.nan, np.nan], ["no_mist_adduct", "no_mist_adduct"]),
}
E = pd.concat([c[0] for c in cases.values()]); F = pd.concat([c[1] for c in cases.values()]); M = pd.concat([c[2] for c in cases.values()])
E.to_parquet(os.path.join(S.EW, "d", "ewin_X.parquet")); F.to_parquet(os.path.join(S.EW, "d", "e2f_X.parquet")); M.to_parquet(os.path.join(S.MO, "d", "mist_e2_X.parquet"))
Xc, Xm, cov, cc = S.frames("d", "X", "c2")
print("covered:", sorted(cov), "| cand covered", cc); print(Xm[["molecule", "official_key", "fp", "fp_rank", "fp_gap"]].to_string(index=False))
assert cov == {"m1"} and np.isclose(Xm.fp.tolist(), [0.8, 0.75, 0.75]).all()
for name, kw in (("inf", dict(inf_at=0)), ("bad_status", None), ("smiles_mismatch", dict(smiles_bad=True))):
    if name == "bad_status": e, f, m = mk("m9", ["a"], [0.5], ["weird"])
    else: e, f, m = mk("m9", ["a", "b"], [0.5, np.nan], ["ok", "no_formula"], **kw)
    e.to_parquet(os.path.join(S.EW, "d", "ewin_Y.parquet")); f.to_parquet(os.path.join(S.EW, "d", "e2f_Y.parquet")); m.to_parquet(os.path.join(S.MO, "d", "mist_e2_Y.parquet"))
    try:
        S.frames("d", "Y", "c2"); print(name, "-> NOT stopped (BAD)")
    except SystemExit as ex:
        print(name, "-> STOP:", str(ex)[:90])
print("TECH_CHECK_DONE")
