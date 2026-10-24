"""Generate the B1 Kaggle notebook: embeds experiments/b1_baseline/{b1_common.py,b1_pipeline.py} verbatim, installs the official RDKit
wheel when the attached datasets provide it (scorer-exact official keys), runs the pipeline and leaves submission.csv in /kaggle/working.
Usage: python -X utf8 make_b1_notebook.py <out.ipynb>
"""
import json, os, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "experiments", "b1_baseline")
files = {n: open(os.path.join(SRC, n), encoding="utf-8").read() for n in ("b1_common.py", "b1_pipeline.py", "b1_rankfeats.py")}
model = os.path.join(SRC, "rank", "lambdarank.txt")
if os.path.exists(model): files["lambdarank.txt"] = open(model, encoding="utf-8").read()
shas = {n: hashlib.sha256(v.encode()).hexdigest() for n, v in files.items()}

cells = []
cells.append(f'''"""B1 baseline (own pipeline) -- label-free retrieval + FPNet + library similarity + GLACIER/ICEBERG + fixed fusion.
Sources embedded from experiments/b1_baseline (sha256 b1_common {shas['b1_common.py'][:12]}, b1_pipeline {shas['b1_pipeline.py'][:12]})."""
import os, sys, glob, subprocess, time, json
T0 = time.time()
os.makedirs('/kaggle/working/b1', exist_ok=True)
SOURCES = {json.dumps(files)}
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
''')
cells.append('''import subprocess, sys, time, json, os
t0 = time.time()
cmd = [sys.executable, '-X', 'utf8', '/kaggle/working/b1/b1_pipeline.py', '--out', '/kaggle/working']
print('running', ' '.join(cmd), flush=True)
with open('/kaggle/working/b1_pipeline.log', 'w') as lf:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in p.stdout:
        print(line, end='', flush=True); lf.write(line)
    rc = p.wait()
print('pipeline rc', rc, f'{time.time()-t0:.0f}s', flush=True)
assert os.path.exists('/kaggle/working/submission.csv'), 'submission.csv missing'
import pandas as pd
sub = pd.read_csv('/kaggle/working/submission.csv'); samp = pd.read_csv('/kaggle/input/enveda-CASMI26-molecule-id-mass-spectra/sample_submission.csv')
assert len(sub) == len(samp) and set(sub.molecule_id) == set(samp.molecule_id), (len(sub), len(samp))
assert sub.smiles.notna().all() and sub.smiles.map(lambda s: len(str(s).split(';'))).max() <= 25
print(json.load(open('/kaggle/working/b1_run_manifest.json')))
print('OK', sub.shape, flush=True)
''')
nb = {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c.splitlines(keepends=True)} for c in cells],
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1]
json.dump(nb, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, shas)
