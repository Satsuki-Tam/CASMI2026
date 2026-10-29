"""W135 class correction (Codex 136 Q2 (a); before any reach number): rewrite the batch CSVs with C1 eligibility from the world rule
(w135_c1audit.py output) and re-apply the registered hash-order assignment (C3 nested and unchanged; C1 = first floor(rest / 2) world-eligible
in hash order; others C2). The original CSVs move to experiments/w135/batches/v1/ (kept); the corrected ones replace them under the same
names, with columns c1_eligible_world / n_ref_after_world_mask added; a v2 manifest records both hashes.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_reclass.py --audit experiments/w135/c1audit/d.parquet --batches dF1 ... --tag d"""
import argparse, hashlib, json, os, shutil, sys
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--audit", required=True); ap.add_argument("--batches", nargs="+", required=True); ap.add_argument("--tag", required=True); a = ap.parse_args()
H = lambda s: hashlib.sha256(s.encode()).hexdigest(); sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest(); PIS = (0.0, 0.3, 0.6)
BD = os.path.join(ROOT, "experiments/w135/batches"); V1 = os.path.join(BD, "v1"); os.makedirs(V1, exist_ok=True)
A = pd.read_parquet(os.path.join(ROOT, a.audit) if not os.path.isabs(a.audit) else a.audit); A["molecule"] = A.molecule.astype(str)
man = dict(tag=a.tag, audit=a.audit, audit_sha256=sha(os.path.join(ROOT, a.audit)), script_sha256=sha(os.path.abspath(__file__)), batches={})
for b in a.batches:
    src = os.path.join(BD, f"{b}.csv"); dst_v1 = os.path.join(V1, f"{b}.csv")
    if os.path.exists(dst_v1): sys.exit(f"REFUSED: {dst_v1} exists (already corrected)")
    bt = pd.read_csv(src); bt["molecule"] = bt.molecule.astype(str); ab = A[A.batch == b].set_index("molecule")
    if set(ab.index) != set(bt.molecule): sys.exit(f"{b}: audit rows differ from the batch")
    el = {m: bool(ab.loc[m, "c1_eligible_world"]) for m in bt.molecule}
    ms = sorted(bt.molecule, key=lambda m: H(f"w135cls|{b}|{m}")); N = len(ms); new = {}
    for p in PIS:
        n3 = int(round(p * N)); rest = ms[n3:]; n1 = len(rest) // 2; c1 = set([m for m in rest if el[m]][:n1])
        new[p] = {m: ("C3" if i < n3 else ("C1" if m in c1 else "C2")) for i, m in enumerate(ms)}
        old3 = set(bt.molecule[bt[f"wclass_p{int(p * 100)}"] == "C3"]); new3 = {m for m, c in new[p].items() if c == "C3"}
        assert old3 == new3, (b, p, "C3 set changed")
    out = bt.copy()
    for p in PIS: out[f"wclass_p{int(p * 100)}"] = out.molecule.map(new[p])
    out["c1_eligible_world"] = out.molecule.map(el); out["n_ref_after_world_mask"] = out.molecule.map(lambda m: int(ab.loc[m, "n_ref_after_world_mask"]))
    out = out.set_index("molecule").loc[ms].reset_index()   # hash order, as the original
    shutil.move(src, dst_v1); out.to_csv(src, index=False)
    man["batches"][b] = dict(v1_sha256=sha(dst_v1), v2_sha256=sha(src), changed={f"p{int(p * 100)}": int((bt.set_index("molecule")[f"wclass_p{int(p * 100)}"].reindex(out.molecule).values != out[f"wclass_p{int(p * 100)}"].values).sum()) for p in PIS},
                             classes={f"p{int(p * 100)}": {k: int((out[f"wclass_p{int(p * 100)}"] == k).sum()) for k in ("C1", "C2", "C3")} for p in PIS})
json.dump(man, open(os.path.join(BD, f"{a.tag}_manifest_v2.json"), "w"), indent=1); print(json.dumps(man, indent=1))
