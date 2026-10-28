"""101: DIAGNOSTIC probe kernel = E0 (kernels/baseline-v18, unchanged) + one appended cell: the engine-2 list ENG (cell 08) top 25,
restricted to provenance group B (COCONUT and not a training structure, the 055 definition, official key), order kept, no refill, empty -> CCO.
Comparable with E0_B (final top 25 -> B, 0.259). Not a method candidate.
Usage: python -X utf8 kernels/make_e0_base_probe.py   (writes kernels/e0-probe-engb)
"""
import copy, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CELL = r'''# ==== DIAGNOSTIC PROBE (Codex 088): E0 engine-2 list (cell 08, ENG blend order) top 25 restricted to one provenance group, order unchanged, no refill; empty -> CCO ====
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
_sub = _pd.read_csv('submission.csv'); _out = []; _nonempty = 0; _n_in = 0; _n_keep = 0; _n_base = 0
for _m in _sub.molecule_id.astype(str):
    _keep = []
    _e = ENG.get(_m) or {}
    _lst = list(_e.get('smiles') or [])[:25]
    _n_base += bool(_lst)
    for _x in _lst:
        _n_in += 1; _k = _okey(_x); _isT = _k in _T
        _isB = (not _isT) and ((_k in _CP) or (_rkey(_x) in _CR))
        if (PROBE_GROUP == 'T' and _isT) or (PROBE_GROUP == 'B' and _isB): _keep.append(_x)
    _n_keep += len(_keep); _nonempty += bool(_keep); _out.append(';'.join(_keep) if _keep else 'CCO')
_sub['smiles'] = _out; _sub.to_csv('submission.csv', index=False)
print('E0_ENG_PROBE', PROBE_GROUP, 'molecules with an ENG list', _n_base, 'rows', len(_sub), 'non-empty lists', _nonempty, 'candidates kept', _n_keep, 'of', _n_in, flush=True)
'''
nb = json.load(open(os.path.join(HERE, "baseline-v18", "casmi26-baseline-v18.ipynb"), encoding="utf-8"))
meta = json.load(open(os.path.join(HERE, "baseline-v18", "kernel-metadata.json"), encoding="utf-8"))
name = "casmi26-e0-probe-engb"; out_dir = os.path.join(HERE, "e0-probe-engb"); os.makedirs(out_dir, exist_ok=True)
nb2 = copy.deepcopy(nb)
nb2["cells"].append(dict(cell_type="markdown", metadata={}, source=["## DIAGNOSTIC probe ENG_B (Codex 101): engine-2 list (ENG, blend order) top 25 restricted to group B; not a method candidate."]))
nb2["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=CELL.replace("__GROUP__", "B")))
json.dump(nb2, open(os.path.join(out_dir, f"{name}.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb"), open(os.path.join(out_dir, "kernel-metadata.json"), "w", encoding="utf-8"), indent=2)
print("wrote", out_dir)
