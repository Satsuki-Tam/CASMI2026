"""132 parity (A), part 2: the run of gen_eval2fd_e132.py (shared E-lite function asserted inside the 102 evaluator) against the stored 102 results.
Per table T: diag/r132A_<T>.csv vs diag/r102_<T>.csv -- unique keys (set, view, molecule), identical key sets, one-to-one join, and EXACT equality of
every main / E-lite column both runs have (main, n_cand, nE, e_reach, rP, p_e, rrf_pe_*, r_rank_e1r, rank_e1r_only, orc_rank_e1r, rrf_rank_e1r_*);
the assertion counts of the run (<out>_e132check.json) must cover every row with candidates of both views. Strata counts (E empty, truth outside E,
negative-ion only, strong class-1 reference lib_max_c1 >= 0.9 in view c1, GL fallback) are reported to show which cases the check covered.
Writes diag/x132a_compare.md / .json; exit 0 only on PASS.
Usage (Spark, experiments/b1_baseline): python -X utf8 ../b1_elite/x132a_compare.py"""
import glob, json, os, sys
import numpy as np, pandas as pd
T_ = {"np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe", "f1dev": "run_f1dev", "f2dev": "run_f2dev", "p2dev": "run_p2dev_fe"}
COLS = ["main", "n_cand", "nE", "e_reach", "rP", "p_e", "rrf_pe_0.5", "rrf_pe_1.0", "r_rank_e1r", "rank_e1r_only", "orc_rank_e1r", "rrf_rank_e1r_0.5", "rrf_rank_e1r_1.0"]
K = ["set", "view", "molecule"]
fails, md, res = [], ["# 132 parity (A): shared E-lite function inside the 102 evaluator vs the stored 102 results", ""], {}
md += ["| table | rows | key sets equal | columns equal | assertion count c1 / c2 (= rows with candidates) | E empty | truth outside E | negative only | strong C1 ref (c1) | GL fallback (c1 / c2) |", "|---|---:|---|---|---|---:|---:|---:|---:|---|"]
for T, run in T_.items():
    a_p, r_p, c_p = f"diag/r132A_{T}.csv", f"diag/r102_{T}.csv", f"diag/r132A_{T}_e132check.json"
    if not (os.path.exists(a_p) and os.path.exists(r_p) and os.path.exists(c_p)): fails.append(f"{T}: missing output"); md.append(f"| {T} | missing | | | | | | | | |"); continue
    A = pd.read_csv(a_p); R = pd.read_csv(r_p); C = json.load(open(c_p))
    for D in (A, R): D["molecule"] = D["molecule"].astype(str)
    uniq = A.duplicated(K).sum() == 0 and R.duplicated(K).sum() == 0
    ka, kr = set(map(tuple, A[K].values)), set(map(tuple, R[K].values)); same = ka == kr
    J = A.merge(R, on=K, how="inner", suffixes=("_a", "_r"), validate="one_to_one") if uniq else None
    bad = {}
    if J is not None:
        for c in COLS:
            if c + "_a" not in J.columns or c + "_r" not in J.columns: bad[c] = "missing column"; continue
            x, y = J[c + "_a"], J[c + "_r"]
            if x.dtype == bool or y.dtype == bool or c == "e_reach": eq = x.astype(str).str.lower() == y.astype(str).str.lower()
            else: eq = np.isclose(x.astype(float), y.astype(float), rtol=0, atol=0, equal_nan=True)
            if not np.all(eq): bad[c] = int((~np.asarray(eq)).sum())
    ncand = {v: int(((A.view == v) & (A.n_cand > 0)).sum()) for v in ("c1", "c2")}
    cnt = {v: int(C.get(f"rank_e1r|{v}|n", -1)) for v in ("c1", "c2")}
    cnt_ok = all(cnt[v] == ncand[v] for v in ("c1", "c2"))
    mols = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(f"{run}/b1_molecules_*.csv"))], ignore_index=True); mols["molecule"] = mols["molecule"].astype(str)
    mols = mols.drop_duplicates(["set", "molecule"]).set_index(["set", "molecule"])
    neg = A.apply(lambda r: all(str(x).endswith("-") for x in str(mols.loc[(r["set"], r["molecule"]), "adducts"]).split("|")) if (r["set"], r["molecule"]) in mols.index else False, axis=1)
    strong = A.apply(lambda r: r["view"] == "c1" and (r["set"], r["molecule"]) in mols.index and float(mols.loc[(r["set"], r["molecule"]), "lib_max_c1"]) >= 0.9, axis=1)
    st = dict(e_empty=int(((A.nE == 0) & (A.n_cand > 0)).sum()), truth_outside_e=int(((A.rP > 0) & ~A.e_reach.astype(str).str.lower().eq("true")).sum()),
              negative_only=int((neg & (A.n_cand > 0)).sum()), strong_c1=int((strong & (A.n_cand > 0)).sum()), fallback={v: int(C.get(f"rank_e1r|{v}|fallback", 0)) for v in ("c1", "c2")},
              top1_changed={v: int(C.get(f"rank_e1r|{v}|top1_changed", 0)) for v in ("c1", "c2")})
    ok = uniq and same and not bad and cnt_ok
    if not ok: fails.append(f"{T}: unique {uniq}, key sets equal {same}, differing columns {bad}, assertion counts {cnt} vs rows with candidates {ncand}")
    res[T] = dict(rows=len(A), unique=bool(uniq), key_sets_equal=bool(same), differing=bad, assertion_counts=cnt, rows_with_candidates=ncand, strata=st, pass_=bool(ok))
    md.append(f"| {T} | {len(A)} | {same} | {'all' if not bad else bad} | {cnt['c1']} / {cnt['c2']} (= {ncand['c1']} / {ncand['c2']}) | {st['e_empty']} | {st['truth_outside_e']} | {st['negative_only']} | {st['strong_c1']} | {st['fallback']['c1']} / {st['fallback']['c2']} |")
verdict = "PARITY_A PASS" if not fails else "PARITY_A FAIL: " + "; ".join(fails)
md = [md[0], "", f"**{verdict}**", ""] + md[1:]
open("diag/x132a_compare.md", "w", encoding="utf-8").write("\n".join(md) + "\n"); json.dump(dict(verdict=verdict, tables=res), open("diag/x132a_compare.json", "w"), indent=1)
print("\n".join(md)); sys.exit(0 if not fails else 1)
