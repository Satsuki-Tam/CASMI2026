"""145 E2 commit-run check (the (C) check of 144 v2 / 145; written before the commit run is read). Exit code 0 only when every check passes.
(1) The main list P of the E2 commit run (submission_pref.csv) must reproduce the v8w7a commit runs already on disk (kernels/b1-probe-tv8w7a/output_v1
    and b1-probe-bv8w7a/output_v1: the same recipe, the same 12 smoke molecules): sha256 of the re-serialised list equal to the reference's
    submission_meta.json files['submission.csv']; fixed / probe lists equal per molecule id.
(2) Run conditions: pipeline rc 0; arguments = the reference arguments + exactly the registered E2 arguments (--e2_model e2_lgb.txt --e2_model_sha SHA
    --e2_hedge 0|1); embedded sources / model / FPNet checkpoint equal to the reference except b1_pipeline.py (= experiments/b1_e2k) and the added
    e2_engine.py / e2_common.py (= experiments/b1_e2k); the manifest's E2 block (model sha as given, K 10, alpha 0.5, hedge, inputs under /kaggle/input,
    molecules = e2_stats rows); the E2_RECORD and E2_RDKIT (2026.03.3) lines present; no learned_failed.
(3) Output sanity of F / H and P: unique ids = the sample ids, no empty SMILES, at most 25 candidates; lists differ only for molecules that went
    through E2 with a non-empty E2 list.
Descriptive: lists / rank-1 changed on the smoke molecules, E2 failures.
Usage: python -X utf8 kernels/check_e2k_commit.py kernels/b1-e2f/output_v1 F experiments/e2/model_v1/e2_lgb.txt"""
import hashlib, io, json, os, sys
import pandas as pd
out, VAR, MODEL = sys.argv[1], sys.argv[2], sys.argv[3]; REF = ["kernels/b1-probe-tv8w7a/output_v1", "kernels/b1-probe-bv8w7a/output_v1"]
_sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
_shat = lambda p: hashlib.sha256(open(p, encoding="utf-8").read().encode()).hexdigest()   # the builder hashes the embedded text
PIPE_SHA, ENG_SHA, COM_SHA = _shat("experiments/b1_e2k/b1_pipeline.py"), _shat("experiments/b1_e2k/e2_engine.py"), _shat("experiments/b1_e2k/e2_common.py")
EM_SHA = _sha(MODEL); HEDGE = 1 if VAR == "H" else 0
EXTRA = ["--e2_model", "e2_lgb.txt", "--e2_model_sha", EM_SHA, "--e2_hedge", str(HEDGE)]
ok = True


def fail(msg):
    global ok; ok = False; print("FAIL:", msg)


def load(p):
    s = pd.read_csv(p, dtype=str, keep_default_na=False)
    if not s.molecule_id.is_unique: fail(f"{p}: duplicate ids")
    bad = s.smiles.map(lambda x: x == "" or len(x.split(";")) > 25 or any(t == "" for t in x.split(";")))
    if bad.any(): fail(f"{p}: {int(bad.sum())} rows with empty SMILES or more than 25 candidates")
    return s


mine = {f: load(os.path.join(out, f)) for f in ("submission.csv", "submission_pref.csv", "submission_fixed.csv", "submission_probe_train.csv", "submission_probe_nontrain.csv")}
ids = set(mine["submission.csv"].molecule_id)
for f, s in mine.items():
    if set(s.molecule_id) != ids or len(s) != len(ids): fail(f"{f}: ids differ from submission.csv")
