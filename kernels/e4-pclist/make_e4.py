"""Build the E4 notebook from the E0 baseline (casmi26-baseline-v18) with exact-match text replacements (version 3, after Codex 004).

E4 v3 = E0 +
 (1) PubChem-only channel list K 25 -> 100 (CORE string);
 (2) the extra PubChem-list structures (not already in the ICE input) are scored by ICEBERG and GLACIER in SEPARATE runner calls with
     their own work dirs and budgets (E4_ICE_BUDGET / E4_GL_BUDGET), AFTER the original runs, so the E0 computations and their coverage
     are never reduced; the extra scores are kept in E4_ICE / E4_GL and used ONLY for the PubChem-list ordering (later overlay cells see
     exactly what E0 saw);
 (3) PubChem-list ordering: whole-list z(pc_fz) + E4_W_GL z(GLACIER) + E4_W_ICE z(ICEBERG) (2.0 / 1.0) only when BOTH models have a finite
     score for EVERY structure of the list (E4_MIN_COVER = 1.0, v5 after Codex 005); otherwise the E0 rule (same-formula slot rerank of the top 25 with ICE+GL) runs unchanged.
Gate values (pc_fz[0], S, top_pop, fz_top, best_pool_fz), slots, promotion, base-list processing, RRF/overlays, data and weights untouched.
Evidence: experiments/p1_baseline/run1/results_final/pclist_v2_A_timstof.md (exact pool condition, real rerank_multi, complete ICE+GL).
Usage: python -X utf8 make_e4.py <baseline.ipynb> <out.ipynb>
"""
import json, sys

src, dst = sys.argv[1], sys.argv[2]
nb = json.load(open(src, encoding="utf-8"))
reps = []

# (1) PubChem-only channel list size (inside the CORE source string -> escaped newlines in the cell text)
reps.append(("\\nPC_N1 = 5000\\nPPM = 10.0\\nK = 25\\n",
             "\\nPC_N1 = 5000\\nPPM = 10.0\\nK = 100  # E4: 25 -> 100 (P1 run1: truth in the PubChem-only list 0.923 -> 0.970)\\n"))

# (2) constants next to the ICE constants (E0 budgets unchanged)
reps.append(("TOPN, ICE_LAM, ICE_BUDGET, ICE_PC = 60, 1.0, 5400, True\n",
             "TOPN, ICE_LAM, ICE_BUDGET, ICE_PC = 60, 1.0, 5400, True\n"
             "E4_W_GL, E4_W_ICE, E4_MIN_COVER, E4_ICE_BUDGET, E4_GL_BUDGET = 2.0, 1.0, 1.0, 2400, 1500   # E4 v5: E4_MIN_COVER 1.0 = both models must cover EVERY list structure, else the E0 rule (Codex 005)\n"
             "E4_CANDS, E4_ITEMS, E4_ICE, E4_GL = {}, [], {}, {}\n"))

# (3a) ICEBERG: second run for the extra PubChem-list structures, after the original run (inside the same try block)
old_ice = ("    meta_f = '/kaggle/working/ice_work/ice_out.json.meta.json'\n"
           "    if os.path.exists(meta_f):\n"
           "        print('ICE meta', open(meta_f).read()[:1500])\n")
new_ice = old_ice + (
    "    # ---- E4: extra PubChem-only list structures (K=100 lists of molecules the gate may use), scored in a SEPARATE run with its own budget\n"
    "    if ICE_PC and isinstance(PC, dict):\n"
    "        for _m in mids:\n"
    "            _p = PC.get(_m)\n"
    "            if _p and _p.get('pc') and BASE[_m][2] < LIB_TAU:\n"
    "                _have = set(cands.get(_m, []))\n"
    "                _extra = [s for s in dict.fromkeys(_p['pc']) if s and s not in _have]\n"
    "                if _extra: E4_CANDS[_m] = _extra\n"
    "    E4_ITEMS = ice_fuse.build_ice_input(te, E4_CANDS) if E4_CANDS else []\n"
    "    print('E4: extra PubChem-list candidates for ICE/GL:', sum(len(v) for v in E4_CANDS.values()), 'in', len(E4_CANDS), 'molecules', f'{time.time()-T0:.0f}s', flush=True)\n"
    "    if E4_ITEMS:\n"
    "        try:\n"
    "            E4_ICE = ice_fuse.run_ice(ICE_PKG, E4_ITEMS, workdir='/kaggle/working/ice_work_e4', device='cuda', budget_s=E4_ICE_BUDGET,\n"
    "                                      site='/kaggle/working/ice_site', extra_args=['--any-rdkit'])\n"
    "            _mf = '/kaggle/working/ice_work_e4/ice_out.json.meta.json'\n"
    "            print('E4 ICE meta', open(_mf).read()[:800] if os.path.exists(_mf) else 'missing', flush=True)\n"
    "        except Exception as _e:\n"
    "            E4_ICE = {}; print('E4 ICE extras failed (E0 path unaffected):', repr(_e), flush=True)\n")
