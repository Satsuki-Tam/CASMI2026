"""101 (c) / Codex 124 queue (used only if |D| < eta and pre-rank2_B > BASE_B): DIAGNOSTIC probe kernel = E0 (kernels/baseline-v18, unchanged)
+ one appended cell that rebuilds E006 from the same run's PREFUSION_LISTS and ENG with the SAME metric_fusion (alpha ALPHA, offset KRR,
window 40, official identity, safe_extend tail from submission_reference.csv) but WITHOUT the post-fusion forward re-ranks of cell 21
(GLACIER / joint ICE on N1 rows / FragGap / ICE fallback), i.e. every row takes cell 21's "unrescored" branch. The forward inside the
pre-fusion (PC / base) lists is unchanged. Parity: rows whose cell-21 branch was placeholder / no_engine / unrescored must equal
submission_e006_control.csv exactly (assert); re-ranked rows are counted. The result is then restricted to group B with the byte-identical
055 extraction cell of make_e0_probe.py (read from submission_fwdoff_full.csv instead of submission.csv). Read: pre-rank2_B - fwdoff_B with
eta 0.015 (the conditional increment of the post-fusion forward set on this fused list). Not a method candidate. Build only.
Usage: python -X utf8 kernels/make_e0_fwdoff_probe.py   (writes kernels/e0-probe-fwdoffb)
"""
import ast, copy, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
tree = ast.parse(open(os.path.join(HERE, "make_e0_probe.py"), encoding="utf-8").read())
EXTRACT = next(n.value.value for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "CELL" for t in n.targets))
src_line = "_sub = _pd.read_csv('submission.csv')"
assert EXTRACT.count(src_line) == 1
EXTRACT = EXTRACT.replace(src_line, "_sub = _pd.read_csv('submission_fwdoff_full.csv')").replace("print('E0_PROBE',", "print('E0_FWDOFF_PROBE',")
REBUILD = r'''# ==== DIAGNOSTIC PROBE (101 (c)): E006 rebuilt WITHOUT the post-fusion forward re-ranks (cell 21 "unrescored" branch for every row) ====
import json as _json, collections as _col
import pandas as _pd0
_ref = _pd0.read_csv('submission_reference.csv', dtype=str, keep_default_na=False)
_ctl = _pd0.read_csv('submission_e006_control.csv', dtype=str, keep_default_na=False)
_aud = _pd0.read_csv('experiment_audit_factorial.csv', dtype=str, keep_default_na=False)
_processed = set(_json.load(open('e004_verification.json'))['processed_ids'])
assert list(_ref.molecule_id) == list(_ctl.molecule_id) and _ref.molecule_id.is_unique
_branch = dict(zip(_aud.molecule_id.astype(str), _aud.branch.astype(str)))
_e006 = dict(zip(_ctl.molecule_id.astype(str), _ctl.smiles.astype(str)))
_rows, _stat = [], _col.Counter()
for _r in _ref.itertuples(index=False):
    _mid, _orig = str(_r.molecule_id), str(_r.smiles).split(';')
    _res = _orig
    if _mid in _processed:
        _eng = ENG.get(_mid)
        if _mid in PREFUSION_LISTS and _eng and _eng.get('smiles'):
            _first = [s for s in PREFUSION_LISTS[_mid] if s and s != 'CCO']
            _cands, _scs, _coll = metric_fusion(_first, _eng['smiles'], metric_identity, alpha=ALPHA, offset=KRR, limit=40)
            if _cands:
                _res = safe_extend(_cands[:25], _cands[25:] + _orig)
                _fused = set(metric_identity(s) for s in _cands) | set(metric_identity(s) for s in _orig)
                assert all(metric_identity(s) in _fused for s in _e006[_mid].split(';') if s != 'CCO'), ('E006 left the fused set', _mid)
    _out = ';'.join(_res) if _res else 'CCO'
    _b = _branch.get(_mid, 'missing'); _same = _out == _e006[_mid]
    if _b in ('placeholder', 'no_engine', 'unrescored'):
        assert _same, ('forward-off differs from E006 on a row without a forward re-rank', _mid, _b)
    assert 1 <= len(_out.split(';')) <= 25
    _ids = [metric_identity(s) for s in _out.split(';')]
    assert _out == 'CCO' or (None not in _ids and len(_ids) == len(set(_ids))), _mid
    _stat[(_b, 'identical' if _same else 'changed', 'top1_same' if _out.split(';')[:1] == _e006[_mid].split(';')[:1] else 'top1_changed')] += 1
    _rows.append((_r.molecule_id, _out))
_pd0.DataFrame(_rows, columns=['molecule_id', 'smiles']).to_csv('submission_fwdoff_full.csv', index=False)
print('E0_FWDOFF_REBUILD', _json.dumps({'|'.join(k): v for k, v in sorted(_stat.items())}), flush=True)
'''
nb = json.load(open(os.path.join(HERE, "baseline-v18", "casmi26-baseline-v18.ipynb"), encoding="utf-8"))
meta = json.load(open(os.path.join(HERE, "baseline-v18", "kernel-metadata.json"), encoding="utf-8"))
name = "casmi26-e0-probe-fwdoffb"; out_dir = os.path.join(HERE, "e0-probe-fwdoffb"); os.makedirs(out_dir, exist_ok=True)
nb2 = copy.deepcopy(nb)
nb2["cells"].append(dict(cell_type="markdown", metadata={}, source=["## DIAGNOSTIC probe fwdoff_B (101 (c)): E006 without the post-fusion forward re-ranks, restricted to group B; not a method candidate."]))
nb2["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=REBUILD))
nb2["cells"].append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=EXTRACT.replace("__GROUP__", "B")))
json.dump(nb2, open(os.path.join(out_dir, f"{name}.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(dict(meta, id=f"hayatetaf/{name}", title=name, code_file=f"{name}.ipynb"), open(os.path.join(out_dir, "kernel-metadata.json"), "w", encoding="utf-8"), indent=2)
print("wrote", out_dir)
