"""Build (not push) the 145 E2 kernels (144_prereg_e2.md v2): the v8w7a kernel recipe (make_b1_notebook.py, same ranker / arguments / smoke /
checkpoint check) with the sources of experiments/b1_e2k (pop0 pipeline + the read-only E2 engine and the F / H hook; e2_engine.py and
e2_common.py embedded) and the E2 arguments. The E2 model comes from the private dataset hayatetaf/casmi26-e2-model (found by file name under
/kaggle/input; sha256 checked by the pipeline). submission.csv = F (casmi26-b1-e2f) or H (casmi26-b1-e2h); submission_pref.csv = P (v8w7a).
Cells: RDKIT (official-identity RDKit 2026.03.3 + the 132 fixture, as the E2 keys were built with it) -> pipeline -> RECORD (manifest E2 block:
model sha given and matching, K 10, alpha 0.5, the hedge flag of this kernel, inputs resolved under /kaggle/input; e2_stats molecules = the
processed molecules with candidates; lists change only where E2 ran and was non-empty; prints E2_RECORD).
v2 (Codex 146): the RECORD cell also asserts the E2 index sha / unmapped 0, the model features / trees, and at most 8 E2 failures (2% of 400;
the hidden rerun's logs are invisible, so a stop on any single failure would lose the slot without a diagnosis, while <= 8 fallbacks to P
move the F reading by <= ~0.002, far inside the registered +-0.015 band; the commit-run check requires 0).
Usage: python -X utf8 kernels/make_b1_e2k.py --variant F|H --model experiments/e2/model_v1/e2_lgb.txt"""
import argparse, hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument("--variant", choices=["F", "H"], required=True); ap.add_argument("--model", required=True); A = ap.parse_args()
SHA = hashlib.sha256(open(A.model, "rb").read()).hexdigest(); HEDGE = 1 if A.variant == "H" else 0
IDX_SHA = hashlib.sha256(open(os.path.join(os.path.dirname(A.model), "e2_ik14_to_scorer.parquet"), "rb").read()).hexdigest()
sys.path.insert(0, os.path.join(ROOT, "experiments", "e2")); from e2_common import FEATS   # v2: the record cell checks the E2 features
name = f"casmi26-b1-e2{A.variant.lower()}"; out = os.path.join(HERE, f"b1-e2{A.variant.lower()}"); os.makedirs(out, exist_ok=True); nbp = os.path.join(out, f"{name}.ipynb")
ARGS = "--k_fpp 200 --k_pop 50 --w_ice 0 --tau 0.9 --main blend21 --gl_budget 14000 --deadline_s 30000 --fpnet_ckpt full_eval_final.pt --analog_w 0 --analog_w_fallback 1 --analog_feat ap --frag_w_fallback 1"
E2A = f"--e2_model e2_lgb.txt --e2_model_sha {SHA} --e2_hedge {HEDGE}"
subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "b1-baseline", "make_b1_notebook.py"), nbp, "--src_dir", os.path.join(ROOT, "experiments", "b1_e2k"),
                "--model", os.path.join(ROOT, "experiments", "b1_baseline", "rank_v8w7a", "lambdarank_stripped.txt"), "--compress", "lzma",
                "--pipeline_args", ARGS + " " + E2A, "--expect_ckpt_sha", "5b8d1c311d1171089374379c10cb82fdcc36457a7ab02ec0dddc6f12059b616d", "--smoke_n", "12"], check=True)
nb = json.load(open(nbp, encoding="utf-8"))
el = json.load(open(os.path.join(HERE, "b1-elite", "casmi26-b1-elite.ipynb"), encoding="utf-8"))
RDK = "".join(el["cells"][1]["source"]).replace("# ==== 132 (Codex 132): the official-identity environment of the pipeline must be RDKit 2026.03.3 (the E keys were built with it) ====",
                                                "# ==== 145 (as 132): the official-identity environment of the pipeline must be RDKit 2026.03.3 (the E2 keys were built with it) ====").replace("ELITE_RDKIT", "E2_RDKIT")
