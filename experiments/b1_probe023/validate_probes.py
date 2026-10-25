"""Codex 023b: validate the class-decomposition probe lists of one pipeline run in evaluation mode (masks + solution).
Uses only the run's own outputs: submission.csv (main), submission_probe_{train,nontrain,coconut,pubchem,pool}.csv, b1_candidates.parquet (per
shortlist candidate: official key, smiles, in_train, in_coconut, in_tier as seen by the run, after the evaluation masks), eval_per_molecule.csv (RR of
each list by the official scorer replica) and the molecules CSV (scorer_key of the truth). Checks, per molecule:
  1. every SMILES of a probe list belongs to that probe's group (T = in_train; C = in_coconut; pool = T or C; Pc = neither; N = not T);
  2. the main top-25 restricted to a group is a prefix of that group's probe list (same full order, then cut);
  3. groups pool / Pc and T / N partition the candidates (disjoint; every main item is in exactly one of each pair);
  4. RR relations: truth in group g -> RR_g >= RR_main; truth not in g -> RR_g = 0; empty lists are 'CCO' and counted;
  5. Pc candidates are all PubChem-tier entries (in_tier) and no candidate lacks a membership flag.
Usage: python -X utf8 validate_probes.py --run DIR --molecules CSV --view c1|c2
"""
import argparse, json
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--molecules", required=True); ap.add_argument("--view", required=True); a = ap.parse_args()
G = ("train", "nontrain", "coconut", "pubchem", "pool")
cand = pd.read_parquet(f"{a.run}/b1_candidates.parquet"); cand["molecule"] = cand.molecule.astype(str)
for c in ("in_train", "in_coconut", "in_tier"): assert cand[c].notna().all(), f"missing flag {c}"
fl = {(m, s): (bool(t), bool(c), bool(ti), k) for m, s, t, c, ti, k in zip(cand.molecule, cand.smiles, cand.in_train, cand.in_coconut, cand.in_tier, cand.key)}
def grp_of(t, c): return {"train": t, "nontrain": not t, "coconut": (not t) and c, "pubchem": (not t) and not c, "pool": t or c}
lists = {"main": pd.read_csv(f"{a.run}/submission.csv")}
for g in G: lists[g] = pd.read_csv(f"{a.run}/submission_probe_{g}.csv")
L = {n: dict(zip(d.molecule_id.astype(str), d.smiles.astype(str))) for n, d in lists.items()}
ids = sorted(L["main"]); assert all(sorted(L[g]) == ids for g in G), "probe files do not cover the same molecules"
per = pd.read_csv(f"{a.run}/eval_per_molecule.csv"); per["molecule_id"] = per.molecule_id.astype(str); per = per.set_index("molecule_id")
mol = pd.read_csv(a.molecules); tkey = dict(zip(mol.molecule.astype(str), mol.scorer_key.astype(str)))
viol = {k: 0 for k in ("membership", "prefix", "partition", "rr_in_group", "rr_out_group", "pc_not_tier", "unknown_smiles")}
stats = dict(n=len(ids), empty={g: 0 for g in G}, truth_group={}, rescued={g: 0 for g in G}, examples=[])
for m in ids:
    main = [x for x in L["main"][m].split(";") if x]
    for x in main:
        if (m, x) not in fl and x != "CCO": viol["unknown_smiles"] += 1
    tk = tkey.get(m); trow = cand[(cand.molecule == m) & (cand.key == tk)]
    t_in, c_in = (bool(trow.in_train.iloc[0]), bool(trow.in_coconut.iloc[0])) if len(trow) else (None, None)
    tg = "absent" if t_in is None else ("T" + ("&C" if c_in else "")) if t_in else ("C-only" if c_in else "Pc")
    stats["truth_group"][tg] = stats["truth_group"].get(tg, 0) + 1
    for g in G:
        pl_ = [x for x in L[g][m].split(";") if x]
        if pl_ == ["CCO"]: stats["empty"][g] += 1; pl_ = []
        for x in pl_:
            if (m, x) not in fl: viol["unknown_smiles"] += 1; continue
            t, c, ti, _ = fl[(m, x)]
            if not grp_of(t, c)[g]: viol["membership"] += 1
            if g == "pubchem" and not ti: viol["pc_not_tier"] += 1
        sub = [x for x in main if (m, x) in fl and grp_of(*fl[(m, x)][:2])[g]]
        if pl_[:len(sub)] != sub: viol["prefix"] += 1
        rr_g, rr_m = float(per.loc[m, f"rr_probe_{g}"]), float(per.loc[m, "rr"])
        if t_in is not None and grp_of(t_in, c_in)[g]:
            if rr_g + 1e-12 < rr_m: viol["rr_in_group"] += 1
            if rr_m == 0 and rr_g > 0: stats["rescued"][g] += 1
        elif rr_g != 0: viol["rr_out_group"] += 1
    for a_, b_ in (("pool", "pubchem"), ("train", "nontrain")):
        A = set(x for x in L[a_][m].split(";") if x and x != "CCO"); Bs = set(x for x in L[b_][m].split(";") if x and x != "CCO")
        if A & Bs: viol["partition"] += 1
        for x in main:   # a main top-25 item keeps a rank <= 25 inside its own group, so it must appear in exactly one list of the pair
            if (m, x) in fl and ((x in A) == (x in Bs)): viol["partition"] += 1
mrr = {n: round(float(per[c].mean()), 4) for n, c in [("main", "rr")] + [(g, f"rr_probe_{g}") for g in G]}
print(json.dumps(dict(view=a.view, run=a.run, mrr=mrr, violations=viol, **stats), indent=None))
print("VALIDATION", "PASS" if not any(viol.values()) else "FAIL", a.view)
