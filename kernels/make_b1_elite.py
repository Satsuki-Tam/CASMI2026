"""Build (not push) the 132 E-lite kernel (132_prereg_elite_public.md): the v8w7a kernel recipe (make_b1_notebook.py, same ranker / arguments /
smoke / checkpoint check; rebuilding v8w7a with this builder from experiments/b1_v7f038 is byte-identical to kernels/b1-fpnet-v8w7a) with the
sources of experiments/b1_elite (pop0 pipeline + the read-only E-lite hook, elite.py embedded) and the E-lite arguments. The E model and the E keys
come from the private dataset hayatetaf/casmi26-b1-elite-e1r (found by file name under /kaggle/input; sha256 checked by the pipeline).
submission.csv = the E-lite list; submission_pref.csv = the main list P of the same run (v8w7a).
v2 (Codex 132): an RDKIT cell before the pipeline requires the official-identity RDKit 2026.03.3 (the E keys were built with it) and a fixture of
tautomer / stereo cases to give the registered official keys, and records the version, the module path and the wheel hash; the RECORD cell after
the run checks the manifest's E-lite block (shas given and matching, K 10, alpha 0.5, pcl / twin off, resolved input paths), elite_stats (unique
molecules = the processed molecules with n_shortlist > 0, n_cand = n_shortlist, 0 <= n_e <= n_cand), the lists (ids, sizes; E empty -> E-lite = P;
lists differ only where E-lite ran) and prints ELITE_RECORD.
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
FIX = {"Oc1ccccn1": "UBQKCCHYAOITMY", "O=c1cccc[nH]1": "UBQKCCHYAOITMY", "CC(=O)CC(C)=O": "YRKCREAYFQTBPV", "CC(O)=CC(C)=O": "YRKCREAYFQTBPV",
       "C[C@H](N)C(=O)O": "QNAYBMKLOCPYGJ", "C[C@@H](N)C(=O)O": "QNAYBMKLOCPYGJ", "Nc1nc2[nH]cnc2c(=O)[nH]1": "UYTPUPDQBNUYGX", "Nc1nc(O)c2nc[nH]c2n1": "UYTPUPDQBNUYGX",
       "O=C1C(O)=C(Oc2cc(O)cc(O)c12)c1ccc(O)c(O)c1": "REFJWTPEDVJJIY", "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O": "WQZGKKKJIJFFOK", "C/C=C/C(=O)O": "LDHQCZJRKDOVOX",
       "C/C=C\\C(=O)O": "LDHQCZJRKDOVOX"}   # RDKit 2026.03.3, the pipeline's official identity (_okey)
RDK = """# ==== 132 (Codex 132): the official-identity environment of the pipeline must be RDKit 2026.03.3 (the E keys were built with it) ====
import glob as _g, hashlib as _h, json as _j, subprocess as _sp, sys as _s
_FIX = %s
_code = ("import json, rdkit; from rdkit import Chem, RDLogger; from rdkit.Chem.MolStandardize import rdMolStandardize; RDLogger.DisableLog('rdApp.*'); T = rdMolStandardize.TautomerEnumerator()\\n"
         "def k(s):\\n    m = Chem.MolFromSmiles(s); Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(T.Canonicalize(m))[:14]\\n"
         "print(json.dumps(dict(version=rdkit.__version__, file=rdkit.__file__, keys={s: k(s) for s in %%r})))" %% (list(_FIX),))
