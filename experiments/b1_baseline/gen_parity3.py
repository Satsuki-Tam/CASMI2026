"""044 ggt3 parity: the pipeline's generated-structure GL decision (gen_choice.json "ggt3") vs gen_eval3 --dump_choice (same base GL and
generated GL through --gl_base_json / --gl_gen_json = mechanical check). Per molecule of the view: GL rule used (scale valid and a top-K
generated structure with finite GL), the chosen official key, the insertion decision, and the final list (the chosen structure at rank 3
iff inserted; otherwise the gt3 gate decides and gen_parity2 covers it). Verdict GGT3PARITY PASS / FAIL.
Usage: python gen_parity3.py --pipe_work RUN --choice diag/genchoice3_x.parquet --view c2 --out parity_ggt3_c2.md
"""
import argparse, json, sys
import pandas as pd
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import b1_gen as BG
ap = argparse.ArgumentParser(); ap.add_argument("--pipe_work", required=True); ap.add_argument("--choice", required=True); ap.add_argument("--view", required=True)
ap.add_argument("--gen_rank", type=int, default=3); ap.add_argument("--out", required=True); a = ap.parse_args()
G = json.load(open(f"{a.pipe_work}/gen_choice.json")); C = pd.read_parquet(a.choice); C = C[C.view == a.view]; C["molecule"] = C.molecule.astype(str)
fin = pd.read_csv(f"{a.pipe_work}/submission.csv"); FIN = dict(zip(fin.molecule_id.astype(str), fin.smiles.astype(str)))
rows, bad, n_gl, n_ins = [], 0, 0, 0
for r in C.itertuples(index=False):
    g = (G.get(r.molecule) or {}).get("ggt3")
    e_gl = bool(r.ggt3_gl) if r.ggt3_gl is not None else False
    p_gl = bool(g["gl"]) if g else False
    if not e_gl and not p_gl: continue          # gt3 path on both sides (gen_parity2 covers it)
    n_gl += 1
    same = (e_gl == p_gl) and (str(r.ggt3_okey) == str(g["okey"]) if g else False) and (bool(r.ggt3_insert) == bool(g["insert"]) if g else False)
    lst = FIN.get(r.molecule, "").split(";")
    ins_ok = True
    if g and g["insert"]:
        n_ins += 1; ins_ok = len(lst) >= a.gen_rank and BG.official_key(lst[a.gen_rank - 1]) == g["okey"]
    good = bool(same and ins_ok); bad += (not good)
    rows.append((r.molecule, f"gl {e_gl}/{p_gl} okey {r.ggt3_okey}/{g['okey'] if g else None} insert {r.ggt3_insert}/{g['insert'] if g else None} final@{a.gen_rank} {ins_ok}", good))
L = [f"# 044 ggt3 parity ({a.view}): {n_gl} molecules on the GL rule, {n_ins} insertions, {bad} mismatches", ""] + [f"- {m}: {d} -> {'OK' if g_ else 'MISMATCH'}" for m, d, g_ in rows]
L.append(""); L.append("GGT3PARITY PASS" if (bad == 0) else "GGT3PARITY FAIL")
open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L[:1] + L[-1:])); sys.exit(0 if bad == 0 else 2)