reps.append((old_ice, new_ice))

# (3b) GLACIER: second run for the same extra structures, after the original run
old_gl = "    print('GL meta', open(meta_f).read()[:1500] if os.path.exists(meta_f) else 'missing')\n"
new_gl = old_gl + (
    "    if E4_ITEMS:                           # E4: GLACIER on the extra PubChem-list structures ([M+H]+ only, as the original run)\n"
    "        try:\n"
    "            _gl_e4 = [dict(it, spectra=[s for s in it['spectra'] if s.get('adduct') == '[M+H]+']) for it in E4_ITEMS]\n"
    "            _gl_e4 = [it for it in _gl_e4 if it['spectra']]\n"
    "            E4_GL = gl_fuse.run_gl(GL_PKG, _gl_e4, workdir='/kaggle/working/gl_work_e4', device='cuda', budget_s=E4_GL_BUDGET,\n"
    "                                   site='/kaggle/working/ice_site', wheels=os.path.join(ICE_PKG, 'wheels'), extra_args=['--any-rdkit'])\n"
    "            _mf = '/kaggle/working/gl_work_e4/gl_out.json.meta.json'\n"
    "            print('E4 GL meta', open(_mf).read()[:800] if os.path.exists(_mf) else 'missing', flush=True)\n"
    "        except Exception as _e:\n"
    "            E4_GL = {}; print('E4 GL extras failed (E0 path unaffected):', repr(_e), flush=True)\n")
reps.append((old_gl, new_gl))

# (4) PubChem-list ordering: whole-list fusion when both models cover the list, otherwise the unchanged E0 rule
old_pc = ("    p = PC.get(m) if (ICE_PC and isinstance(PC, dict)) else None\n"
          "    if p and p.get('pc_form') and ice:\n"
          "        try:                             # re-order the PubChem list by z(f.z) + lam z(ice) inside same-formula groups;\n"
          "            o = ice_fuse.rerank(p['pc'], p['pc_keys'], p['pc_fz'], p['pc_form'], ice, lam=ICE_LAM, top_n=25)\n"
          "            o = gl_rerank(o, p['pc'], p['pc_keys'], p['pc_fz'], p['pc_form'], ice, gl, 25, 'pc_')\n"
          "            fz0 = p['pc_fz'][0]          # the gate keeps using the ORIGINAL top f.z (rel), so gate decisions are unchanged\n"
          "            p['pc'] = [p['pc'][i] for i in o]; p['pc_keys'] = [p['pc_keys'][i] for i in o]\n"
          "            p['pc_fz'] = [fz0] + [p['pc_fz'][i] for i in o][1:]\n"
          "            ice_stats['pc_changed'] = ice_stats.get('pc_changed', 0) + int(o[:1] != [0])\n"
          "        except Exception as e:\n"
          "            print('pc rerank failed', m, repr(e))\n")
