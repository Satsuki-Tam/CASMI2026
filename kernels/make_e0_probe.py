"""049 (proposal, pending Codex): DIAGNOSTIC probe kernels of E0 (the public 0.464 reproduction, kernels/baseline-v18, unchanged) with one
appended cell that keeps only the candidates of one provenance group of E0's FINAL list (order unchanged; empty list -> CCO), so that E0's
Public score can be split by truth group exactly like the B1 probes T (0.160) and B (0.202) of 10/26. Not a method candidate.
  T = training structure: official key in the v2 pool with the train bit (src 1 or 3)
  B = COCONUT structure and not T: official key in the v2 pool with the COCONUT bit (src 2 or 3) or raw InChIKey14 in the COCONUT store
Usage: python -X utf8 kernels/make_e0_probe.py   (writes kernels/e0-probe-t and kernels/e0-probe-b)
"""
import copy, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "baseline-v18")
CELL = r'''# ==== DIAGNOSTIC PROBE (Codex 049): E0's final list restricted to one provenance group, order unchanged; empty -> CCO ====
import pickle as _pk, glob as _glob
import pandas as _pd, polars as _pl
from rdkit import Chem as _Chem
from rdkit.Chem.MolStandardize import rdMolStandardize as _rms
from rdkit import RDLogger as _RDL
_RDL.DisableLog("rdApp.*")
PROBE_GROUP = '__GROUP__'
def _find(p):
    hits = sorted(_glob.glob(f'/kaggle/input/**/{p}', recursive=True), key=len)
    if not hits: raise FileNotFoundError(p)
    return hits[0]
_te = _rms.TautomerEnumerator()
def _okey(s):
    try:
        m = _Chem.MolFromSmiles(s)
        if m is None: return None
        _Chem.RemoveStereochemistry(m); m = _te.Canonicalize(m); return _Chem.MolToInchiKey(m)[:14]
    except Exception: return None
def _rkey(s):
    try:
        m = _Chem.MolFromSmiles(s); return _Chem.MolToInchiKey(m)[:14] if m is not None else None
    except Exception: return None
_pool = _pl.read_parquet(_find('pool_meta.parquet'), columns=['key', 'src'])
_T = set(_pool.filter(_pl.col('src').is_in([1, 3]))['key'].to_list()); _CP = set(_pool.filter(_pl.col('src').is_in([2, 3]))['key'].to_list())
_CR = set(str(x) for x in _pk.load(open(_find('coco_meta.pkl'), 'rb'))['keys'])
_sub = _pd.read_csv('submission.csv'); _out = []; _nonempty = 0; _n_in = 0; _n_keep = 0
for _s in _sub.smiles.astype(str):
    _keep = []
    for _x in [y for y in _s.split(';') if y]:
        _n_in += 1; _k = _okey(_x); _isT = _k in _T
        _isB = (not _isT) and ((_k in _CP) or (_rkey(_x) in _CR))
        if (PROBE_GROUP == 'T' and _isT) or (PROBE_GROUP == 'B' and _isB): _keep.append(_x)
    _n_keep += len(_keep); _nonempty += bool(_keep); _out.append(';'.join(_keep) if _keep else 'CCO')
_sub['smiles'] = _out; _sub.to_csv('submission.csv', index=False)
print('E0_PROBE', PROBE_GROUP, 'rows', len(_sub), 'non-empty lists', _nonempty, 'candidates kept', _n_keep, 'of', _n_in, flush=True)
'''
TARGETS = [  # (source dir, source notebook, new kernel name, group)
    ("baseline-v18", "casmi26-baseline-v18.ipynb", "casmi26-e0-probe-t", "T"),
    ("baseline-v18", "casmi26-baseline-v18.ipynb", "casmi26-e0-probe-b", "B"),
    ("b1-fpnet-analog", "casmi26-b1-fpnet-analog.ipynb", "casmi26-b1-probe-b379", "B"),   # the 0.379 working baseline (57650023), same appended cell
]
for src_dir, src_nb, name, g in TARGETS:
    nb = json.load(open(os.path.join(HERE, src_dir, src_nb), encoding="utf-8"))
    meta = json.load(open(os.path.join(HERE, src_dir, "kernel-metadata.json"), encoding="utf-8"))
    out_dir = os.path.join(HERE, name.replace("casmi26-", "")); os.makedirs(out_dir, exist_ok=True)
    nb2 = copy.deepcopy(nb)
    nb2["cells"].append(dict(cell_type="markdown", metadata={}, source=[f"## DIAGNOSTIC probe {g} (Codex 049): the final list restricted to provenance group {g}; not a method candidate."]))
    nb2["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=CELL.replace("__GROUP__", g)))
    json.dump(nb2, open(os.path.join(out_dir, f"{name}.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    m2 = dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb")
    json.dump(m2, open(os.path.join(out_dir, "kernel-metadata.json"), "w", encoding="utf-8"), indent=2)
    print("wrote", out_dir, "from", src_dir)
