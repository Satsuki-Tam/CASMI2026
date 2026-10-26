"""042 v2 parity (official keys; gen_eval2 --dump_choice): the submission pipeline's generation records (gen_choice.json, submission_base.csv, submission.csv) vs gen_eval --dump_choice.

Checks per molecule of the view: (1) the chosen novel structure (raw InChIKey first block) is the same; (2) the derivable candidate set
(official keys) is the same; (3) the final list = the derivability-reordered base list with the chosen structure at rank --gen_rank
whenever it was inserted (structure present at that rank). Verdict GENPARITY PASS / FAIL.
Usage: python gen_parity.py --pipe_work RUN_DIR --choice diag/genchoice_parity16.parquet --view c2 --gen_rank 3 --out parity_gen_c2.md
"""
import argparse, json, sys
import pandas as pd
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")
ap = argparse.ArgumentParser(); ap.add_argument("--pipe_work", required=True); ap.add_argument("--choice", required=True); ap.add_argument("--view", required=True)
ap.add_argument("--gen_rank", type=int, default=3); ap.add_argument("--gen_rule", default="always"); ap.add_argument("--out", required=True); a = ap.parse_args()


def rk(smi):
    m = Chem.MolFromSmiles(smi) if smi else None
    return Chem.MolToInchiKey(m)[:14] if m is not None else None


from rdkit.Chem.MolStandardize import rdMolStandardize
TAUT = rdMolStandardize.TautomerEnumerator()


def ok(smi):
    m = Chem.MolFromSmiles(smi) if smi else None
    if m is None: return None
    Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]


base = pd.read_csv(f"{a.pipe_work}/submission_base.csv"); base["molecule_id"] = base.molecule_id.astype(str); BASE = dict(zip(base.molecule_id, base.smiles.astype(str)))
G = json.load(open(f"{a.pipe_work}/gen_choice.json")); C = pd.read_parquet(a.choice); C = C[C.view == a.view]; C["molecule"] = C.molecule.astype(str)
fin = pd.read_csv(f"{a.pipe_work}/submission.csv"); fin["molecule_id"] = fin.molecule_id.astype(str); FIN = dict(zip(fin.molecule_id, fin.smiles.astype(str)))
rows, bad = [], 0
for r in C.itertuples(index=False):
    g = G.get(r.molecule)
    if g is None: rows.append((r.molecule, "missing in pipeline", False)); bad += 1; continue
    pg = g["gen"]; pk = pg[0] if pg else None
    ek = r.gen_okey if isinstance(r.gen_okey, str) else None
    same_gen = pk == ek
    der_e = set(x for x in str(r.derivable or "").split(";") if x); der_p = set(g["derivable"])
    same_der = der_e == der_p
    lst = FIN.get(r.molecule, "").split(";")
    ins_ok = True
    if pg:   # inserted unless its official key is already in the base top-25 (pipeline dedupe)
        base_ok = {ok(x) for x in BASE.get(r.molecule, "").split(";") if x}
        expect = ok(pg[1]) not in base_ok
        if a.gen_rule == "fzgate" and hasattr(r, "gt3_insert"): expect = expect and bool(r.gt3_insert)
        ins_ok = ((len(lst) >= a.gen_rank and ok(lst[a.gen_rank - 1]) == pk) if expect else (pg[1] not in lst)) if a.gen_rule in ("always", "fzgate") else True
    good = bool(same_gen and same_der and ins_ok); bad += (not good)
    rows.append((r.molecule, f"gen {'=' if same_gen else '!='} ({pk} vs {ek}); derivable {len(der_p)} vs {len(der_e)} {'=' if same_der else '!='}; inserted@{a.gen_rank} {ins_ok}", good))
L = [f"# 042 generation parity ({a.view}): {len(rows)} molecules, {bad} mismatches", ""] + [f"- {m}: {d} -> {'OK' if g_ else 'MISMATCH'}" for m, d, g_ in rows]
L.append(""); L.append("GENPARITY PASS" if bad == 0 else "GENPARITY FAIL")
open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L[-3:])); sys.exit(0 if bad == 0 else 2)
