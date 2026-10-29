"""132 E-lite commit-run check (parity (C) of 132_prereg_elite_public.md; written before the commit run is read). Exit code 0 only when every check passes.
v2 (Codex 132): expected pipeline 930fa3f8 (registered-combination asserts), ELITE_RDKIT line (official-identity RDKit 2026.03.3 + fixture), shas given, inputs resolved under /kaggle/input.
(1) The main list P of the E-lite commit run must reproduce the v8w7a commit runs already on disk (kernels/b1-probe-tv8w7a/output_v1 and
    b1-probe-bv8w7a/output_v1: the same recipe, the same 12 smoke molecules):
    - submission_pref.csv put into the reference run's molecule order, re-serialised with pandas (molecule_id, smiles; UTF-8; LF): sha256 equal to
      the reference's submission_meta.json files['submission.csv'] (the hash of the original v8w7a main list);
    - fixed / probe_train / probe_nontrain lists: content equal per molecule id.
(2) Run conditions: pipeline rc 0; the pipeline arguments = the reference arguments + exactly the registered E-lite arguments; embedded sources /
    model / FPNet checkpoint equal to the reference except b1_pipeline.py (expected 992912ec...) and the added elite.py (expected 4a11a714...);
    processed ids equal; the manifest's E-lite block: model / keys sha256 as registered, K 10, alpha 0.5, molecules = elite_stats rows; the
    ELITE_RECORD line present; no learned_failed.
(3) Output sanity of the E-lite list and P: unique ids = the sample ids, no empty SMILES, at most 25 candidates; lists differ only for molecules
    that went through E-lite.
Descriptive: lists / rank-1 changed by E-lite on the smoke molecules.
Usage: python -X utf8 kernels/check_elite_commit.py kernels/b1-elite/output_v1"""
import hashlib, io, json, os, sys
import pandas as pd
out = sys.argv[1]; REF = ["kernels/b1-probe-tv8w7a/output_v1", "kernels/b1-probe-bv8w7a/output_v1"]
PIPE_SHA, ELITE_SHA = "930fa3f835ecad9d54b5e2822427253c4758337104a32d3506da28252a337536", "4a11a714eb0bfb52070ea66bf15413ed04c7019c2fe41c823f64dada2bad3ed2"
EM_SHA, EK_SHA = "8f4a81b5f8ba7f589cfd74980ea40075169121b2ce1382cb92a1f2aa150ec1f5", "f572682b47a882de18bbe3ded9129fa0544e3c52281447e90f7bc3f13042a672"
EXTRA = ["--elite_model", "elite132_e1r_lambdarank.txt", "--elite_keys", "elite132_e_window_keys_v2.parquet", "--elite_k", "10", "--elite_alpha", "0.5", "--elite_model_sha", EM_SHA, "--elite_keys_sha", EK_SHA]
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
mm = json.load(open(os.path.join(out, "submission_meta.json"))); man = mm["run_manifest"]; el = man.get("elite") or {}
if mm["pipeline_rc"] != 0: fail("pipeline rc")
if mm["embedded_sha256"].get("b1_pipeline.py") != PIPE_SHA: fail(f"embedded b1_pipeline.py {mm['embedded_sha256'].get('b1_pipeline.py')}")
if mm["embedded_sha256"].get("elite.py") != ELITE_SHA: fail(f"embedded elite.py {mm['embedded_sha256'].get('elite.py')}")
if el.get("model_sha256") != EM_SHA or el.get("keys_sha256") != EK_SHA: fail(f"E-lite inputs {el.get('model_sha256')} / {el.get('keys_sha256')}")
if el.get("K") != 10.0 or el.get("alpha") != 0.5: fail(f"K / alpha {el.get('K')} / {el.get('alpha')}")
if el.get("expected_shas_given") is not True or el.get("pcl_boost") or el.get("twin_tau") is not None: fail(f"registered combination: shas given {el.get('expected_shas_given')}, pcl {el.get('pcl_boost')}, twin {el.get('twin_tau')}")
if not str(el.get("model", "")).startswith("/kaggle/input/") or not str(el.get("keys", "")).startswith("/kaggle/input/"): fail(f"E inputs not resolved under /kaggle/input: {el.get('model')} {el.get('keys')}")
if man["params"].get("LAM") != 0.5 or man["params"].get("lam_fixed") is not None: fail("LAM / lam_fixed")
if man.get("fusion", {}).get("learned_failed"): fail("learned_failed present")
es = pd.read_csv(os.path.join(out, "elite_stats.csv"), dtype={"molecule": str})
if el.get("molecules") != len(es): fail(f"E-lite molecules {el.get('molecules')} vs elite_stats rows {len(es)}")
args_mine = mm["pipeline_args"]
proc_mine = set(pd.read_csv(os.path.join(out, "b1_stage_stats.csv")).molecule.astype(str))
for r in REF:
    rm = json.load(open(os.path.join(r, "submission_meta.json")))
    ra = rm["pipeline_args"]; i_ = ra.index("--test") if "--test" in ra else len(ra)
    want_args = ra[:i_ - 2] + EXTRA + ra[i_ - 2:] if ra[i_ - 2] == "--limit" else None
    if want_args is None or args_mine != want_args: fail(f"{r}: pipeline arguments differ\n  mine {args_mine}\n  want {want_args}")
    for k in set(rm["embedded_sha256"]) | set(mm["embedded_sha256"]):
        if k not in ("b1_pipeline.py", "elite.py") and rm["embedded_sha256"].get(k) != mm["embedded_sha256"].get(k): fail(f"{r}: embedded {k} differs")
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
if not set(ch) <= set(es.molecule): fail("a list changed for a molecule that did not go through E-lite")
print("descriptive: E-lite vs P of this run: processed", len(proc_mine), "E-lite molecules", len(es), "lists changed", len(ch),
      "rank-1 changed", int(sum(m_[k].split(";")[0] != p_[k].split(";")[0] for k in m_.index)), "| manifest", {k: el.get(k) for k in ("e_nonempty", "e_size_median", "cand_median", "top1_changed", "lists_changed")})
logs = [f for f in os.listdir(out) if f.startswith("casmi26-b1-elite") and f.endswith(".log")]
rec = [l for f in logs for l in open(os.path.join(out, f), encoding="utf-8", errors="replace").read().splitlines() if "ELITE_RECORD" in l]
print("record:", rec[-1][:700] if rec else "MISSING")
if not rec: fail("ELITE_RECORD line missing")
rdk = [l for f in logs for l in open(os.path.join(out, f), encoding="utf-8", errors="replace").read().splitlines() if "ELITE_RDKIT" in l]
print("rdkit:", rdk[-1][:400] if rdk else "MISSING")
if not rdk or '\\"version\\": \\"2026.03.3\\"' not in rdk[-1]: fail("ELITE_RDKIT line missing or not 2026.03.3")
print("ELITE_COMMIT_CHECK", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
