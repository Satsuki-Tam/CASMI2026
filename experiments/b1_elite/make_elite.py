"""132 (one-shot Public comparison, 132_prereg_elite_public.md): the pipeline of the submitted v8w7a list (experiments/b1_pop0, sha 365fe307 =
the frozen v7f fusion loop moved verbatim into _fusion_pass; default arguments = v8w7a) with ONE addition, the fixed E-lite RRF of 102
(rrf_rank_e1r_0.5, elite.py) applied to the final main order of every molecule:
  --elite_model (rank_e1r lambdarank.txt) --elite_keys (E key v2 parquet) [--elite_k 10 --elite_alpha 0.5 --elite_model_sha --elite_keys_sha]
  -> submission.csv = the E-lite list; submission_pref.csv = the main list P of the same run; elite_stats.csv per molecule; manifest 'elite'.
Construction: _fusion_pass gets a keyword hook (default None) that is called once per molecule with candidates at the END of the loop body
(after the main list and its probes are appended) and only reads; the loop is otherwise the pop0 loop node for node (checked on the AST).
Without --elite_model the run is the pop0 / v8w7a run (hook None; outputs as before). Molecules without candidates keep the placeholder.
Usage: python -X utf8 experiments/b1_elite/make_elite.py   (writes experiments/b1_elite/b1_pipeline.py + copies; prints the checks)"""
import ast, copy, hashlib, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "b1_pop0")
for f in ("b1_common.py", "b1_analog.py", "b1_frag.py", "b1_rankfeats.py"):
    shutil.copy(os.path.join(SRC, f), os.path.join(HERE, f))
