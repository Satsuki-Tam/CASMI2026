"""Generate the B1 Kaggle notebook: embeds experiments/b1_baseline/{b1_common.py,b1_pipeline.py} verbatim, installs the official RDKit
wheel when the attached datasets provide it (scorer-exact official keys), runs the pipeline and leaves submission.csv in /kaggle/working.
Usage: python -X utf8 make_b1_notebook.py <out.ipynb>
"""
import json, os, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "experiments", "b1_baseline")
import argparse
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--src_dir", default=SRC, help="directory holding b1_common.py / b1_pipeline.py / b1_rankfeats.py to embed (default: experiments/b1_baseline)"); ap.add_argument("--model", default=os.path.join(SRC, "rank", "lambdarank.txt"), help="LambdaRank model to embed ('' = none -> fixed rule)")
ap.add_argument("--emit", default="main", choices=["main", "insurance", "probe_train", "probe_nontrain", "probe_coconut", "probe_pubchem", "probe_pool", "probe_band26"], help="which list becomes submission.csv (one Kaggle submission per kernel version); "
                "probe_* = DIAGNOSTIC class-decomposition probes (Codex 023), needs a pipeline that writes submission_probe_*.csv")
ap.add_argument("--compress", default="zlib", choices=["zlib", "lzma"], help="blob codec (lzma for large models, e.g. 600-tree rankers; default zlib = unchanged)")
ap.add_argument("--pipeline_args", default="", help="extra b1_pipeline.py arguments, e.g. '--k_short 200 --k_pop 50 --w_ice 0'")
ap.add_argument("--expect_ckpt_sha", default="", help="full sha256 the loaded --fpnet_ckpt must have (asserted from the run manifest; empty = not checked)")
ap.add_argument("--smoke_n", type=int, default=0, help="commit-run smoke switch (E0 recipe): when test.parquet is the visible dummy (spectrum-id md5 654e030e...) and the run is not a competition rerun, run the pipeline on its first N molecules only (--limit; the other ids get the CCO placeholder) (saves ~3 h of GPU quota per version); 0 = off")
A = ap.parse_args()
files = {n: open(os.path.join(A.src_dir, n), encoding="utf-8").read() for n in ("b1_common.py", "b1_pipeline.py", "b1_rankfeats.py")}
if os.path.exists(os.path.join(A.src_dir, "b1_analog.py")): files["b1_analog.py"] = open(os.path.join(A.src_dir, "b1_analog.py"), encoding="utf-8").read()   # analog channel (2026-10-26), imported by b1_pipeline only with --analog_w
if os.path.exists(os.path.join(A.src_dir, "b1_frag.py")): files["b1_frag.py"] = open(os.path.join(A.src_dir, "b1_frag.py"), encoding="utf-8").read()   # MetFrag-lite (038), imported only with --frag_w_fallback
print("embedding sources from", A.src_dir)
model = A.model
if model and os.path.exists(model): files["lambdarank.txt"] = open(model, encoding="utf-8").read(); print("embedding model", model)
else: print("no model embedded -> fixed rule")
shas = {n: hashlib.sha256(v.encode()).hexdigest() for n, v in files.items()}
# the kernel API rejects notebooks above ~1 MiB (400 on SaveKernel, 2026-10-25): embed the sources + model as one zlib/base64 blob
import base64, zlib, lzma
_raw = json.dumps(files).encode("utf-8")
BLOB = base64.b64encode(lzma.compress(_raw, preset=9 | lzma.PRESET_EXTREME) if A.compress == "lzma" else zlib.compress(_raw, 9)).decode("ascii")
print(f"embedded blob {len(BLOB)/1e3:.0f} KB (raw {sum(len(v) for v in files.values())/1e3:.0f} KB)")