assert "E2_RDKIT" in RDK and "145 (as 132)" in RDK
RECORD = """# ==== 145 E2: record of the run (submission.csv = %s, submission_pref.csv = main list P of the same run) ====
import json as _j, pandas as _p
_m = _j.load(open('/kaggle/working/b1_run_manifest.json')); _e = _m.get('e2') or {}
assert _e.get('model_sha256') == '%s' and _e.get('expected_sha_given') is True, ('E2 model', _e.get('model_sha256'), _e.get('expected_sha_given'))
assert _e.get('K') == 10.0 and _e.get('alpha') == 0.5 and _e.get('hedge') == %d, ('E2 combination', _e.get('K'), _e.get('alpha'), _e.get('hedge'))
assert _e.get('index_sha256') == '%s' and _e.get('index_unmapped_rows') == 0, ('E2 index', _e.get('index_sha256'), _e.get('index_unmapped_rows'))
assert _e.get('feats') == %s and _e.get('trees') == 800, ('E2 model features / trees', _e.get('trees'))
assert _e.get('e2_failed', 10**6) <= 8, ('E2 failed on more than 2%% of the hidden molecules: stop instead of a silently diluted F', _e.get('e2_failed'))   # v2 (Codex 146); <= 8 shifts the F reading by <= ~0.002
assert _m['params'].get('LAM') == 0.5 and _m['params'].get('lam_fixed') is None and _m.get('learned_model'), ('fusion parameters / ranker', _m['params'].get('LAM'), _m['params'].get('lam_fixed'), _m.get('learned_model'))
assert all(str(_e.get(k_, '')).startswith('/kaggle/input/') for k_ in ('model', 'bio', 'pcl', 'structs', 'index')), ('E2 inputs not resolved under /kaggle/input', {k_: _e.get(k_) for k_ in ('model', 'bio', 'pcl', 'structs', 'index')})
_st = _p.read_csv('/kaggle/working/b1_stage_stats.csv', dtype={'molecule': str})
_withc = set(_st[_st['n_shortlist'].fillna(0) > 0].molecule) if 'n_shortlist' in _st.columns else None
_es = _p.read_csv('/kaggle/working/e2_stats.csv', dtype={'molecule': str})
assert _withc is not None and _es.molecule.is_unique and set(_es.molecule) == _withc, ('e2_stats molecules != processed molecules with candidates', len(_es), None if _withc is None else len(_withc))
assert _e.get('molecules') == len(_es), ('manifest E2 molecules', _e.get('molecules'), len(_es))
_s = _p.read_csv('/kaggle/working/submission.csv', dtype=str, keep_default_na=False); _r = _p.read_csv('/kaggle/working/submission_pref.csv', dtype=str, keep_default_na=False)
for _d, _f in ((_s, 'submission.csv'), (_r, 'submission_pref.csv')):
    assert _d.molecule_id.is_unique and set(_d.molecule_id) == set(_s.molecule_id), _f
    assert _d.smiles.map(lambda x: x != '' and len(x.split(';')) <= 25 and all(t_ != '' for t_ in x.split(';'))).all(), (_f, 'empty SMILES or more than 25')
_a, _b = _s.set_index('molecule_id').smiles, _r.set_index('molecule_id').smiles
_ch = [k for k in _a.index if _a[k] != _b[k]]; _t1 = [k for k in _a.index if _a[k].split(';')[0] != _b[k].split(';')[0]]
assert set(_ch) <= set(_es.molecule), 'a list changed for a molecule that did not go through E2'
assert not (set(_ch) & set(_es[_es.n_e2 == 0].molecule)), 'a list changed although E2 was empty'
assert not _m['fusion'].get('learned_failed'), 'learned fusion failed on some molecule'
print('E2_RECORD', _j.dumps(dict(e2={k: _e.get(k) for k in ('model', 'model_sha256', 'trees', 'K', 'alpha', 'hedge', 'molecules', 'e2_nonempty', 'e2_failed', 'top1_changed', 'top25_changed', 'new_keys_mols', 'lists_changed', 'pcl_tier_rows', 'bio_rows', 'coconut', 'index_sha256', 'index_keys', 'index_unmapped_rows', 'e2_seconds')},
      lists_changed=len(_ch), top1_changed=len(_t1), fusion=_m['fusion'])), flush=True)
""" % ("H" if HEDGE else "F", SHA, HEDGE, IDX_SHA, json.dumps(FEATS))
assert len(nb["cells"]) == 2, len(nb["cells"])
nb["cells"].insert(1, dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=RDK))
nb["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=RECORD))
json.dump(nb, open(nbp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
meta = json.load(open(os.path.join(HERE, "b1-fpnet-v8w7a", "kernel-metadata.json"), encoding="utf-8"))
meta = dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb", dataset_sources=meta["dataset_sources"] + ["hayatetaf/casmi26-e2-model"])
json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w", encoding="utf-8"), indent=1)
print("wrote", out, os.path.getsize(nbp), "bytes; model sha", SHA[:16], "hedge", HEDGE)