s = open(os.path.join(SRC, "b1_pipeline.py"), encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("365fe30737af"), "pop0 pipeline changed"
t = s


def rep(old, new, count=1):
    global t
    assert t.count(old) == count, (old[:80], t.count(old)); t = t.replace(old, new)


# 1. arguments
rep('    ap.add_argument("--gl_json", default=None,',
    '    ap.add_argument("--elite_model", default=None, help="132: E-lite second engine (102 rank_e1r lambdarank.txt); submission.csv = the fixed identity RRF of the final main order with E (elite.py), the main list = submission_pref.csv (default None = off, outputs as before)")\n'
    '    ap.add_argument("--elite_keys", default=None, help="132: E key v2 parquet (column key = official keys of PubChemLite / BIO); E = in_coconut | in_train | key in this set")\n'
    '    ap.add_argument("--elite_k", type=float, default=10.0); ap.add_argument("--elite_alpha", type=float, default=0.5)\n'
    '    ap.add_argument("--elite_model_sha", default=None, help="132: expected sha256 of --elite_model (stop on mismatch)"); ap.add_argument("--elite_keys_sha", default=None, help="132: expected sha256 of --elite_keys")\n'
    '    ap.add_argument("--gl_json", default=None,')
# 2. E-lite setup + hook (defined before _fusion_pass; reads molinfo / args at call time)
SETUP = '''    ELITE, ELITE_OUT, ELITE_ST, ELITE_MAN = None, {}, [], None
    if args.elite_model:   # 132: fixed E-lite RRF (102 rrf_rank_e1r_0.5) on the final main order of every molecule
        assert args.elite_keys and args.lam_fixed is None, "132: --elite_model needs --elite_keys and no --lam_fixed"
        import hashlib as _hl, lightgbm as _lgb
        import elite as EL
        from b1_rankfeats import feature_matrix as _fm_e
        assert args.elite_k == 10.0 and args.elite_alpha == 0.5, "132: only the registered K 10 / alpha 0.5"   # Codex 132: the registered combination
        assert not args.pcl_boost and args.twin_tau is None, "132: pcl_boost / twin_tau must be off (the hook reads the final main order)"
        assert booster is not None, "132: the main ranker must be loaded"
        def _sha(p_):
            with open(p_, "rb") as fh_: return _hl.sha256(fh_.read()).hexdigest()
        def _res(p_, want_):   # Kaggle: a dataset file is found by its name under /kaggle/input; several hits -> the one with the expected sha256, else stop (Codex 132)
            if os.path.exists(p_) or not KAGGLE: return os.path.abspath(p_)
            hits_ = sorted(glob.glob(os.path.join("/kaggle/input", "**", os.path.basename(p_)), recursive=True))
            if not hits_: raise FileNotFoundError(p_)
            if len(hits_) == 1: return hits_[0]
            ok_ = [h_ for h_ in hits_ if want_ and _sha(h_) == want_]
            if len(ok_) != 1: raise SystemExit(f"132: ambiguous E input {os.path.basename(p_)}: {hits_}")
            return ok_[0]
        _em, _ek = _res(args.elite_model, args.elite_model_sha), _res(args.elite_keys, args.elite_keys_sha); _ems, _eks = _sha(_em), _sha(_ek)
        if args.elite_model_sha and _ems != args.elite_model_sha: raise SystemExit(f"132: E model sha256 {_ems} != expected {args.elite_model_sha}")
        if args.elite_keys_sha and _eks != args.elite_keys_sha: raise SystemExit(f"132: E keys sha256 {_eks} != expected {args.elite_keys_sha}")
        _eb = _lgb.Booster(model_file=_em); _ekeys = pd.read_parquet(_ek, columns=["key"]).key.astype(str)
        ELITE = dict(booster=_eb, feats=list(_eb.feature_name()), keys=set(_ekeys))
        ELITE_MAN = dict(model=_em, model_sha256=_ems, keys=_ek, keys_sha256=_eks, n_keys=len(ELITE["keys"]), K=args.elite_k, alpha=args.elite_alpha, feats=ELITE["feats"], trees=_eb.num_trees(),
                         expected_shas_given=bool(args.elite_model_sha and args.elite_keys_sha), pcl_boost=args.pcl_boost, twin_tau=args.twin_tau)
        log(f"132 E-lite: model {_em} ({_ems[:12]}, {_eb.num_trees()} trees, {len(ELITE['feats'])} features), E keys {len(ELITE['keys']):,} ({_eks[:12]}), K {args.elite_k} alpha {args.elite_alpha}")
    def _elite_hook(mid, rows, order, fp, g, pop, lib):   # 132: reads the final main order of one molecule; writes only ELITE_OUT / ELITE_ST
        mi_ = molinfo.get(str(mid), dict(n_query=1, ce_known=0.0))
        new_, es_, ne_ = EL.fused_order(ELITE["booster"], ELITE["feats"], _fm_e, ELITE["keys"], rows, order, fp, g, pop, lib, mi_["n_query"], mi_["ce_known"],
                                        mi_.get("n_unique", np.nan), args.elite_k, args.elite_alpha)
        o_ = [int(i) for i in order]
        assert EL.rrf(o_, es_, args.elite_k, 0.0) == o_, "132: alpha 0 does not reproduce the main order"
        assert sorted(new_) == sorted(o_), "132: the E-lite list changed the candidate set"
        assert 0 <= ne_ <= len(o_) and (ne_ > 0 or new_ == o_), "132: E empty but the list changed"   # Codex 132
        _k = [r["key"] for r in rows]; assert all(_k) and len(set(_k)) == len(_k), "132: candidate official keys must be non-null and unique"
        ELITE_OUT[str(mid)] = ";".join(rows[i]["smiles"] for i in new_[:25])
        ELITE_ST.append(dict(molecule=str(mid), n_cand=len(rows), n_e=ne_, top1_changed=int(new_[0] != o_[0]), top25_changed=int(new_[:25] != o_[:25]),
                             main_top1_in_e=int(o_[0] in set(es_)), e_top1_main_rank=(o_.index(es_[0]) + 1 if es_ else 0), new_top1_main_rank=o_.index(new_[0]) + 1))
'''
rep("    def _fusion_pass(LAM, fused_stats):   # pop0 (116/124)", SETUP + "    def _fusion_pass(LAM, fused_stats, hook=None):   # pop0 (116/124)")
# 3. the hook call at the end of the loop body
probe_line = '                sub_probe[name_].append((mid, ";".join(rows[i]["smiles"] for i in kept_[:25]) if kept_ else "CCO"))\n'
rep(probe_line, probe_line + '            if hook is not None: hook(mid, rows, order, fp, g, pop, lib)   # 132 E-lite (read only; None = the pop0 / v8w7a loop)\n')
# 4. the main pass passes the hook
rep("    sub, sub_fixed, sub_probe = _fusion_pass(LAM if args.lam_fixed is None else args.lam_fixed, fused_stats)",
    "    sub, sub_fixed, sub_probe = _fusion_pass(LAM if args.lam_fixed is None else args.lam_fixed, fused_stats, hook=(_elite_hook if ELITE is not None else None))")
# 5. outputs
OUT = '''    sub_pref = None
    if ELITE is not None:   # 132: submission.csv = the E-lite list; submission_pref.csv = the main list P of this run
        _need = [str(m_) for m_ in all_ids if feats.get(str(m_))]
        assert all(m_ in ELITE_OUT for m_ in _need) and len(ELITE_OUT) == len(_need), ("132: E-lite list missing for some molecules with candidates", len(ELITE_OUT), len(_need))
        sub_pref = sub; sub = [(m_, ELITE_OUT.get(str(m_), s_)) for m_, s_ in sub_pref]
        pd.DataFrame(sub_pref, columns=["molecule_id", "smiles"]).to_csv(f"{P['work']}/submission_pref.csv", index=False)
        _st = pd.DataFrame(ELITE_ST, columns=["molecule", "n_cand", "n_e", "top1_changed", "top25_changed", "main_top1_in_e", "e_top1_main_rank", "new_top1_main_rank"]); _st.to_csv(f"{P['work']}/elite_stats.csv", index=False)
        ELITE_MAN.update(molecules=len(_need), e_nonempty=int((_st.n_e > 0).sum()) if len(_st) else 0, e_size_median=float(_st.n_e.median()) if len(_st) else 0.0,
                         cand_median=float(_st.n_cand.median()) if len(_st) else 0.0, top1_changed=int(_st.top1_changed.sum()) if len(_st) else 0,
                         top25_changed=int(_st.top25_changed.sum()) if len(_st) else 0, lists_changed=int(sum(a_ != b_ for (_, a_), (_, b_) in zip(sub, sub_pref))))
        log(f"132 E-lite: {ELITE_MAN['molecules']} molecules, E non-empty {ELITE_MAN['e_nonempty']}, median E {ELITE_MAN['e_size_median']:.0f} of {ELITE_MAN['cand_median']:.0f}, rank-1 changed {ELITE_MAN['top1_changed']}, lists changed {ELITE_MAN['lists_changed']}")
'''
df_line = '    df = pd.DataFrame(sub, columns=["molecule_id", "smiles"]); df.to_csv(f"{P[\'work\']}/submission.csv", index=False)\n'
rep(df_line, OUT + df_line)
# 6. manifest
rep("fusion_lamref=dict(fused_stats_ref)),", "fusion_lamref=dict(fused_stats_ref), elite=ELITE_MAN),")
# 7. local scoring: also the main list of the run
sc_line = "        official, per = _score(df); official_fixed, per_fixed = _score(df_fixed)\n"
rep(sc_line, sc_line + "        official_pref = _score(pd.DataFrame(sub_pref, columns=[\"molecule_id\", \"smiles\"]))[0] if sub_pref is not None else None   # 132: main list P of the same run\n")
rep("        out_ = dict(official_mrr25=official, official_mrr25_fixed=official_fixed,", "        out_ = dict(official_mrr25=official, official_mrr25_pref=official_pref, official_mrr25_fixed=official_fixed,")
rep('        log(f"OFFICIAL MRR@25 = {official:.4f} (main', '        if official_pref is not None: log(f"132: OFFICIAL MRR@25 of the E-lite list {official:.4f} vs the main list P {official_pref:.4f}")\n        log(f"OFFICIAL MRR@25 = {official:.4f} (main')
open(os.path.join(HERE, "b1_pipeline.py"), "w", encoding="utf-8", newline="\n").write(t)


# ---- AST checks: the fusion loop = the pop0 loop plus exactly one trailing `if hook is not None: hook(...)`; _fusion_pass signature; other statements of _fusion_pass unchanged
def main_fn(src): return next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "main")