cells = []
cells.append(f'''"""B1 baseline (own pipeline) -- label-free retrieval + FPNet + library similarity + GLACIER/ICEBERG + fixed fusion.
Sources embedded from experiments/b1_baseline (sha256 b1_common {shas['b1_common.py'][:12]}, b1_pipeline {shas['b1_pipeline.py'][:12]})."""
import os, sys, glob, subprocess, time, json, base64, zlib, lzma
T0 = time.time()
os.makedirs('/kaggle/working/b1', exist_ok=True)
BLOB = {json.dumps(BLOB)}
SOURCES = json.loads((lzma.decompress if {json.dumps(A.compress)} == 'lzma' else zlib.decompress)(base64.b64decode(BLOB)).decode('utf-8'))
for name, text in SOURCES.items():
    open(f'/kaggle/working/b1/{{name}}', 'w', encoding='utf-8').write(text)
print('sources written', list(SOURCES), flush=True)
# official RDKit (scorer version) when provided by an attached dataset; otherwise keep the image's RDKit (keys may differ for ~1.6% of structures)
tag = f'cp{{sys.version_info.major}}{{sys.version_info.minor}}'
whl = [w for w in glob.glob('/kaggle/input/**/rdkit-2026.3.3-*.whl', recursive=True) if tag in w]
if whl:
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-index', '--quiet', whl[0]], capture_output=True, text=True)
    print('rdkit wheel install rc', r.returncode, r.stdout[-300:], r.stderr[-300:], flush=True)
else:
    print('no rdkit 2026.3.3 wheel attached; using the image RDKit', flush=True)
import rdkit; print('rdkit', rdkit.__version__, flush=True)
print('inputs:', sorted(os.listdir('/kaggle/input'))[:20], '| competitions:', sorted(os.listdir('/kaggle/input/competitions')) if os.path.isdir('/kaggle/input/competitions') else None, flush=True)
''')
cells.append(f'''PIPELINE_ARGS = {json.dumps(A.pipeline_args.split())}
EMBEDDED_SHA256 = {json.dumps(shas)}
EXPECT_CKPT_SHA = {json.dumps(A.expect_ckpt_sha)}
SMOKE_N = {A.smoke_n}   # >0: commit-run smoke on the visible dummy test only (never on the competition rerun)
EMIT = {json.dumps(A.emit)}   # 'main' = the pipeline's main list is submission.csv; 'insurance' = the fixed rule + library priority list is submission.csv (separate kernel version per Kaggle submission)
''' + '''import subprocess, sys, time, json, os, shutil, glob
t0 = time.time()
import hashlib, pandas as pd
_tests = sorted(glob.glob('/kaggle/input/**/enveda-CASMI26-molecule-id-mass-spectra/test.parquet', recursive=True))
assert len(_tests) == 1, ('competition test.parquet must be unique', _tests)   # Codex 025: one input decides both the mode and the pipeline input
COMP_TEST = _tests[0]; COMP_DIR = os.path.dirname(COMP_TEST)
TEST_FILE_SHA = hashlib.sha256(open(COMP_TEST, 'rb').read()).hexdigest()
_te = pd.read_parquet(COMP_TEST, columns=['molecule_id', 'spectrum_id'])
TEST_SIG = hashlib.md5(','.join(sorted(_te.spectrum_id.astype(str))).encode()).hexdigest()
KNOWN_DUMMY = (TEST_SIG == '654e030e4173780e945252b4a5adf70b' and TEST_FILE_SHA == '2fa29c4aa06e93b48e0cd6619fd2de3f4e956f0019d242141678b7287f2b43e0')   # visible dummy: spectrum ids AND file bytes
IS_RERUN = bool(os.getenv('KAGGLE_IS_COMPETITION_RERUN')) or not KNOWN_DUMMY   # anything not provably the dummy -> full run
SMOKE = SMOKE_N > 0 and not IS_RERUN
if SMOKE:   # commit run on the visible dummy: the pipeline processes its first SMOKE_N molecules and writes the CCO placeholder for the other ids (--limit)
    PIPELINE_ARGS = PIPELINE_ARGS + ['--limit', str(SMOKE_N)]
else:
    assert not any(a == '--limit' or a.startswith('--limit=') for a in PIPELINE_ARGS), 'full run must not carry --limit'
PIPELINE_ARGS = PIPELINE_ARGS + ['--test', COMP_TEST]
print('test', COMP_TEST, 'molecules', _te.molecule_id.nunique(), 'signature', TEST_SIG, 'file sha256', TEST_FILE_SHA, '| known dummy', KNOWN_DUMMY, '| rerun', IS_RERUN, '| SMOKE', SMOKE, SMOKE_N, flush=True)
cmd = [sys.executable, '-X', 'utf8', '/kaggle/working/b1/b1_pipeline.py', '--out', '/kaggle/working'] + PIPELINE_ARGS
print('running', ' '.join(cmd), flush=True)
with open('/kaggle/working/b1_pipeline.log', 'w') as lf:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in p.stdout:
        print(line, end='', flush=True); lf.write(line)
    rc = p.wait()
print('pipeline rc', rc, f'{time.time()-t0:.0f}s', flush=True)
assert rc == 0, f'pipeline failed (rc {rc}); no submission file is promoted'   # Codex 023b: never promote outputs of a failed run
import pandas as pd, hashlib
samp = pd.read_csv(os.path.join(COMP_DIR, 'sample_submission.csv'))
# completeness (Codex 025): every test molecule was processed in a full run (zero-candidate molecules still get a stats row); smoke processes only its first SMOKE_N
_stats = pd.read_csv('/kaggle/working/b1_stage_stats.csv'); PROCESSED = set(_stats['molecule'].astype(str)); TEST_IDS = set(_te.molecule_id.astype(str))
if SMOKE: assert len(PROCESSED) == min(SMOKE_N, len(TEST_IDS)) and PROCESSED <= TEST_IDS, (len(PROCESSED), SMOKE_N)
else: assert PROCESSED == TEST_IDS, ('full run did not process every test molecule', len(PROCESSED), len(TEST_IDS))
_man = json.load(open('/kaggle/working/b1_run_manifest.json'))
if EXPECT_CKPT_SHA: assert _man['params'].get('fpnet_ckpt_sha256') == EXPECT_CKPT_SHA, ('loaded FPNet checkpoint differs', _man['params'].get('fpnet_ckpt_sha256'))
def check(path):   # every molecule id once, non-empty SMILES lists of at most 25
    s_ = pd.read_csv(path)
    assert len(s_) == len(samp) and set(s_.molecule_id) == set(samp.molecule_id) and s_.molecule_id.is_unique, (path, len(s_), len(samp))
    assert s_.smiles.notna().all() and s_.smiles.map(lambda x: len(str(x).split(';'))).max() <= 25, path
    return s_
check('/kaggle/working/submission.csv')
if EMIT == 'insurance':
    check('/kaggle/working/submission_fixed.csv')
    os.replace('/kaggle/working/submission.csv', '/kaggle/working/submission_main.csv'); shutil.copy('/kaggle/working/submission_fixed.csv', '/kaggle/working/submission.csv')
    print('EMIT insurance: submission.csv = fixed rule + library priority (main list kept as submission_main.csv)', flush=True)
elif EMIT.startswith('probe_'):
    for f_ in glob.glob('/kaggle/working/submission_probe_*.csv'): check(f_)
    os.replace('/kaggle/working/submission.csv', '/kaggle/working/submission_main.csv'); shutil.copy(f'/kaggle/working/submission_{EMIT}.csv', '/kaggle/working/submission.csv')
    print(f'EMIT {EMIT}: DIAGNOSTIC probe -- submission.csv = the main list filtered by candidate group (main list kept as submission_main.csv)', flush=True)
sub = check('/kaggle/working/submission.csv')
meta = dict(emit=EMIT, pipeline_rc=rc, pipeline_args=PIPELINE_ARGS, embedded_sha256=EMBEDDED_SHA256, test_signature=TEST_SIG, test_file_sha256=TEST_FILE_SHA, known_dummy=KNOWN_DUMMY, is_rerun=IS_RERUN, smoke=SMOKE, smoke_n=SMOKE_N, n_test=len(TEST_IDS), n_processed=len(PROCESSED), expect_ckpt_sha=EXPECT_CKPT_SHA,
            files={os.path.basename(f_): hashlib.sha256(open(f_, 'rb').read()).hexdigest() for f_ in sorted(glob.glob('/kaggle/working/submission*.csv'))},
            run_manifest=json.load(open('/kaggle/working/b1_run_manifest.json')))
json.dump(meta, open('/kaggle/working/submission_meta.json', 'w'), indent=1); print(json.dumps(meta)[:3000], flush=True)
print('OK', sub.shape, flush=True)
''')
nb = {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c.splitlines(keepends=True)} for c in cells],
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
out = A.out
json.dump(nb, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, shas)