new_pc = ("    p = PC.get(m) if (ICE_PC and isinstance(PC, dict)) else None\n"
          "    _e4_done = False\n"
          "    if p and p.get('pc') and len(p['pc']) >= 2:\n"
          "        try:                             # E4: whole-list fusion z(pc_fz) + E4_W_GL z(GLACIER) + E4_W_ICE z(ICEBERG) over the K-structure list\n"
          "            _gx = dict(gl or {}); _gx.update({k: v for k, v in (E4_GL.get(str(m)) or {}).items() if v is not None})\n"
          "            _ix = dict(ice or {}); _ix.update({k: v for k, v in (E4_ICE.get(str(m)) or {}).items() if v is not None})\n"
          "            _b = np.asarray(p['pc_fz'], dtype=float)\n"
          "            _gv = np.array([_gx.get(s) if _gx.get(s) is not None else np.nan for s in p['pc']], dtype=float)\n"
          "            _iv = np.array([_ix.get(s) if _ix.get(s) is not None else np.nan for s in p['pc']], dtype=float)\n"
          "            _okg, _oki = np.isfinite(_gv), np.isfinite(_iv)\n"
          "            _need = max(2, int(np.ceil(E4_MIN_COVER * len(_b))))\n"
          "            if int(_okg.sum()) >= _need and int(_oki.sum()) >= _need:\n"
          "                def _e4z(v, ok):\n"
          "                    out = np.zeros_like(v); out[ok] = (v[ok] - v[ok].mean()) / (v[ok].std() + 1e-9); return out\n"
          "                _f = (_b - _b.mean()) / (_b.std() + 1e-9) + E4_W_GL * _e4z(_gv, _okg) + E4_W_ICE * _e4z(_iv, _oki)\n"
          "                o = [int(i) for i in np.argsort(-_f, kind='stable')]\n"
          "                fz0 = p['pc_fz'][0]          # the gate keeps using the ORIGINAL top f.z (rel), so gate decisions are unchanged\n"
          "                p['pc'] = [p['pc'][i] for i in o]; p['pc_keys'] = [p['pc_keys'][i] for i in o]\n"
          "                p['pc_fz'] = [fz0] + [p['pc_fz'][i] for i in o][1:]\n"
          "                ice_stats['pc_changed'] = ice_stats.get('pc_changed', 0) + int(o[:1] != [0])\n"
          "                ice_stats['pc_e4_fused'] = ice_stats.get('pc_e4_fused', 0) + 1\n"
          "                ice_stats['pc_e4_gl_cov'] = ice_stats.get('pc_e4_gl_cov', 0) + int(_okg.sum()); ice_stats['pc_e4_ice_cov'] = ice_stats.get('pc_e4_ice_cov', 0) + int(_oki.sum())\n"
          "                _e4_done = True\n"
          "            else:\n"
          "                ice_stats['pc_e4_fallback'] = ice_stats.get('pc_e4_fallback', 0) + 1\n"
          "        except Exception as e:\n"
          "            print('pc fusion failed -> E0 rule', m, repr(e))\n"
          "    if (not _e4_done) and p and p.get('pc_form') and ice:\n"
          "        try:                             # E0 rule, unchanged: z(f.z) + lam z(ice) (+ GL) inside same-formula groups of the top 25\n"
          "            o = ice_fuse.rerank(p['pc'], p['pc_keys'], p['pc_fz'], p['pc_form'], ice, lam=ICE_LAM, top_n=25)\n"
          "            o = gl_rerank(o, p['pc'], p['pc_keys'], p['pc_fz'], p['pc_form'], ice, gl, 25, 'pc_')\n"
          "            fz0 = p['pc_fz'][0]          # the gate keeps using the ORIGINAL top f.z (rel), so gate decisions are unchanged\n"
          "            p['pc'] = [p['pc'][i] for i in o]; p['pc_keys'] = [p['pc_keys'][i] for i in o]\n"
          "            p['pc_fz'] = [fz0] + [p['pc_fz'][i] for i in o][1:]\n"
          "            ice_stats['pc_changed'] = ice_stats.get('pc_changed', 0) + int(o[:1] != [0])\n"
          "        except Exception as e:\n"
          "            print('pc rerank failed', m, repr(e))\n")
reps.append((old_pc, new_pc))

log = []
for old, new in reps:
    hits = [(i, "".join(c["source"]).count(old)) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]
    hits = [(i, n) for i, n in hits if n]
    assert len(hits) == 1 and hits[0][1] == 1, f"expected exactly one match for {old[:60]!r}, got {hits}"
    i = hits[0][0]
    text = "".join(nb["cells"][i]["source"]).replace(old, new)
    nb["cells"][i]["source"] = text.splitlines(keepends=True)
    log.append(f"cell {i}: {old[:70]!r} -> {new[:70]!r}")
json.dump(nb, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(log)); print("wrote", dst)
if __name__ == "__main__" and "--selftest" in sys.argv:
    pass
