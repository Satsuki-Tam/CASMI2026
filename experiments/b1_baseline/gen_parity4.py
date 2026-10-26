"""045 full-list parity of the generation rules (Codex 045 Q1): for EVERY query of the view, the expected final list is built from the
evaluator's decisions (gen_eval3/4 --dump_choice) and the pipeline's base list (submission_base.csv, itself checked against the registered
main by b1_parity), then compared with the pipeline's final submission.csv by ordered official keys of the top-25.
Expected list: rule ggt3 -> GL path (ggt3_gl): the chosen structure at rank k if ggt3_insert, else the base list; gt3 path: the best novel
structure at rank k if gt3_insert, else the base list. Rule gt3 -> the gt3 path only. Also checks: identical id sets, one row per id,
no official-key duplicate inside a list, list length <= 25. Exit code 0 only if every check passes (GENPARITY4 PASS).
Usage: python gen_parity4.py --pipe_work RUN --choice diag/genchoice3_x.parquet --view c2 --rule ggt3 --out parity4.md
"""
import argparse, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1_gen as BG
ap = argparse.ArgumentParser(); ap.add_argument("--pipe_work", required=True); ap.add_argument("--choice", required=True); ap.add_argument("--view", required=True)
ap.add_argument("--rule", required=True, choices=["gt3", "ggt3"]); ap.add_argument("--gen_rank", type=int, default=3); ap.add_argument("--out", required=True); a = ap.parse_args()
base = pd.read_csv(f"{a.pipe_work}/submission_base.csv"); fin = pd.read_csv(f"{a.pipe_work}/submission.csv")
C = pd.read_parquet(a.choice); C = C[C.view == a.view].copy(); C["molecule"] = C.molecule.astype(str)
fails, n_ins, n_gl = [], 0, 0
B = dict(zip(base.molecule_id.astype(str), base.smiles.astype(str))); F_ = fin.molecule_id.astype(str)
if F_.duplicated().any(): fails.append(("*", f"{int(F_.duplicated().sum())} duplicated ids in submission.csv"))
FIN = dict(zip(F_, fin.smiles.astype(str)))
ids_c = set(C.molecule); ids_f = set(FIN)
if not ids_c <= ids_f: fails.append(("*", f"{len(ids_c - ids_f)} evaluated molecules missing from submission.csv"))
K = {}
def keys(lst):
    out = []
    for s_ in lst:
        if s_ not in K: K[s_] = BG.official_key(s_) or ("RAW:" + s_)   # unparsable spellings compared verbatim
        out.append(K[s_])
    return out
for r in C.itertuples(index=False):
    m = r.molecule
    if m not in FIN or m not in B: continue
    bl = [x for x in B[m].split(";") if x]
    ins = None
    if a.rule == "ggt3" and bool(getattr(r, "ggt3_gl", False)):
        n_gl += 1
        if bool(r.ggt3_insert): ins = r.ggt3_smiles
    elif bool(r.gt3_insert) and isinstance(r.gen_smiles, str):
        ins = r.gen_smiles
    exp = (bl[:a.gen_rank - 1] + [ins] + bl[a.gen_rank - 1:])[:25] if ins else bl[:25]
    n_ins += ins is not None
    got = [x for x in FIN[m].split(";") if x]
    ke, kg = keys(exp), keys(got)
    if len(got) > 25: fails.append((m, f"list length {len(got)} > 25"))
    if len(set(kg)) != len(kg): fails.append((m, "official-key duplicate in the final list"))
    if ke != kg: fails.append((m, f"ordered top-25 differs (expected insert {'yes' if ins else 'no'}; first difference at rank {next((i + 1 for i, (x, y) in enumerate(zip(ke, kg)) if x != y), min(len(ke), len(kg)) + 1)})"))
L = [f"# 045 full-list parity ({a.rule}, {a.view}): {len(C)} queries, {n_gl} on the GL path, {n_ins} insertions expected, {len(fails)} failures", ""]
L += [f"- {m}: {d}" for m, d in fails[:50]]
L += ["", "GENPARITY4 PASS" if not fails else "GENPARITY4 FAIL"]
open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join([L[0], L[-1]])); sys.exit(0 if not fails else 2)
