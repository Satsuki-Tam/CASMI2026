"""132 parity (A) (132_prereg_elite_public.md): writes gen_eval2fd_e132.py = a copy of the 102/104 evaluator gen_eval2fd.py (Spark version,
sha256 5f3cded6...; the original is not touched) with ONE added block: for every E model, every (set, view, molecule) the shared function of the
submission pipeline (experiments/b1_elite/elite.py) is applied to the evaluator's own inputs and must reproduce, exactly,
  the E rows, the E feature matrix (NaN-aware equality), the E order, the full RRF orders for alpha 0.5 and 1.0, and the main order for alpha 0;
any difference stops the run (AssertionError). Counts go to <out>_e132check.json. The variant columns are written as before, so the run's CSV
can be compared row by row with the stored 102 CSVs (x132a_compare.py).
Usage (Spark, repo root): python -X utf8 experiments/b1_elite/make_ge132.py experiments/b1_baseline/gen_eval2fd.py experiments/b1_baseline/gen_eval2fd_e132.py"""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("5f3cded6917b"), "unexpected gen_eval2fd.py version"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep("    import lightgbm as lgb\n",
    "    import lightgbm as lgb\n"
    "    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), \"experiments\", \"b1_elite\")); import elite as EL   # 132 (A)\n"
    "    from collections import Counter as _Ctr; ELC = _Ctr()\n")
anchor = '                            for al_ in (0.5, 1.0): out[f"rrf_{t_}_{al_}"] = rr_of(_rrf(es_, al_))\n'
CHECK = '''                            # 132 (A): the submission pipeline's shared function on this evaluator's inputs must reproduce the 102 definition exactly
                            ei2_ = np.flatnonzero(EL.e_mask(g.in_coconut.values, g[f"in_train_{vv}"].values, okeys, EKS))
                            assert np.array_equal(ei2_, ei_), ("132A: E rows differ", s, v, mid)
                            es2_ = []
                            if len(ei2_):
                                XE2_ = EL.e_matrix(feature_matrix, list(emod_.feature_name()), ei2_, fp, glv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values,
                                                   g.src_mask.values, g.lotus_refs.values, lib, g[f"lib_same_{vv}"].values, g[f"lib_nref_{vv}"].values, g.in_tier.values,
                                                   g[f"in_train_{vv}"].values, g.in_coconut.values, g.ppm_err.values, g.fp_rank_window.values, float(M.loc[mid, "n_query"]),
                                                   float(M.loc[mid, "ce_known"]), float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan, feats["ap"], feats["mean_tan"])
                                assert XE2_.shape == XE.shape and np.array_equal(XE2_, XE, equal_nan=True), ("132A: E feature matrix differs", s, v, mid)
                                es2_ = EL.e_rank(emod_, XE2_, ei2_, pos_m)
                            assert es2_ == [int(i) for i in es_], ("132A: E order differs", s, v, mid)
                            o_main_ = [int(i) for i in order]
                            for al_ in (0.5, 1.0):
                                assert EL.rrf(o_main_, es2_, a.rrf_k, al_) == [int(i_) for _, i_ in _rrf(es_, al_)], ("132A: RRF order differs", al_, s, v, mid)
                            assert EL.rrf(o_main_, es2_, a.rrf_k, 0.0) == o_main_, ("132A: alpha 0 does not give the main order", s, v, mid)
                            ELC[f"{t_}|{v}|n"] += 1; ELC[f"{t_}|{v}|e_nonempty"] += int(len(ei2_) > 0); ELC[f"{t_}|{v}|gl_ok"] += int(gl_ok); ELC[f"{t_}|{v}|fallback"] += int(not gl_ok)
                            ELC[f"{t_}|{v}|truth_outside_e"] += int(bool(tr.any()) and not bool(tr[ei_].any() if len(ei_) else False)); ELC[f"{t_}|{v}|top1_changed"] += int(EL.rrf(o_main_, es2_, a.rrf_k, 0.5)[0] != o_main_[0])
'''
rep(anchor, anchor + CHECK)
# write the counts next to the run's other outputs
rep("    if a.dump_choice: pd.DataFrame(choice).to_parquet(",
    "    json.dump(dict(ELC), open(os.path.join(HERE, OUTS[0] + \"_e132check.json\"), \"w\"), indent=1); log(f\"132A check counts {dict(ELC)}\")   # 132 (A)\n"
    "    if a.dump_choice: pd.DataFrame(choice).to_parquet(")
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", dst, hashlib.sha256(t.encode()).hexdigest())