mm = json.load(open(os.path.join(out, "submission_meta.json"))); man = mm["run_manifest"]; el = man.get("e2") or {}
if mm["pipeline_rc"] != 0: fail("pipeline rc")
if mm["embedded_sha256"].get("b1_pipeline.py") != PIPE_SHA: fail(f"embedded b1_pipeline.py {mm['embedded_sha256'].get('b1_pipeline.py')}")
if mm["embedded_sha256"].get("e2_engine.py") != ENG_SHA or mm["embedded_sha256"].get("e2_common.py") != COM_SHA: fail(f"embedded e2 sources {mm['embedded_sha256'].get('e2_engine.py')} / {mm['embedded_sha256'].get('e2_common.py')}")
if el.get("model_sha256") != EM_SHA or el.get("expected_sha_given") is not True: fail(f"E2 model {el.get('model_sha256')} given {el.get('expected_sha_given')}")
if el.get("K") != 10.0 or el.get("alpha") != 0.5 or el.get("hedge") != HEDGE: fail(f"K / alpha / hedge {el.get('K')} / {el.get('alpha')} / {el.get('hedge')}")
if not all(str(el.get(k, "")).startswith("/kaggle/input/") for k in ("model", "bio", "pcl", "structs")): fail(f"E2 inputs not resolved under /kaggle/input: {[el.get(k) for k in ('model', 'bio', 'pcl', 'structs')]}")
if man["params"].get("LAM") != 0.5 or man["params"].get("lam_fixed") is not None: fail("LAM / lam_fixed")
if man.get("fusion", {}).get("learned_failed"): fail("learned_failed present")
es = pd.read_csv(os.path.join(out, "e2_stats.csv"), dtype={"molecule": str})
if el.get("molecules") != len(es): fail(f"E2 molecules {el.get('molecules')} vs e2_stats rows {len(es)}")
args_mine = mm["pipeline_args"]
proc_mine = set(pd.read_csv(os.path.join(out, "b1_stage_stats.csv")).molecule.astype(str))
for r in REF:
    rm = json.load(open(os.path.join(r, "submission_meta.json")))
    ra = rm["pipeline_args"]; i_ = ra.index("--test") if "--test" in ra else len(ra)
    want_args = ra[:i_ - 2] + EXTRA + ra[i_ - 2:] if ra[i_ - 2] == "--limit" else None
    if want_args is None or args_mine != want_args: fail(f"{r}: pipeline arguments differ\n  mine {args_mine}\n  want {want_args}")
    for k in set(rm["embedded_sha256"]) | set(mm["embedded_sha256"]):
        if k not in ("b1_pipeline.py", "e2_engine.py", "e2_common.py") and rm["embedded_sha256"].get(k) != mm["embedded_sha256"].get(k): fail(f"{r}: embedded {k} differs")
    if rm["run_manifest"]["params"].get("fpnet_ckpt_sha256") != man["params"].get("fpnet_ckpt_sha256"): fail(f"{r}: FPNet checkpoint differs")
    if set(pd.read_csv(os.path.join(r, "b1_stage_stats.csv")).molecule.astype(str)) != proc_mine: fail(f"{r}: processed ids differ")
    order = pd.read_csv(os.path.join(r, "submission.csv"), dtype=str, keep_default_na=False).molecule_id.tolist()
    pref = mine["submission_pref.csv"].set_index("molecule_id").smiles
    if set(order) != set(pref.index): fail(f"{r}: id sets differ"); continue
    buf = io.StringIO(); pd.DataFrame({"molecule_id": order, "smiles": [pref[m] for m in order]}).to_csv(buf, index=False, lineterminator="\n")
    h = hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest(); want = rm["files"]["submission.csv"]
    print(f"P (submission_pref) vs {r}: sha256 {h[:16]} want {want[:16]} -> {'equal' if h == want else 'DIFFERENT'}")
    if h != want: fail(f"{r}: main list hash differs")
    for f_m in ("submission_fixed.csv", "submission_probe_train.csv", "submission_probe_nontrain.csv"):
        a = mine[f_m].set_index("molecule_id").smiles; b = pd.read_csv(os.path.join(r, f_m), dtype=str, keep_default_na=False).set_index("molecule_id").smiles
        if set(a.index) != set(b.index): fail(f"{r} {f_m}: ids"); continue
        d = [m for m in a.index if a[m] != b[m]]
        print(f"{f_m} vs {r}: rows {len(a)}, differing {len(d)}")
        if d: fail(f"{f_m} vs {r}: {len(d)} rows differ")
m_ = mine["submission.csv"].set_index("molecule_id").smiles; p_ = mine["submission_pref.csv"].set_index("molecule_id").smiles.loc[m_.index]
ch = [k for k in m_.index if m_[k] != p_[k]]
if not set(ch) <= set(es[es.n_e2 > 0].molecule): fail("a list changed for a molecule without a non-empty E2 list")
print("descriptive: E2 vs P of this run: processed", len(proc_mine), "E2 molecules", len(es), "lists changed", len(ch),
      "rank-1 changed", int(sum(m_[k].split(";")[0] != p_[k].split(";")[0] for k in m_.index)), "| manifest", {k: el.get(k) for k in ("e2_nonempty", "e2_failed", "top1_changed", "top25_changed", "new_keys_mols", "lists_changed")})
logs = [f for f in os.listdir(out) if f.startswith("casmi26-b1-e2") and f.endswith(".log")]
rec = [l for f in logs for l in open(os.path.join(out, f), encoding="utf-8", errors="replace").read().splitlines() if "E2_RECORD" in l]
print("record:", rec[-1][:700] if rec else "MISSING")
if not rec: fail("E2_RECORD line missing")
rdk = [l for f in logs for l in open(os.path.join(out, f), encoding="utf-8", errors="replace").read().splitlines() if "E2_RDKIT" in l]
print("rdkit:", rdk[-1][:400] if rdk else "MISSING")
if not rdk or '\\"version\\": \\"2026.03.3\\"' not in rdk[-1]: fail("E2_RDKIT line missing or not 2026.03.3")
print("E2K_COMMIT_CHECK", VAR, "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
