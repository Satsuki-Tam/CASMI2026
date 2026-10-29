"""133 (MIST-feature ranker pair, Codex 131 Q2): writes experiments/mist/mist_score_v4.py = mist_score.py v3 (sha 633647cb, registered for 128; not
touched) with three per-(query, formula) assignment-quality outputs averaged over the candidate's usable queries, next to the unchanged mist_cos /
mist_ll / n_q / status:
  mist_fint = intensity fraction of the merged spectrum that MIST's own subformula assignment (20 ppm) explains under the candidate's formula,
  mist_npk  = number of assigned peaks (all of them, not only the top-10 the model reads),
  mist_ppm  = intensity-weighted mean ppm error of the assigned peaks (NaN when none is assigned).
The model input is built exactly as before: A.tree_to_row(A.assign_tree(...)) == A.featurize(...) (the same two calls), and the merged spectrum used
for the fraction is MIST's merge_ms_spectrum on the same text (deterministic). Usage: python -X utf8 experiments/mist/make_score_v4.py"""
import hashlib, os
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, "mist_score.py"), encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("633647cb"), "mist_score.py v3 changed"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep('"""MIST per-candidate scores', '"""v4 (133, make_score_v4.py): + mist_fint / mist_npk / mist_ppm (assignment quality per candidate formula, mean over usable queries).\nMIST per-candidate scores')
rep("from mist.utils import chem_utils as C\n", "from mist.utils import chem_utils as C\nfrom mist.data import featurizers as MF\n")
rep('                    pairs.append((x, f)); feats.append(A.featurize(mz, it, prec, f, add_of_row[x], str(ins_of_row[x]) if ins_of_row is not None else "unknown"))\n',
    '                    tree_ = A.assign_tree(mz, it, prec, f, add_of_row[x]); tb_ = tree_["output_tbl"]   # v4: the same two calls as A.featurize\n'
    '                    if (x, "tot") not in QT: mg_ = MF.merge_ms_spectrum(A.ms_text(mz, it, prec)); QT[(x, "tot")] = float(mg_[:, 1].sum()) if len(mg_) else 0.0\n'
    '                    ai_ = np.asarray(tb_["ms2_inten"], float) if tb_ else np.zeros(0); pe_ = np.asarray(tb_["mass_diff"], float) if tb_ else np.zeros(0)\n'
    '                    QA[(x, f)] = (float(ai_.sum() / QT[(x, "tot")]) if QT[(x, "tot")] > 0 else 0.0, float(len(ai_)), float((ai_ * pe_).sum() / ai_.sum()) if ai_.sum() > 0 else np.nan)\n'
    '                    pairs.append((x, f)); feats.append(A.tree_to_row(tree_, str(ins_of_row[x]) if ins_of_row is not None else "unknown"))\n')
rep("            pairs, feats = [], []\n", "            pairs, feats, QA, QT = [], [], {}, {}\n")
rep("                cs, ll = [], []\n", "                cs, ll, qa = [], [], []\n")
rep("                        pc = np.clip(p, 1e-6, 1 - 1e-6); ll.append(float((bits * np.log(pc) + (1 - bits) * np.log(1 - pc)).mean()))\n",
    "                        pc = np.clip(p, 1e-6, 1 - 1e-6); ll.append(float((bits * np.log(pc) + (1 - bits) * np.log(1 - pc)).mean())); qa.append(QA[(x, f)])\n")
rep("                                 mist_ll=float(np.mean(ll)) if ll else np.nan, n_q=len(cs), status=st))\n",
    "                                 mist_ll=float(np.mean(ll)) if ll else np.nan, n_q=len(cs), status=st,\n"
    "                                 mist_fint=float(np.mean([v_[0] for v_ in qa])) if qa else np.nan, mist_npk=float(np.mean([v_[1] for v_ in qa])) if qa else np.nan,\n"
    "                                 mist_ppm=float(np.nanmean([v_[2] for v_ in qa])) if (qa and np.isfinite([v_[2] for v_ in qa]).any()) else np.nan))\n")
rep('        O = pd.DataFrame(rows, columns=["set", "molecule", "smiles", "official_key", "mist_cos", "mist_ll", "n_q", "status"])\n',
    '        O = pd.DataFrame(rows, columns=["set", "molecule", "smiles", "official_key", "mist_cos", "mist_ll", "n_q", "status", "mist_fint", "mist_npk", "mist_ppm"])\n')
rep('code={f: sha(os.path.join(HERE, f)) for f in ("mist_score.py", "mist_adapter.py")}', 'code={f: sha(os.path.join(HERE, f)) for f in ("mist_score_v4.py", "mist_score.py", "mist_adapter.py")}')
open(os.path.join(HERE, "mist_score_v4.py"), "w", encoding="utf-8", newline="\n").write(t)
print("wrote mist_score_v4.py", hashlib.sha256(t.encode()).hexdigest())
