"""133: writes experiments/b1_baseline/gen_eval2fd_m133.py = gen_eval2fd.py (registered 128 version, sha 3c51a35b; not touched) with the MIST
inputs for main models whose feature list contains the EXTRA_MIST block:
  --mist_main DIR --mist_main_tag TAG: the table of set S is DIR/mist_<TAG>_<S>.parquet (experiments/mist/mist_score_v4.py); every candidate row of
  every evaluated (set, molecule) must find its (molecule, smiles) row (strict, else stop); arrays (cos, nq, status, fint, npk, ppm) + the neutral
  formula (wf_common.neutral_formula) go to feature_matrix(mist=...). Models without the block (e.g. rank_v8w7a) are computed exactly as before.
Usage: python -X utf8 experiments/mist/make_ge133.py"""
import hashlib, os
B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline")
s = open(os.path.join(B, "gen_eval2fd.py"), encoding="utf-8").read().replace("\r\n", "\n")
assert hashlib.sha256(s.encode()).hexdigest().startswith("3c51a35b0f0b"), "gen_eval2fd.py changed"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep('ap_.add_argument("--ekeys", default="diag/e_window_keys_v2.parquet");',
    'ap_.add_argument("--mist_main", default="", help="133: dir of mist_<tag>_<set>.parquet (mist_score_v4.py) for main models with the EXTRA_MIST block"); ap_.add_argument("--mist_main_tag", default="")\n'
    'ap_.add_argument("--ekeys", default="diag/e_window_keys_v2.parquet");')
rep("    from b1_rankfeats import feature_matrix\n", "    from b1_rankfeats import feature_matrix, EXTRA_MIST\n")
rep("    WMS, WMX = {}, {}\n",
    "    MMX = {}   # 133: (set, molecule) -> {smiles: (cos, nq, status, fint, npk, ppm)}\n"
    "    if any(f_ in EXTRA_MIST for fl_ in FEATS_M for f_ in fl_):\n"
    "        if not (a.mist_main and a.mist_main_tag): raise SystemExit(\"133: a main model needs the MIST block but --mist_main / --mist_main_tag are not given\")\n"
    "        from wf_common import neutral_formula as _NF133\n"
    "        for s_ in a.sets:\n"
    "            X_ = pd.read_parquet(os.path.join(HERE, a.mist_main, f\"mist_{a.mist_main_tag}_{s_}.parquet\")); X_[\"molecule\"] = X_.molecule.astype(str)\n"
    "            if X_.duplicated([\"molecule\", \"smiles\"]).any(): raise SystemExit(f\"133: duplicate MIST rows in {s_}\")\n"
    "            for m_, h_ in X_.groupby(\"molecule\"): MMX[(s_, m_)] = dict(zip(h_.smiles.astype(str), zip(h_.mist_cos.astype(float), h_.n_q.astype(float), h_.status.astype(str), h_.mist_fint.astype(float), h_.mist_npk.astype(float), h_.mist_ppm.astype(float))))\n"
    "        log(f\"133 MIST tables {a.mist_main} tag {a.mist_main_tag}: {len(MMX):,} (set, molecule) groups\")\n"
    "    def _mist133(s_, m_, smiles_):\n"
    "        d_ = MMX.get((s_, str(m_)))\n"
    "        if d_ is None: raise SystemExit(f\"133: no MIST rows for {s_} {m_}\")\n"
    "        v_ = [d_.get(str(sm_)) for sm_ in smiles_]\n"
    "        if any(x_ is None for x_ in v_): raise SystemExit(f\"133: candidates of {s_} {m_} without a MIST row\")\n"
    "        return dict(cos=[x_[0] for x_ in v_], nq=[x_[1] for x_ in v_], status=[x_[2] for x_ in v_], fint=[x_[3] for x_ in v_], npk=[x_[4] for x_ in v_], ppm=[x_[5] for x_ in v_],\n"
    "                    form=[_NF133(str(sm_)) for sm_ in smiles_])\n"
    "    WMS, WMX = {}, {}\n")
rep("feats=list(fl_), cmp=cmp_, analog=(dict(ap=feats['ap'], mean_tan=feats['mean_tan']) if any(f_.startswith('ana_') or f_ == 'z_ana_ap' for f_ in fl_) else None))\n",
    "feats=list(fl_), cmp=cmp_, analog=(dict(ap=feats['ap'], mean_tan=feats['mean_tan']) if any(f_.startswith('ana_') or f_ == 'z_ana_ap' for f_ in fl_) else None),\n"
    "                                       mist=(_mist133(s, mid, g.smiles) if any(f_ in EXTRA_MIST for f_ in fl_) else None))   # 133\n")
open(os.path.join(B, "gen_eval2fd_m133.py"), "w", encoding="utf-8", newline="\n").write(t)
print("wrote gen_eval2fd_m133.py", hashlib.sha256(t.encode()).hexdigest())
