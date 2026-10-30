"""145 E2 kernel pipeline (144_prereg_e2.md v2): the pipeline of the submitted v8w7a list (experiments/b1_pop0, sha 365fe307) with ONE
addition, the E2 second engine and the fixed fusion F (identity RRF, K 10, alpha 0.5; --e2_hedge 1 = H) applied to the final main order:
  --e2_model (e2_lgb.txt) --e2_model_sha [--e2_hedge 0|1] [--e2_dump 1] [--e2_bio / --e2_pcl / --e2_structs file names]
  -> submission.csv = F (or H); submission_pref.csv = the main list P of the same run; e2_stats.csv per molecule; manifest 'e2'.
Construction:
  (1) a worker function _e2frag (MetFrag-lite of an E-window list, b1_frag) next to _okey;
  (2) after the evaluation-mode masks are read, the E2 engine (experiments/e2/e2_engine.py, embedded) is built on the SAME objects P uses
      (PubChem tier arrays, v2 pool, COCONUT arrays, spectra store, library index key_rows, analog store) + BIO / PubChemLite tier rows /
      train_structs (resolved by file name; several hits must be byte-identical);
  (3) in the candidate loop, right after feats[mid] = rows, the E2 order of the molecule from the same queries q, M_by_add and FPNet logits
      zlog (read only; P's rows are not touched); test regime = no masks; evaluation mode supports the C1 view only (rows + same_lib);
  (4) _fusion_pass gets a keyword hook (default None) called once per molecule at the END of the loop body with (mid, rows, order); the hook
      fuses P's final top 25 (official keys) with the E2 order by e2_engine.fuse_rrf (alpha 0 must give P; empty E2 -> P);
  (5) output: submission.csv = F / H, submission_pref.csv = P; molecules without P candidates keep the placeholder.
Without --e2_model the run is the pop0 / v8w7a run (hook None; outputs as before).
Usage: python -X utf8 experiments/b1_e2k/make_e2k.py   (writes experiments/b1_e2k/b1_pipeline.py + copies; prints the checks)"""
import hashlib, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "b1_pop0"); E2D = os.path.join(os.path.dirname(HERE), "e2")
for f in ("b1_common.py", "b1_analog.py", "b1_frag.py", "b1_rankfeats.py"):
    shutil.copy(os.path.join(SRC, f), os.path.join(HERE, f))
for f in ("e2_engine.py", "e2_common.py"):
    shutil.copy(os.path.join(E2D, f), os.path.join(HERE, f))
