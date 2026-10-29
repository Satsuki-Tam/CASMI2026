"""133 v2 (Codex 133, results unread) for experiments/b1_baseline/b1_rank_train.py (v1 1a934edc): the MIST loader validates every table with
experiments/mist/mist_validate.py (status / range / null / duplicate checks and the one-to-one match with the run's feature table of the set),
loads the molecule-level query flags (mist_<tag>_<set>_qflags.parquet, mist_qflags.py; validated against the table) and passes mol_nq to the
feature block; the table glob excludes the *_qflags files. Usage: python -X utf8 experiments/mist/patch_ranktrain_m133_v2.py"""
import hashlib, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline", "b1_rank_train.py")
s = open(P, encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("1a934edc9295"), "b1_rank_train.py is not the 133 v1 version"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep("MISTCOV = {}   # 133: (run basename, set) -> [groups, candidate rows]\n",
    "MISTCOV = {}   # 133: (run basename, set) -> [groups, candidate rows]\nMISTQ = {}   # 133 v2: (run basename, set, molecule) -> number of MIST-usable queries (mist_qflags.py)\n")
rep("    return dict(cos=[x[0] for x in v_], nq=[x[1] for x in v_], status=[x[2] for x in v_], fint=[x[3] for x in v_], npk=[x[4] for x in v_], ppm=[x[5] for x in v_],\n"
    "                form=[neutral_formula(str(sm)) for sm in smiles])\n",
    "    q_ = MISTQ.get((os.path.basename(run), s, str(mid)))\n"
    "    if q_ is None: raise SystemExit(f\"133: no MIST query flag for {os.path.basename(run)} {s} {mid}\")\n"
    "    return dict(cos=[x[0] for x in v_], nq=[x[1] for x in v_], status=[x[2] for x in v_], fint=[x[3] for x in v_], npk=[x[4] for x in v_], ppm=[x[5] for x in v_],\n"
    "                form=[neutral_formula(str(sm)) for sm in smiles], mol_nq=q_)\n")
rep("        tags_ = dict(x.split('=', 1) for x in a.mist_tags); runs_ = [os.path.basename(r.split(':')[0]) for r in a.runs]\n",
    "        tags_ = dict(x.split('=', 1) for x in a.mist_tags); runs_ = [os.path.basename(r.split(':')[0]) for r in a.runs]; rpath_ = {os.path.basename(r.split(':')[0]): r.split(':')[0] for r in a.runs}\n"
    "        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \"mist\")); import mist_validate as MV   # 133 v2\n")
rep("            fs_ = sorted(_g.glob(os.path.join(a.mist_dir, f\"mist_{tags_[rb_]}_*.parquet\")))\n",
    "            fs_ = sorted(f_ for f_ in _g.glob(os.path.join(a.mist_dir, f\"mist_{tags_[rb_]}_*.parquet\")) if not f_.endswith(\"_qflags.parquet\"))\n")
rep("                M_ = pd.read_parquet(f_); M_[\"molecule\"] = M_.molecule.astype(str)\n",
    "                M_ = pd.read_parquet(f_); M_[\"molecule\"] = M_.molecule.astype(str)\n"
    "                s1_ = str(M_[\"set\"].iloc[0]) if len(M_) else os.path.basename(f_)[len(f\"mist_{tags_[rb_]}_\"):-len(\".parquet\")]\n"
    "                MV.validate_table(M_, f_, feat=pd.read_parquet(os.path.join(rpath_[rb_], f\"b1_features_{s1_}.parquet\"), columns=[\"molecule\", \"smiles\", \"official_key\"]))\n"
    "                Q_ = pd.read_parquet(f_[:-len(\".parquet\")] + \"_qflags.parquet\"); Q_[\"molecule\"] = Q_.molecule.astype(str); MV.validate_qflags(Q_, M_, f_)\n"
    "                for m_, n_ in zip(Q_.molecule, Q_.n_mist_q): MISTQ[(rb_, s1_, m_)] = float(n_)\n")
open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched", P, hashlib.sha256(t.encode()).hexdigest())
