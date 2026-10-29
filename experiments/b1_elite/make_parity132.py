"""132 parity (B) (132_prereg_elite_public.md): writes experiments/b1_elite/b1_parity_e132.py = experiments/b1_baseline/b1_parity.py (sha 7cfb5eee,
the 087 parity: pipeline vs evaluator path on the panel, both views) with the E-lite replay added on the evaluator path:
  --elite_model / --elite_keys / --elite_k / --elite_alpha and --pred_elite (the pipeline's submission.csv = the E-lite list; --pred_main is then
  the pipeline's submission_pref.csv = P). After the evaluator-side main score of a molecule is final, its full order is fused with E by the shared
  function (experiments/b1_elite/elite.py) on the table rows (E = in_coconut | in_train_<view> | official key in the E keys; analog features from
  --analog_parquet), and compared with the pipeline's E-lite list: ordered top-25 official identities, top-1, RR. The E membership of every candidate
  shared by the table and the pipeline dump is compared too (dump: in_coconut | in_train | key in the E keys).
  Strata covered are counted (E empty, truth outside E, negative-ion only, strong class-1 reference lib_max_c1 >= 0.9 in view c1, GL fallback).
  FAIL unless every molecule agrees (ordered top-25, top-1, RR) and every shared candidate has the same E membership.
Usage: python -X utf8 experiments/b1_elite/make_parity132.py"""
import hashlib, os
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "b1_baseline", "b1_parity.py")
s = open(SRC, encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("7cfb5eeef914"), "b1_parity.py changed"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep("HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE);",
    "HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \"b1_baseline\"); sys.path.insert(0, HERE); sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)));")
rep('ap.add_argument("--pipe_work", default=None,',
    'ap.add_argument("--elite_model", default=None, help="132 (B): E-lite model; the evaluator path replays the E-lite RRF (elite.py) and compares it with --pred_elite")\n'
    'ap.add_argument("--elite_keys", default=None); ap.add_argument("--elite_k", type=float, default=10.0); ap.add_argument("--elite_alpha", type=float, default=0.5)\n'
    'ap.add_argument("--pred_elite", default=None, help="132 (B): the pipeline\'s E-lite list (its submission.csv; --pred_main = its submission_pref.csv)")\n'
    'ap.add_argument("--pipe_work", default=None,')
rep('    stats = dict(n=0, top1_main=0, top1_ins=0, rr_main=0, rr_ins=0, top25_main=0, top25_ins=0, set25_main=0, set25_ins=0, fallback_eval=0)\n',
    '    stats = dict(n=0, top1_main=0, top1_ins=0, rr_main=0, rr_ins=0, top25_main=0, top25_ins=0, set25_main=0, set25_ins=0, fallback_eval=0)\n'
    '    EL = None\n'
    '    if a.elite_model:   # 132 (B)\n'
    '        import elite as EL\n'
    '        EBST = lgb.Booster(model_file=a.elite_model); EFEATS = list(EBST.feature_name()); EKS = set(pd.read_parquet(a.elite_keys, columns=["key"]).key.astype(str))\n'
    '        PE = pd.read_csv(a.pred_elite); PE["molecule_id"] = PE.molecule_id.astype(str); pe_of = dict(zip(PE.molecule_id, PE.smiles.astype(str)))\n'
    '        stats.update(n_el=0, top1_el=0, rr_el=0, top25_el=0, emem_cands=0, emem_mismatch=0, e_empty=0, truth_outside_e=0, neg_only=0, strong_c1=0, fallback_el=0, el_top1_changed=0)\n'
    '        EL_BAD = []\n')
rep('            ev_main = [ident(str(g.smiles.values[i])) for i in np.argsort(-main, kind="stable")[:25]];',
    '            if EL is not None:   # 132 (B): the E-lite RRF on the evaluator path, compared with the pipeline\'s E-lite list\n'
    '                o_ = [int(i) for i in np.argsort(-main, kind="stable")]; okeys_ = g.official_key.astype(str).values\n'
    '                em_ = EL.e_mask(g.in_coconut.values, g[f"in_train_{v}"].values, okeys_, EKS); ei_ = np.flatnonzero(em_); es_ = []\n'
    '                if len(ei_):\n'
    '                    assert mid in ANA_MT, (mid, "analog features missing for the E-lite replay")\n'
    '                    XE_ = EL.e_matrix(feature_matrix, EFEATS, ei_, fp, glv, pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib,\n'
    '                                      g[f"lib_same_{v}"].values, g[f"lib_nref_{v}"].values, g.in_tier.values, g[f"in_train_{v}"].values, g.in_coconut.values, g.ppm_err.values, g.fp_rank_window.values,\n'
    '                                      float(Mall.loc[mid, "n_query"]), float(Mall.loc[mid, "ce_known"]), float(Mall.loc[mid, "n_unique"]) if "n_unique" in Mall.columns else np.nan,\n'
    '                                      [ANA_MT[mid][0][str(sm)] for sm in g.smiles], [ANA_MT[mid][1][str(sm)] for sm in g.smiles])\n'
    '                    es_ = EL.e_rank(EBST, XE_, ei_, EL.positions(o_, len(g)))\n'
    '                new_ = EL.rrf(o_, es_, a.elite_k, a.elite_alpha); assert EL.rrf(o_, es_, a.elite_k, 0.0) == o_\n'
    '                ev_el = [ident(str(g.smiles.values[i])) for i in new_[:25]]; pp_el = [ident(x) for x in pe_of[mid].split(";")]\n'
    '                stats["n_el"] += 1; stats["top1_el"] += ev_el[0] == pp_el[0]; stats["top25_el"] += ev_el == pp_el; stats["el_top1_changed"] += int(new_[0] != o_[0])\n'
    '                stats["rr_el"] += metric.per_molecule_reciprocal_rank(truth_of[mid], pe_of[mid].split(";")) == metric.per_molecule_reciprocal_rank(truth_of[mid], [str(g.smiles.values[i]) for i in new_[:25]])\n'
    '                if ev_el != pp_el: EL_BAD.append(mid)\n'
    '                dm_ = D[D.molecule == mid].drop_duplicates("key"); pk_ = set(dm_.key.astype(str))\n'
    '                ep_ = {k_ for k_, c_, t_ in zip(dm_.key.astype(str), dm_.in_coconut.astype(bool), dm_.in_train.astype(bool)) if c_ or t_ or k_ in EKS}\n'
    '                ef_ = {okeys_[i] for i in ei_}; sh_ = set(okeys_) & pk_\n'
    '                stats["emem_cands"] += len(sh_); stats["emem_mismatch"] += len((ef_ & sh_) ^ (ep_ & sh_))\n'
    '                tk_ = set(okeys_[g.is_truth.values.astype(bool)]) if "is_truth" in g.columns else set()\n'
    '                stats["e_empty"] += int(len(ei_) == 0); stats["truth_outside_e"] += int(bool(tk_) and not (tk_ & ef_)); stats["fallback_el"] += int(not gl_ok_)\n'
    '                stats["neg_only"] += int(all(str(x_).endswith("-") for x_ in str(Mall.loc[mid, "adducts"]).split("|")))\n'
    '                stats["strong_c1"] += int(v == "c1" and float(Mall.loc[mid, "lib_max_c1"]) >= 0.9)\n'
    '            ev_main = [ident(str(g.smiles.values[i])) for i in np.argsort(-main, kind="stable")[:25]];')
rep('    if stats["top1_main"] < n: fails.append(f"main top-1 differs for {n - stats[\'top1_main\']} molecules")\n',
    '    if stats["top1_main"] < n: fails.append(f"main top-1 differs for {n - stats[\'top1_main\']} molecules")\n'
    '    if EL is not None:   # 132 (B)\n'
    '        md += ["", f"## 132 E-lite agreement on {stats[\'n_el\']} molecules (K {a.elite_k:g}, alpha {a.elite_alpha:g}, E keys {len(EKS):,})", "",\n'
    '               f"| ordered top-25 identical | top-1 identical | RR identical | E membership mismatches / shared candidates | E-lite rank-1 changed vs P |", "|---:|---:|---:|---:|---:|",\n'
    '               f"| {stats[\'top25_el\']}/{stats[\'n_el\']} | {stats[\'top1_el\']}/{stats[\'n_el\']} | {stats[\'rr_el\']}/{stats[\'n_el\']} | {stats[\'emem_mismatch\']} / {stats[\'emem_cands\']} | {stats[\'el_top1_changed\']} |", "",\n'
    '               f"strata covered: E empty {stats[\'e_empty\']}, truth outside E {stats[\'truth_outside_e\']}, negative-ion only {stats[\'neg_only\']}, strong class-1 reference (c1, lib_max_c1 >= 0.9) {stats[\'strong_c1\']}, GL fallback {stats[\'fallback_el\']}"]\n'
    '        if stats["n_el"] != stats["n"]: fails.append(f"132: E-lite compared on {stats[\'n_el\']} of {stats[\'n\']} molecules")\n'
    '        if stats["top25_el"] < stats["n_el"] or stats["top1_el"] < stats["n_el"] or stats["rr_el"] < stats["n_el"]: fails.append(f"132: E-lite list differs (ordered top-25 {stats[\'n_el\'] - stats[\'top25_el\']}, top-1 {stats[\'n_el\'] - stats[\'top1_el\']}, RR {stats[\'n_el\'] - stats[\'rr_el\']} molecules; e.g. {EL_BAD[:3]})")\n'
    '        if stats["emem_mismatch"]: fails.append(f"132: E membership differs for {stats[\'emem_mismatch\']} shared candidates")\n')
dst = os.path.join(HERE, "b1_parity_e132.py")
open(dst, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", dst, hashlib.sha256(t.encode()).hexdigest())