mo, mn = main_fn(s), main_fn(t)
fpo = next(n for n in mo.body if isinstance(n, ast.FunctionDef) and n.name == "_fusion_pass"); fpn = next(n for n in mn.body if isinstance(n, ast.FunctionDef) and n.name == "_fusion_pass")
lo = next(n for n in fpo.body if isinstance(n, ast.For)); ln = next(n for n in fpn.body if isinstance(n, ast.For))
last = ln.body[-1]
assert isinstance(last, ast.If) and ast.unparse(last.test) == "hook is not None" and len(last.body) == 1 and ast.unparse(last.body[0]) == "hook(mid, rows, order, fp, g, pop, lib)" and not last.orelse
ln2 = copy.deepcopy(ln); ln2.body = ln2.body[:-1]
assert ast.dump(lo) == ast.dump(ln2), "the fusion loop differs from the pop0 loop beyond the hook"
assert [a.arg for a in fpn.args.args] == ["LAM", "fused_stats", "hook"] and [ast.unparse(d) for d in fpn.args.defaults] == ["None"]
assert [ast.dump(x) for x in fpo.body if x is not lo] == [ast.dump(x) for x in fpn.body if x is not ln], "_fusion_pass statements outside the loop changed"
print("loop identical to pop0 except the trailing hook; _fusion_pass signature (LAM, fused_stats, hook=None)")
print("main statements: pop0", len(mo.body), "elite", len(mn.body))
print("b1_pipeline.py sha256", hashlib.sha256(t.encode()).hexdigest())
print("elite.py sha256", hashlib.sha256(open(os.path.join(HERE, "elite.py"), "rb").read()).hexdigest())
