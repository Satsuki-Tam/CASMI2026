"""133: --mist_dir / --mist_tags for experiments/b1_baseline/b1_rank_train.py (opt-in; without them the trainer is unchanged).
--mist_tags RUN_BASENAME=TAG ...: the MIST table of a run is <mist_dir>/mist_<TAG>_<set>.parquet (experiments/mist/mist_score_v4.py). Every view row
of a run with a tag must find its (set, molecule, smiles) row in that table (one-to-one per (set, molecule, smiles); else stop), and the MIST arrays
(cos, nq, status, fint, npk, ppm) plus the candidate's neutral formula (wf_common.neutral_formula) are passed to feature_matrix(mist=...).
Usage: python -X utf8 experiments/mist/patch_ranktrain_m133.py"""
import hashlib, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline", "b1_rank_train.py")
s = open(P, encoding="utf-8").read().replace("\r\n", "\n")
print("b1_rank_train.py sha256 before", hashlib.sha256(s.encode()).hexdigest())
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep("EXPO = {}   # official key -> (fp_pos, negpool)",
    "MISTD = {}   # 133: (run basename, set, molecule) -> {smiles: (cos, nq, status, fint, npk, ppm)} from --mist_dir / --mist_tags\n"
    "MISTCOV = {}   # 133: (run basename, set) -> [groups, candidate rows]\n"
    "EXPO = {}   # official key -> (fp_pos, negpool)")
rep("def load_run(run, eval_csv, group_override=None, feats=FEATS):\n",
    "def mist_of(run, s, mid, smiles):   # 133: strict lookup; the formula is the 128 neutral formula of the representative SMILES\n"
    "    from wf_common import neutral_formula\n"
    "    d_ = MISTD.get((os.path.basename(run), s, str(mid)))\n"
    "    if d_ is None: raise SystemExit(f\"133: no MIST rows for {os.path.basename(run)} {s} {mid}\")\n"
    "    v_ = [d_.get(str(sm)) for sm in smiles]\n"
    "    if any(x is None for x in v_): raise SystemExit(f\"133: {sum(x is None for x in v_)} candidates of {os.path.basename(run)} {s} {mid} without a MIST row\")\n"
    "    c_ = MISTCOV.setdefault((os.path.basename(run), s), [0, 0]); c_[0] += 1; c_[1] += len(v_)\n"
    "    return dict(cos=[x[0] for x in v_], nq=[x[1] for x in v_], status=[x[2] for x in v_], fint=[x[3] for x in v_], npk=[x[4] for x in v_], ppm=[x[5] for x in v_],\n"
    "                form=[neutral_formula(str(sm)) for sm in smiles])\n\n\n"
    "def load_run(run, eval_csv, group_override=None, feats=FEATS):\n")
rep("                                   analog=(dict(ap=[ANA.get((s, view, mid), {}).get(str(sm), (0.0, 0.0))[0] for sm in g.smiles], mean_tan=[ANA.get((s, view, mid), {}).get(str(sm), (0.0, 0.0))[1] for sm in g.smiles]) if ANA else None))\n",
    "                                   analog=(dict(ap=[ANA.get((s, view, mid), {}).get(str(sm), (0.0, 0.0))[0] for sm in g.smiles], mean_tan=[ANA.get((s, view, mid), {}).get(str(sm), (0.0, 0.0))[1] for sm in g.smiles]) if ANA else None),\n"
    "                                   mist=(mist_of(run, s, mid, g.smiles) if MISTD else None))\n")
rep('    ap.add_argument("--fit_frac", type=float, default=1.0,',
    '    ap.add_argument("--mist_dir", default="", help="133: directory of mist_<tag>_<set>.parquet (experiments/mist/mist_score_v4.py); needed by the v2_noice_ana_mist feature set")\n'
    '    ap.add_argument("--mist_tags", nargs="*", default=[], help="133: RUN_BASENAME=TAG for every run (strict: every view row needs its MIST row)")\n'
    '    ap.add_argument("--fit_frac", type=float, default=1.0,')
rep("    if a.exposure_ledger:\n",
    "    if a.mist_dir:   # 133\n"
    "        import glob as _g\n"
    "        tags_ = dict(x.split('=', 1) for x in a.mist_tags); runs_ = [os.path.basename(r.split(':')[0]) for r in a.runs]\n"
    "        if set(runs_) - set(tags_): raise SystemExit(f\"133: runs without a MIST tag: {sorted(set(runs_) - set(tags_))}\")\n"
    "        for rb_ in runs_:\n"
    "            fs_ = sorted(_g.glob(os.path.join(a.mist_dir, f\"mist_{tags_[rb_]}_*.parquet\")))\n"
    "            if not fs_: raise SystemExit(f\"133: no MIST tables for {rb_} (tag {tags_[rb_]})\")\n"
    "            for f_ in fs_:\n"
    "                M_ = pd.read_parquet(f_); M_[\"molecule\"] = M_.molecule.astype(str)\n"
    "                if M_.duplicated([\"set\", \"molecule\", \"smiles\"]).any(): raise SystemExit(f\"133: duplicate MIST rows in {f_}\")\n"
    "                for (s_, m_), h_ in M_.groupby([\"set\", \"molecule\"]):\n"
    "                    MISTD[(rb_, str(s_), m_)] = dict(zip(h_.smiles.astype(str), zip(h_.mist_cos.astype(float), h_.n_q.astype(float), h_.status.astype(str), h_.mist_fint.astype(float), h_.mist_npk.astype(float), h_.mist_ppm.astype(float))))\n"
    "        print(f\"133 MIST tables {a.mist_dir}: {len(MISTD):,} (run, set, molecule) groups, tags {tags_}\", flush=True)\n"
    "    if a.exposure_ledger:\n")
rep("    for k_, c_ in sorted(ACOV.items()):\n",
    "    for k_, c_ in sorted(MISTCOV.items()): print(f\"MIST-COVER {k_[0]} {k_[1]}: groups {c_[0]}, candidate rows {c_[1]} (all matched)\", flush=True)\n"
    "    for k_, c_ in sorted(ACOV.items()):\n")
open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched", P, hashlib.sha256(t.encode()).hexdigest())