s = open(os.path.join(SRC, "b1_pipeline.py"), encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("365fe30737af"), "pop0 pipeline changed"
assert "E2" not in s and "e2_" not in s, "name clash with the pop0 pipeline"
t = s


def rep(old, new, count=1):
    global t
    assert t.count(old) == count, (old[:80], t.count(old)); t = t.replace(old, new)


# 1. worker
rep("def _okey(smiles):",
    "def _e2frag(task):   # 145 E2: MetFrag-lite of one E-window list (b1_frag.score(b1_frag.fragments(s), spectra)), worker side\n"
    "    import b1_frag as _FR\n"
    "    smiles_, spectra_ = task; return {s_: float(_FR.score(_FR.fragments(s_), spectra_)) for s_ in smiles_}\n\n\n"
    "def _okey(smiles):")
# 2. arguments
rep('    ap.add_argument("--gl_json", default=None,',
    '    ap.add_argument("--e2_model", default=None, help="145: E2 second engine (experiments/e2 e2_lgb.txt); submission.csv = the fixed identity RRF F of the final main order with E2 (K 10, alpha 0.5; --e2_hedge 1 = H), the main list = submission_pref.csv (default None = off, outputs as before)")\n'
    '    ap.add_argument("--e2_model_sha", default=None, help="145: expected sha256 of --e2_model (stop on mismatch)"); ap.add_argument("--e2_hedge", type=int, default=0, choices=[0, 1])\n'
    '    ap.add_argument("--e2_dump", type=int, default=0, choices=[0, 1], help="145: also write the E2 tables (e2_ewin.parquet / e2_feats.parquet) for the parity check")\n'
    '    ap.add_argument("--e2_bio", default="bio_structures.parquet"); ap.add_argument("--e2_pcl", default="pubchemlite_annotations.parquet"); ap.add_argument("--e2_structs", default="train_structs.parquet")\n'
    '    ap.add_argument("--gl_json", default=None,')
# 3. engine setup (after the evaluation-mode masks)
rep('        if EXCL_ROWS or EXCL_IDS or MASK: log(f"EVALUATION MODE: global masks {len(EXCL_ROWS)} rows / {len(EXCL_IDS)} identities; per-molecule masks for {len(MASK)} molecules")\n',
    '        if EXCL_ROWS or EXCL_IDS or MASK: log(f"EVALUATION MODE: global masks {len(EXCL_ROWS)} rows / {len(EXCL_IDS)} identities; per-molecule masks for {len(MASK)} molecules")\n'
    '        E2 = None; E2_ORDER = {}; E2_TAB = []; E2_FAIL = []; E2_MAN = None\n'
    '        if args.e2_model:   # 145: E2 engine on the same queries / FPNet logits / library index / analog store as P\n'
    '            import hashlib as _hl2, lightgbm as _lgb2\n'
    '            from e2_engine import EStores, E2Engine\n'
    '            from rdkit import Chem as _Ch2\n'
    '            from rdkit.Chem import rdFingerprintGenerator as _rfg2\n'
    '            assert ANA_STORE is not None, "145: E2 needs the analog store of the v8w7a configuration"\n'
    '            assert not EXCL_IDS and not any(m_.get("ids") for m_ in MASK.values()), "145: E2 supports the test regime and the C1 evaluation view only"\n'
    '            def _sha2(p_):\n'
    '                with open(p_, "rb") as fh_: return _hl2.sha256(fh_.read()).hexdigest()\n'
    '            def _res2(name_):   # a file given by name: the path itself, else a unique file under /kaggle/input (Kaggle) or data/external_kaggle (local); several hits must be byte-identical\n'
    '                if os.path.exists(name_): return os.path.abspath(name_)\n'
    '                root_ = "/kaggle/input" if KAGGLE else os.path.join(os.environ.get("CASMI_ROOT", r"C:\\kaggle\\CASMI" if os.name == "nt" else os.path.expanduser("~/CASMI2026")), "data", "external_kaggle")\n'
    '                hits_ = sorted(glob.glob(os.path.join(root_, "**", os.path.basename(name_)), recursive=True))\n'
    '                if not hits_: raise FileNotFoundError(name_)\n'
    '                if len(hits_) > 1 and len({_sha2(h_) for h_ in hits_}) > 1: raise SystemExit(f"145: ambiguous E2 input {name_}: {hits_}")\n'
    '                return hits_[0]\n'
    '            _e2m = _res2(args.e2_model); _e2ms = _sha2(_e2m)\n'
    '            if args.e2_model_sha and _e2ms != args.e2_model_sha: raise SystemExit(f"145: E2 model sha256 {_e2ms} != expected {args.e2_model_sha}")\n'
    '            _e2b = _lgb2.Booster(model_file=_e2m); _bio_p, _pcl_p, _str_p = _res2(args.e2_bio), _res2(args.e2_pcl), _res2(args.e2_structs)\n'
    '            _pcl_rows = pl.read_parquet(_pcl_p, columns=["tier_row"]).filter(pl.col("tier_row") >= 0)["tier_row"].unique().to_numpy()\n'
    '            _bio = pl.read_parquet(_bio_p, columns=["smiles", "monoisotopic_mass"]).drop_nulls()\n'
    '            _ts2 = pd.read_parquet(_str_p, columns=["key", "smiles"]).drop_duplicates("key"); _key_smi2 = dict(zip(_ts2.key.astype(str), _ts2.smiles.astype(str)))\n'
    '            _mg2 = _rfg2.GetMorganGenerator(radius=2, fpSize=2048); _mfpc2 = {}\n'
    '            def _mfp2(s_):\n'
    '                if s_ not in _mfpc2:\n'
    '                    m_ = _Ch2.MolFromSmiles(s_) if s_ else None; _mfpc2[s_] = _mg2.GetFingerprint(m_) if m_ is not None else None\n'
    '                return _mfpc2[s_]\n'
    '            _K2S = dict(zip(pool.filter(pl.col("src").is_in([1, 3]))["key"].to_list(), pool.filter(pl.col("src").is_in([1, 3]))["smiles"].to_list()))\n'
    '            def _alias2(tk_, raw_):   # evaluation C1 view only: the truth key\'s tautomer raw keys (as b1_ewin)\n'
    '                keys_ = {raw_} if raw_ else set(); smi_ = _K2S.get(tk_, "")\n'
    '                if not smi_: return keys_\n'
    '                try:\n'
    '                    m_ = _Ch2.MolFromSmiles(smi_); _Ch2.RemoveStereochemistry(m_)\n'
    '                    for t_ in TAUT.Enumerate(m_):\n'
    '                        try: keys_.add(_Ch2.MolToInchiKey(t_)[:14])\n'
    '                        except Exception: pass\n'
    '                except Exception: pass\n'
    '                return keys_\n'
    '            E2 = E2Engine(EStores(tmass, toff, tbuf, _pcl_rows, pool, CMASS, CSMI, _bio), _e2b, key_rows, lambda x_: spectrum(int(x_)), lib_of_row, add_of_row, mode_of_row, prec_of_row, ANA_STORE, _key_smi2, _mfp2)\n'
    '            E2_MAN = dict(model=_e2m, model_sha256=_e2ms, expected_sha_given=bool(args.e2_model_sha), trees=_e2b.num_trees(), feats=list(_e2b.feature_name()), K=10.0, alpha=0.5, hedge=args.e2_hedge,\n'
    '                          bio=_bio_p, bio_sha256=_sha2(_bio_p), pcl=_pcl_p, pcl_sha256=_sha2(_pcl_p), structs=_str_p, structs_sha256=_sha2(_str_p), pcl_tier_rows=int(len(_pcl_rows)), bio_rows=int(_bio.height),\n'
    '                          coconut=int(len(CMASS)) if CMASS is not None else 0)\n'
    '            log(f"145 E2: model {_e2m} ({_e2ms[:12]}, {_e2b.num_trees()} trees), PCL tier rows {len(_pcl_rows):,}, BIO {_bio.height:,}, COCONUT {E2_MAN[\'coconut\']:,}, hedge {args.e2_hedge}")\n')
# 4. per-molecule E2 order (read only)
rep("            feats[mid] = rows\n",
    "            feats[mid] = rows\n"
    "            if E2 is not None:   # 145: the E2 order of this molecule from the same q / M_by_add / zlog (P's rows untouched)\n"
    "                try:\n"
    "                    _c1t = (same_lib.get('identity'), _alias2(same_lib.get('identity'), str(mid)), same_lib.get('lib')) if same_lib else None\n"
    "                    def _fm2(sm_, _z=zlog):\n"
    "                        res_ = wp.map(_feat, [(sm_[i_:i_ + 400], _z) for i_ in range(0, len(sm_), 400)]); return [k_ for r_ in res_ for k_ in r_[0]], (np.concatenate([r_[1] for r_ in res_]) if res_ else np.zeros(0, np.float32))\n"
    "                    _om2 = lambda sm_: [k_ for r_ in wp.map(_okey, [sm_[i_:i_ + 200] for i_ in range(0, len(sm_), 200)]) for k_ in r_]\n"
    "                    _Et, _Ft = E2.tables(q, M_by_add, _fm2, _om2, lambda t_: wp.map(_e2frag, t_), query_rows=frozenset(int(x_) for x_ in excl_rows), c1_truth=_c1t, mol_id=str(mid))\n"
    "                    E2_ORDER[str(mid)] = (E2.rank(_Et, _Ft), dict(zip(_Et.official_key.astype(str), _Et.smiles.astype(str))) if _Et is not None else {})\n"
    "                    if args.e2_dump and _Et is not None: E2_TAB.append((_Et, _Ft))\n"
    "                except Exception as e_:\n"
    "                    E2_FAIL.append(str(mid)); log('145 E2 failed for', mid, repr(e_))\n")
# 5. hook
rep("    def _fusion_pass(LAM, fused_stats):",
    "    E2_OUT, E2_ST = {}, []\n"
    "    def _e2_hook(mid, rows, order):   # 145: F (or H) from the final main order of one molecule; writes only E2_OUT / E2_ST\n"
    "        import e2_engine as _E2M\n"
    "        o_ = [int(i) for i in order]; p_ = [rows[i]['key'] for i in o_[:25]]; smi_ = {rows[i]['key']: rows[i]['smiles'] for i in o_}\n"
    "        assert all(p_) and len(set(p_)) == len(p_), '145: P keys must be non-null and unique'\n"
    "        el_, esmi_ = E2_ORDER.get(str(mid), ([], {})); er_ = {k_: i_ + 1 for i_, k_ in enumerate(el_)}\n"
    "        assert _E2M.fuse_rrf(p_, er_, el_[:25], 0.0) == p_, '145: alpha 0 does not reproduce P'\n"
    "        F_ = _E2M.fuse_rrf(p_, er_, el_[:25], 0.5)\n"
    "        if args.e2_hedge: F_ = _E2M.insert2(F_, el_[0] if el_ else None)\n"
    "        assert el_ or F_ == p_, '145: E2 empty but the list changed'\n"
    "        out_ = [smi_.get(k_) or esmi_.get(k_) for k_ in F_]; assert all(out_), '145: a fused key without SMILES'\n"
    "        E2_OUT[str(mid)] = ';'.join(out_)\n"
    "        E2_ST.append(dict(molecule=str(mid), n_p=len(p_), n_e2=len(el_), top1_changed=int(F_[0] != p_[0]), top25_changed=int(F_ != p_), new_keys=len(set(F_) - set(p_)),\n"
    "                          e2_top1_p_rank=(p_.index(el_[0]) + 1 if el_ and el_[0] in p_ else 0), failed=int(str(mid) in E2_FAIL)))\n"
    "    def _fusion_pass(LAM, fused_stats, hook=None):")
rep('                sub_probe[name_].append((mid, ";".join(rows[i]["smiles"] for i in kept_[:25]) if kept_ else "CCO"))\n        return sub, sub_fixed, sub_probe',
    '                sub_probe[name_].append((mid, ";".join(rows[i]["smiles"] for i in kept_[:25]) if kept_ else "CCO"))\n'
    '            if hook is not None: hook(mid, rows, order)   # 145 E2 (read only; None = the pop0 / v8w7a loop)\n'
    '        return sub, sub_fixed, sub_probe')
rep("    sub, sub_fixed, sub_probe = _fusion_pass(LAM if args.lam_fixed is None else args.lam_fixed, fused_stats)",
    "    sub, sub_fixed, sub_probe = _fusion_pass(LAM if args.lam_fixed is None else args.lam_fixed, fused_stats, hook=(_e2_hook if E2 is not None else None))")
# 6. outputs
rep('    df = pd.DataFrame(sub, columns=["molecule_id", "smiles"]); df.to_csv(f"{P[\'work\']}/submission.csv", index=False)',
    '    sub_pref = None\n'
    '    if E2 is not None:   # 145: submission.csv = F (or H); submission_pref.csv = the main list P of this run\n'
    '        _need = [str(m_) for m_ in all_ids if feats.get(str(m_))]\n'
    '        assert all(m_ in E2_OUT for m_ in _need) and len(E2_OUT) == len(_need), ("145: F missing for some molecules with candidates", len(E2_OUT), len(_need))\n'
    '        sub_pref = sub; sub = [(m_, E2_OUT.get(str(m_), s_)) for m_, s_ in sub_pref]\n'
    '        pd.DataFrame(sub_pref, columns=["molecule_id", "smiles"]).to_csv(f"{P[\'work\']}/submission_pref.csv", index=False)\n'
    '        _st2 = pd.DataFrame(E2_ST, columns=["molecule", "n_p", "n_e2", "top1_changed", "top25_changed", "new_keys", "e2_top1_p_rank", "failed"]); _st2.to_csv(f"{P[\'work\']}/e2_stats.csv", index=False)\n'
    '        if args.e2_dump and E2_TAB:\n'
    '            pd.concat([e_ for e_, _ in E2_TAB], ignore_index=True).to_parquet(f"{P[\'work\']}/e2_ewin.parquet", index=False); pd.concat([f_ for _, f_ in E2_TAB], ignore_index=True).to_parquet(f"{P[\'work\']}/e2_feats.parquet", index=False)\n'
    '        E2_MAN.update(molecules=len(_need), e2_nonempty=int((_st2.n_e2 > 0).sum()), e2_failed=len(E2_FAIL), top1_changed=int(_st2.top1_changed.sum()), top25_changed=int(_st2.top25_changed.sum()),\n'
    '                      new_keys_mols=int((_st2.new_keys > 0).sum()), lists_changed=int(sum(a_ != b_ for (_, a_), (_, b_) in zip(sub, sub_pref))))\n'
    '        log(f"145 E2: {E2_MAN[\'molecules\']} molecules, E2 non-empty {E2_MAN[\'e2_nonempty\']}, failed {E2_MAN[\'e2_failed\']}, rank-1 changed {E2_MAN[\'top1_changed\']}, lists changed {E2_MAN[\'lists_changed\']}")\n'
    '    df = pd.DataFrame(sub, columns=["molecule_id", "smiles"]); df.to_csv(f"{P[\'work\']}/submission.csv", index=False)')
rep("fusion_lamref=dict(fused_stats_ref)),", "fusion_lamref=dict(fused_stats_ref), e2=E2_MAN),")
rep("        out_ = dict(official_mrr25=official, official_mrr25_fixed=official_fixed,",
    "        official_pref = _score(pd.DataFrame(sub_pref, columns=['molecule_id', 'smiles']))[0] if sub_pref is not None else None   # 145: main list P of the same run\n"
    "        if official_pref is not None: log(f'145: OFFICIAL MRR@25 of F {official:.4f} vs the main list P {official_pref:.4f}')\n"
    "        out_ = dict(official_mrr25=official, official_mrr25_pref=official_pref, official_mrr25_fixed=official_fixed,")
open(os.path.join(HERE, "b1_pipeline.py"), "w", encoding="utf-8").write(t)
import ast
ast.parse(t)
print("wrote", os.path.join(HERE, "b1_pipeline.py"), hashlib.sha256(t.encode()).hexdigest()[:12], f"{len(t) - len(s):+d} chars vs pop0")
