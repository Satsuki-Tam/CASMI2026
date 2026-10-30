"""160 decision (Codex 160 Q1): LABEL-FREE structural check of the six fold-0 e-worlds at pi3 0.3 (the holdout), the same set / order checks
x158_diag.py runs on the development worlds, without reading any truth, class, family, label, reach or metric column (columns are selected
at read time; truth / wclass / fam / y / is_truth / truth_in_ewin are never loaded). Per world and query:
  R  rosters: v1 Q == U2 Q == E ledger == the batch CSV (no duplicates);
  S  U2 key set == P25 (v1 table, src P) | E25 (top 25 of the v2.1 e2s by e2_rank) | B (v1 table, src B);
  O  P order in U2 (in_P rows by rP) == P order in the v1 table; E ledger: n_e of the ledger == Q2.n_e == number of e2s rows, ranks 1..n_e;
  F  F list: P empty -> []; E empty -> P; else e2_engine.fuse_rrf(P25, full-window ranks, E25, 0.5) == Q2.f_top25 == the f_rank order of U2.
Prints match counts and PASS / FAIL only. Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/x160_echeck.py"""
import json, os, sys
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments/e2")); sys.path.insert(1, os.path.join(ROOT, "experiments/b1_baseline"))
import e2_engine as E2M
FH1 = os.path.join(ROOT, "experiments/w135/fh"); FH2 = os.path.join(ROOT, "experiments/w135/fh2_1"); V2 = os.path.join(ROOT, "experiments/w135/v2_1")
HOLD = [f"{b}_p30" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3")]


def main():
    fails = []; n = dict(R=0, S=0, O=0, F=0, q=0)
    for w in HOLD:
        b = w.split("_p")[0]
        U1 = pd.read_parquet(os.path.join(FH1, f"U_{w}.parquet"), columns=["molecule", "key", "src", "rP"])
        Q1 = pd.read_parquet(os.path.join(FH1, f"Q_{w}.parquet"), columns=["molecule", "n_p"])
        U2 = pd.read_parquet(os.path.join(FH2, f"U2_{w}.parquet"), columns=["molecule", "key", "in_P", "rP", "in_E25", "in_Ewin", "e2_rank", "f_rank", "in_F_pool"])
        Q2 = pd.read_parquet(os.path.join(FH2, f"Q2_{w}.parquet"), columns=["molecule", "n_e", "n_e25", "n_u2", "f_applied", "f_top25"])
        E = pd.read_parquet(os.path.join(V2, w, f"e2s_{b}.parquet"), columns=["molecule", "official_key", "e2_rank", "n_e"])
        L = pd.read_csv(os.path.join(V2, w, f"ewin_molecules_{b}.csv"), usecols=["molecule", "n_e"], dtype={"molecule": str})
        B = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv"), usecols=["molecule"], dtype={"molecule": str})
        for D in (U1, Q1, U2, Q2, E): D["molecule"] = D.molecule.astype(str)
        mols = list(Q1.molecule); q2 = Q2.set_index("molecule"); led = L.set_index("molecule")
        ok_r = (set(mols) == set(Q2.molecule) == set(L.molecule) == set(B.molecule)) and not (Q1.molecule.duplicated().any() or Q2.molecule.duplicated().any() or L.molecule.duplicated().any())
        if not ok_r: fails.append(f"{w}: R rosters differ"); continue
        for m in mols:
            n["q"] += 1; n["R"] += 1
            u1 = U1[U1.molecule == m]; p25 = u1[u1.src == "P"].sort_values("rP").key.astype(str).tolist(); bset = set(u1[u1.src == "B"].key.astype(str))
            e = E[E.molecule == m].sort_values("e2_rank"); er = dict(zip(e.official_key.astype(str), e.e2_rank.astype(int))); e25 = e.official_key.astype(str).tolist()[:25]
            u2 = U2[U2.molecule == m]
            if set(u2.key.astype(str)) == set(p25) | bset | set(e25) and set(u2[u2.in_E25 == 1].key.astype(str)) == set(e25): n["S"] += 1
            else: fails.append(f"{w} {m}: S U2 != P25 | E25 | B")
            ne = int(q2.loc[m, "n_e"])
            if (u2[u2.in_P == 1].sort_values("rP").key.astype(str).tolist() == p25 and int(led.loc[m, "n_e"]) == ne == len(e)
                    and e.e2_rank.astype(int).tolist() == list(range(1, ne + 1))): n["O"] += 1
            else: fails.append(f"{w} {m}: O P order / E ledger")
            f = [] if not p25 else (list(p25) if not e25 else E2M.fuse_rrf(p25, er, e25, 0.5))
            fr = u2[u2.f_rank <= 25].sort_values("f_rank").key.astype(str).tolist()
            if f[:25] == json.loads(q2.loc[m, "f_top25"]) == fr: n["F"] += 1
            else: fails.append(f"{w} {m}: F list differs")
    print(f"X160_ECHECK {'PASS' if not fails else 'FAIL'}: {n['q']} e-world queries (6 worlds, pi3 0.3); rosters {n['R']}, U2 = P25|E25|B {n['S']}, "
          f"P order + E ledger {n['O']}, F list {n['F']}; failures {len(fails)} (no label, class, family, reach or metric was read)")
    for x in fails[:10]: print("  -", x)
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
