"""pop0 commit-run check (written before the kernel is pushed; strengthened after Codex 126). Exit code 0 only when every check passes.
(1) The frozen-LAM reference lists of the pop0 commit run must reproduce the v8w7a commit runs already on disk (kernels/b1-probe-tv8w7a/output_v1
    and b1-probe-bv8w7a/output_v1: the same notebook, the same 12 smoke molecules):
    - MAIN list, byte level: submission_lamref.csv is put into the reference run's molecule order (its extracted submission.csv keeps the original
      order), re-serialised with pandas (molecule_id, smiles; UTF-8; LF) and its sha256 must equal the reference's submission_meta.json
      files['submission.csv'] (written BEFORE the group extraction, i.e. the hash of the original v8w7a main list);
    - fixed / probe_train / probe_nontrain lists: content equal per molecule id (file order differs between runs: polars unique()).
(2) Run conditions: pipeline rc 0; params lam_fixed == 0.0 and LAM == 0.5; the embedded sources / model / FPNet checkpoint hashes and every
    pipeline argument except --lam_fixed equal to the reference runs'; processed ids (b1_stage_stats.csv) equal to the reference runs'; the
    POP0_RECORD line present; both passes with the same learned / fallback counts and no learned_failed.
(3) Output sanity of all five lists: unique ids = the sample ids, no empty / missing SMILES, at most 25 candidates.
Descriptive: how many pop0 lists / rank-1 differ from the frozen-LAM main of the same run.
Usage: python -X utf8 kernels/check_pop0_commit.py kernels/b1-pop0/output_v1"""
import hashlib, io, json, os, sys
import pandas as pd
out = sys.argv[1]; REF = ["kernels/b1-probe-tv8w7a/output_v1", "kernels/b1-probe-bv8w7a/output_v1"]
ok = True
def fail(msg):
    global ok; ok = False; print("FAIL:", msg)
def load(p):
    s = pd.read_csv(p, dtype=str, keep_default_na=False)
    if not s.molecule_id.is_unique: fail(f"{p}: duplicate ids")
    bad = s.smiles.map(lambda x: x == "" or len(x.split(";")) > 25 or any(t == "" for t in x.split(";")))
    if bad.any(): fail(f"{p}: {int(bad.sum())} rows with empty SMILES or more than 25 candidates")
    return s
mine = {f: load(os.path.join(out, f)) for f in ("submission.csv", "submission_lamref.csv", "submission_lamref_fixed.csv", "submission_lamref_probe_train.csv", "submission_lamref_probe_nontrain.csv")}
ids = set(mine["submission.csv"].molecule_id)
for f, s in mine.items():
    if set(s.molecule_id) != ids or len(s) != len(ids): fail(f"{f}: ids differ from submission.csv")
mm = json.load(open(os.path.join(out, "submission_meta.json"))); man = mm["run_manifest"]
if mm["pipeline_rc"] != 0: fail("pipeline rc")
if man["params"].get("lam_fixed") != 0.0 or man["params"].get("LAM") != 0.5: fail(f"lam_fixed / LAM {man['params'].get('lam_fixed')} / {man['params'].get('LAM')}")
fu, fr = man.get("fusion", {}), man.get("fusion_lamref", {})
for k in ("learned", "fallback_gl_cover", "gl_used", "empty", "analog", "frag"):
    if fu.get(k, 0) != fr.get(k, 0): fail(f"fusion count {k} differs between passes: {fu.get(k)} vs {fr.get(k)}")
if fu.get("learned_failed") or fr.get("learned_failed"): fail("learned_failed present")
args_mine = [a for i, a in enumerate(mm["pipeline_args"]) if a != "--lam_fixed" and not (i > 0 and mm["pipeline_args"][i - 1] == "--lam_fixed")]
proc_mine = set(pd.read_csv(os.path.join(out, "b1_stage_stats.csv")).molecule.astype(str))
for r in REF:
    rm = json.load(open(os.path.join(r, "submission_meta.json")))
    if rm["pipeline_args"] != args_mine: fail(f"{r}: pipeline arguments differ {rm['pipeline_args']} vs {args_mine}")
    for k in set(rm["embedded_sha256"]) | set(mm["embedded_sha256"]):
        if k != "b1_pipeline.py" and rm["embedded_sha256"].get(k) != mm["embedded_sha256"].get(k): fail(f"{r}: embedded {k} differs")
    if rm["run_manifest"]["params"].get("fpnet_ckpt_sha256") != man["params"].get("fpnet_ckpt_sha256"): fail(f"{r}: FPNet checkpoint differs")
    if set(pd.read_csv(os.path.join(r, "b1_stage_stats.csv")).molecule.astype(str)) != proc_mine: fail(f"{r}: processed ids differ")
    order = pd.read_csv(os.path.join(r, "submission.csv"), dtype=str, keep_default_na=False).molecule_id.tolist()
    lam = mine["submission_lamref.csv"].set_index("molecule_id").smiles
    if set(order) != set(lam.index): fail(f"{r}: id sets differ"); continue
    buf = io.StringIO(); pd.DataFrame({"molecule_id": order, "smiles": [lam[m] for m in order]}).to_csv(buf, index=False, lineterminator="\n")
    h = hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest(); want = rm["files"]["submission.csv"]
    print(f"main list vs {r}: sha256 {h[:16]} want {want[:16]} -> {'equal' if h == want else 'DIFFERENT'}")
    if h != want: fail(f"{r}: main list hash differs")
    for f_m, f_r in (("submission_lamref_fixed.csv", "submission_fixed.csv"), ("submission_lamref_probe_train.csv", "submission_probe_train.csv"),
                     ("submission_lamref_probe_nontrain.csv", "submission_probe_nontrain.csv")):
        a = mine[f_m].set_index("molecule_id").smiles; b = pd.read_csv(os.path.join(r, f_r), dtype=str, keep_default_na=False).set_index("molecule_id").smiles
        if set(a.index) != set(b.index): fail(f"{r} {f_r}: ids"); continue
        d = [m for m in a.index if a[m] != b[m]]
        print(f"{f_m} vs {r}/{f_r}: rows {len(a)}, processed {len(proc_mine)}, differing {len(d)}")
        if d: fail(f"{f_m} vs {r}: {len(d)} rows differ")
m_ = mine["submission.csv"].set_index("molecule_id").smiles; r_ = mine["submission_lamref.csv"].set_index("molecule_id").smiles.loc[m_.index]
print("descriptive: pop0 vs frozen-LAM main of this run: processed", len(proc_mine), "lists changed", int(sum(m_[k] != r_[k] for k in proc_mine)),
      "rank-1 changed", int(sum(m_[k].split(";")[0] != r_[k].split(";")[0] for k in proc_mine)))
logs = [f for f in os.listdir(out) if f.startswith("casmi26-b1-pop0") and f.endswith(".log")]
rec = [l for f in logs for l in open(os.path.join(out, f), encoding="utf-8", errors="replace").read().splitlines() if "POP0_RECORD" in l]
print("record:", rec[-1][:600] if rec else "MISSING")
if not rec: fail("POP0_RECORD line missing")
print("POP0_COMMIT_CHECK", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
