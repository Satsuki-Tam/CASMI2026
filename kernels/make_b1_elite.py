"""Build (not push) the 132 E-lite kernel (132_prereg_elite_public.md): the v8w7a kernel recipe (make_b1_notebook.py, same ranker / arguments /
smoke / checkpoint check; rebuilding v8w7a with this builder from experiments/b1_v7f038 is byte-identical to kernels/b1-fpnet-v8w7a) with the
sources of experiments/b1_elite (pop0 pipeline + the read-only E-lite hook, elite.py embedded) and the E-lite arguments. The E model and the E keys
come from the private dataset hayatetaf/casmi26-b1-elite-e1r (found by file name under /kaggle/input; sha256 checked by the pipeline).
submission.csv = the E-lite list; submission_pref.csv = the main list P of the same run (v8w7a). An appended RECORD cell asserts the run manifest's
E-lite block (shas, K 10, alpha 0.5, molecules = processed molecules with candidates), the lists' ids / sizes, and prints ELITE_RECORD.
Usage: python -X utf8 kernels/make_b1_elite.py"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
name = "casmi26-b1-elite"; out = os.path.join(HERE, "b1-elite"); os.makedirs(out, exist_ok=True); nbp = os.path.join(out, f"{name}.ipynb")
ARGS = "--k_fpp 200 --k_pop 50 --w_ice 0 --tau 0.9 --main blend21 --gl_budget 14000 --deadline_s 30000 --fpnet_ckpt full_eval_final.pt --analog_w 0 --analog_w_fallback 1 --analog_feat ap --frag_w_fallback 1"
EM_SHA, EK_SHA = "8f4a81b5f8ba7f589cfd74980ea40075169121b2ce1382cb92a1f2aa150ec1f5", "f572682b47a882de18bbe3ded9129fa0544e3c52281447e90f7bc3f13042a672"
ELITE = f"--elite_model elite132_e1r_lambdarank.txt --elite_keys elite132_e_window_keys_v2.parquet --elite_k 10 --elite_alpha 0.5 --elite_model_sha {EM_SHA} --elite_keys_sha {EK_SHA}"
subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "b1-baseline", "make_b1_notebook.py"), nbp, "--src_dir", os.path.join(ROOT, "experiments", "b1_elite"),
                "--model", os.path.join(ROOT, "experiments", "b1_baseline", "rank_v8w7a", "lambdarank_stripped.txt"), "--compress", "lzma",
                "--pipeline_args", ARGS + " " + ELITE, "--expect_ckpt_sha", "5b8d1c311d1171089374379c10cb82fdcc36457a7ab02ec0dddc6f12059b616d", "--smoke_n", "12"], check=True)
nb = json.load(open(nbp, encoding="utf-8"))
RECORD = """# ==== 132 E-lite: record of the run (submission.csv = E-lite list, submission_pref.csv = main list P of the same run) ====
import json as _j, pandas as _p
_m = _j.load(open('/kaggle/working/b1_run_manifest.json')); _e = _m.get('elite') or {}
assert _e.get('model_sha256') == '%s' and _e.get('keys_sha256') == '%s', ('E-lite inputs', _e.get('model_sha256'), _e.get('keys_sha256'))
assert _e.get('K') == 10.0 and _e.get('alpha') == 0.5 and _m['params'].get('LAM') == 0.5 and _m['params'].get('lam_fixed') is None, ('E-lite / fusion parameters', _e.get('K'), _e.get('alpha'))
_st = _p.read_csv('/kaggle/working/b1_stage_stats.csv'); _proc = set(_st.molecule.astype(str)); _withc = set(_st[_st.n_unique.fillna(0) > 0].molecule.astype(str)) if 'n_unique' in _st.columns else _proc
_es = _p.read_csv('/kaggle/working/elite_stats.csv', dtype={'molecule': str})
assert _e.get('molecules') == len(_es) and set(_es.molecule) <= _proc, ('E-lite molecules', _e.get('molecules'), len(_es), len(_proc))
_s = _p.read_csv('/kaggle/working/submission.csv', dtype=str, keep_default_na=False); _r = _p.read_csv('/kaggle/working/submission_pref.csv', dtype=str, keep_default_na=False)
for _d, _f in ((_s, 'submission.csv'), (_r, 'submission_pref.csv')):
    assert _d.molecule_id.is_unique and set(_d.molecule_id) == set(_s.molecule_id), _f
    assert _d.smiles.map(lambda x: x != '' and len(x.split(';')) <= 25 and all(t_ != '' for t_ in x.split(';'))).all(), (_f, 'empty SMILES or more than 25')
_a, _b = _s.set_index('molecule_id').smiles, _r.set_index('molecule_id').smiles
_ch = [k for k in _a.index if _a[k] != _b[k]]; _t1 = [k for k in _a.index if _a[k].split(';')[0] != _b[k].split(';')[0]]
assert set(_ch) <= set(_es.molecule), 'a list changed for a molecule that did not go through E-lite'
assert not _m['fusion'].get('learned_failed'), 'learned fusion failed on some molecule'
print('ELITE_RECORD', _j.dumps(dict(elite={k: _e.get(k) for k in ('model_sha256', 'keys_sha256', 'n_keys', 'K', 'alpha', 'trees', 'molecules', 'e_nonempty', 'e_size_median', 'cand_median', 'top1_changed', 'top25_changed', 'lists_changed')},
      lists_changed=len(_ch), top1_changed=len(_t1), fusion=_m['fusion'])), flush=True)
""" % (EM_SHA, EK_SHA)
nb["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=RECORD))
json.dump(nb, open(nbp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
meta = json.load(open(os.path.join(HERE, "b1-fpnet-v8w7a", "kernel-metadata.json"), encoding="utf-8"))
meta = dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb", dataset_sources=meta["dataset_sources"] + ["hayatetaf/casmi26-b1-elite-e1r"])
json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w", encoding="utf-8"), indent=1)
print("wrote", out, os.path.getsize(nbp), "bytes")