_r = _sp.run([_s.executable, '-c', _code], capture_output=True, text=True)   # a fresh interpreter = the environment the pipeline subprocess gets
assert _r.returncode == 0, ('132: RDKit fixture failed', _r.stderr[-500:])
_res = _j.loads(_r.stdout.strip().splitlines()[-1])
assert _res['version'] == '2026.03.3', ('132: the official-identity RDKit must be 2026.03.3', _res['version'], _res['file'])
_bad = {s_: (_res['keys'][s_], k_) for s_, k_ in _FIX.items() if _res['keys'][s_] != k_}
assert not _bad, ('132: official-identity fixture keys differ', _bad)
_whl = {w_: _h.sha256(open(w_, 'rb').read()).hexdigest() for w_ in sorted(_g.glob('/kaggle/input/**/rdkit-2026.3.3-*.whl', recursive=True))}
print('ELITE_RDKIT', _j.dumps(dict(version=_res['version'], file=_res['file'], fixture=len(_FIX), wheels=_whl)), flush=True)
""" % json.dumps(FIX)
RECORD = """# ==== 132 E-lite: record of the run (submission.csv = E-lite list, submission_pref.csv = main list P of the same run) ====
import json as _j, pandas as _p
_m = _j.load(open('/kaggle/working/b1_run_manifest.json')); _e = _m.get('elite') or {}
assert _e.get('model_sha256') == '%s' and _e.get('keys_sha256') == '%s' and _e.get('expected_shas_given') is True, ('E-lite inputs', _e.get('model_sha256'), _e.get('keys_sha256'), _e.get('expected_shas_given'))
assert _e.get('K') == 10.0 and _e.get('alpha') == 0.5 and not _e.get('pcl_boost') and _e.get('twin_tau') is None, ('E-lite combination', _e.get('K'), _e.get('alpha'), _e.get('pcl_boost'), _e.get('twin_tau'))
assert _m['params'].get('LAM') == 0.5 and _m['params'].get('lam_fixed') is None and _m.get('learned_model'), ('fusion parameters / ranker', _m['params'].get('LAM'), _m['params'].get('lam_fixed'), _m.get('learned_model'))
assert str(_e.get('model', '')).startswith('/kaggle/input/') and str(_e.get('keys', '')).startswith('/kaggle/input/'), ('E inputs not resolved under /kaggle/input', _e.get('model'), _e.get('keys'))
_st = _p.read_csv('/kaggle/working/b1_stage_stats.csv', dtype={'molecule': str})
_withc = _st[_st['n_shortlist'].fillna(0) > 0].set_index('molecule')['n_shortlist'] if 'n_shortlist' in _st.columns else None
assert _withc is not None and _withc.index.is_unique, 'stage stats: n_shortlist missing or duplicate molecules'
_es = _p.read_csv('/kaggle/working/elite_stats.csv', dtype={'molecule': str})
assert _es.molecule.is_unique and set(_es.molecule) == set(_withc.index), ('elite_stats molecules != processed molecules with candidates', len(_es), len(_withc))
assert _e.get('molecules') == len(_es), ('manifest E-lite molecules', _e.get('molecules'), len(_es))
assert (_es.set_index('molecule').n_cand == _withc.loc[_es.molecule].values).all() and ((_es.n_e >= 0) & (_es.n_e <= _es.n_cand)).all(), 'n_cand / n_e out of range'
_s = _p.read_csv('/kaggle/working/submission.csv', dtype=str, keep_default_na=False); _r = _p.read_csv('/kaggle/working/submission_pref.csv', dtype=str, keep_default_na=False)
for _d, _f in ((_s, 'submission.csv'), (_r, 'submission_pref.csv')):
    assert _d.molecule_id.is_unique and set(_d.molecule_id) == set(_s.molecule_id), _f
    assert _d.smiles.map(lambda x: x != '' and len(x.split(';')) <= 25 and all(t_ != '' for t_ in x.split(';'))).all(), (_f, 'empty SMILES or more than 25')
_a, _b = _s.set_index('molecule_id').smiles, _r.set_index('molecule_id').smiles
_ch = [k for k in _a.index if _a[k] != _b[k]]; _t1 = [k for k in _a.index if _a[k].split(';')[0] != _b[k].split(';')[0]]
assert set(_ch) <= set(_es.molecule), 'a list changed for a molecule that did not go through E-lite'
assert not (set(_ch) & set(_es[_es.n_e == 0].molecule)), 'a list changed although E was empty'
assert not _m['fusion'].get('learned_failed'), 'learned fusion failed on some molecule'
print('ELITE_RECORD', _j.dumps(dict(elite={k: _e.get(k) for k in ('model', 'model_sha256', 'keys', 'keys_sha256', 'n_keys', 'K', 'alpha', 'trees', 'expected_shas_given', 'molecules', 'e_nonempty', 'e_size_median', 'cand_median', 'top1_changed', 'top25_changed', 'lists_changed')},
      lists_changed=len(_ch), top1_changed=len(_t1), fusion=_m['fusion'])), flush=True)
""" % (EM_SHA, EK_SHA)
assert len(nb["cells"]) == 2, len(nb["cells"])
nb["cells"].insert(1, dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=RDK))
nb["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=RECORD))
json.dump(nb, open(nbp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
meta = json.load(open(os.path.join(HERE, "b1-fpnet-v8w7a", "kernel-metadata.json"), encoding="utf-8"))
meta = dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb", dataset_sources=meta["dataset_sources"] + ["hayatetaf/casmi26-b1-elite-e1r"])
json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w", encoding="utf-8"), indent=1)
print("wrote", out, os.path.getsize(nbp), "bytes")
