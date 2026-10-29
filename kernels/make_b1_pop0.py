"""Build (not push) the pop0 DIAGNOSTIC kernel (116 / 124 / 125): the v8w7a kernel recipe (make_b1_notebook.py, same model / args / smoke / ckpt
check; rebuilding v8w7a with this recipe from experiments/b1_v7f038 is byte-identical to kernels/b1-fpnet-v8w7a) with the sources of
experiments/b1_pop0 (make_pop0.py: frozen fusion loop moved verbatim into _fusion_pass, fixed-rule prior coefficient as --lam_fixed) and
--lam_fixed 0 -> submission.csv = the pop0 list; submission_lamref*.csv = the frozen-LAM lists of the same run (in-run control).
An appended RECORD cell asserts lam_fixed 0 in the run manifest and the lamref files' ids, and prints the per-pass fusion counts and the number of
molecules whose list / rank-1 changed. Not a method candidate.
Usage: python -X utf8 kernels/make_b1_pop0.py"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
name = "casmi26-b1-pop0"; out = os.path.join(HERE, "b1-pop0"); os.makedirs(out, exist_ok=True); nbp = os.path.join(out, f"{name}.ipynb")
ARGS = "--k_fpp 200 --k_pop 50 --w_ice 0 --tau 0.9 --main blend21 --gl_budget 14000 --deadline_s 30000 --fpnet_ckpt full_eval_final.pt --analog_w 0 --analog_w_fallback 1 --analog_feat ap --frag_w_fallback 1"
subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "b1-baseline", "make_b1_notebook.py"), nbp, "--src_dir", os.path.join(ROOT, "experiments", "b1_pop0"),
                "--model", os.path.join(ROOT, "experiments", "b1_baseline", "rank_v8w7a", "lambdarank_stripped.txt"), "--compress", "lzma",
                "--pipeline_args", ARGS + " --lam_fixed 0", "--expect_ckpt_sha", "5b8d1c311d1171089374379c10cb82fdcc36457a7ab02ec0dddc6f12059b616d", "--smoke_n", "12"], check=True)
nb = json.load(open(nbp, encoding="utf-8"))
RECORD = """# ==== DIAGNOSTIC pop0 (116/124/125): record of the in-run control ====
import json as _j, pandas as _p
_m = _j.load(open('/kaggle/working/b1_run_manifest.json'))
assert _m['params'].get('lam_fixed') == 0.0 and _m['params'].get('LAM') == 0.5, ('lam_fixed / LAM', _m['params'].get('lam_fixed'), _m['params'].get('LAM'))
_s = _p.read_csv('/kaggle/working/submission.csv')
for _f in ('submission_lamref.csv', 'submission_lamref_fixed.csv', 'submission_lamref_probe_train.csv', 'submission_lamref_probe_nontrain.csv'):
    _r = _p.read_csv('/kaggle/working/' + _f); assert len(_r) == len(_s) and set(_r.molecule_id) == set(_s.molecule_id) and _r.molecule_id.is_unique, _f
print('POP0_RECORD', _j.dumps(dict(lam_fixed=_m['params']['lam_fixed'], LAM=_m['params']['LAM'], fusion=_m['fusion'], fusion_lamref=_m.get('fusion_lamref'))), flush=True)
"""
nb["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=RECORD))
json.dump(nb, open(nbp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
meta = json.load(open(os.path.join(HERE, "b1-fpnet-v8w7a", "kernel-metadata.json"), encoding="utf-8"))
json.dump(dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb"), open(os.path.join(out, "kernel-metadata.json"), "w", encoding="utf-8"), indent=1)
print("wrote", out, os.path.getsize(nbp), "bytes")
