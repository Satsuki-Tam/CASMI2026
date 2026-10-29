"""133 v2 (Codex 133 Q1, results unread): two definition fixes of the EXTRA_MIST block in experiments/b1_baseline/b1_rankfeats.py (v1 c04509c5):
  mist_mol_noq = the molecule has no MIST-usable query (mist['mol_nq'] == 0, from mist_qflags.py, independent of the candidate formulas);
                 v1 derived it from the candidates' statuses, which an invalid candidate formula (status no_formula) could flip;
  d_rank_mist_fp / d_z_mist_fp only where MIST and FP are both finite, d_z_mist_gl only where MIST and GL are both finite (else NaN);
                 v1 compared a finite MIST value with an imputed FP / GL rank or z.
Every other column is unchanged. Usage: python -X utf8 experiments/mist/patch_rankfeats_m133_v2.py"""
import hashlib, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline", "b1_rankfeats.py")
s = open(P, encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("c04509c523b0"), "b1_rankfeats.py is not v1 (c04509c5)"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep('    """133: EXTRA_MIST columns from dict(cos, nq, status, fint, npk, ppm, form) (one molecule\'s list; form = neutral formula or None)."""',
    '    """133: EXTRA_MIST columns from dict(cos, nq, status, fint, npk, ppm, form, mol_nq) (one molecule\'s list; form = neutral formula or None;\n'
    '    mol_nq = the molecule\'s number of MIST-usable queries, mist_qflags.py; v2: mist_mol_noq from mol_nq, disagreements only where both are finite)."""')
rep("    noq = bool(n) and all(str(x) in (\"no_qrows\", \"no_mist_adduct\") for x in st)\n",
    "    noq = float(mist[\"mol_nq\"]) == 0   # v2 (Codex 133): query availability, independent of the candidate formulas\n")
rep("                d_rank_mist_fp=np.where(ok, np.log1p(rank_desc(cos)) - np.log1p(rank_desc(fp)), np.nan), d_z_mist_fp=np.where(ok, zm - zlist(fp), np.nan),\n"
    "                d_z_mist_gl=np.where(ok, zm - term(gl), np.nan))\n",
    "                d_rank_mist_fp=np.where(ok & np.isfinite(fp), np.log1p(rank_desc(cos)) - np.log1p(rank_desc(fp)), np.nan),\n"
    "                d_z_mist_fp=np.where(ok & np.isfinite(fp), zm - zlist(fp), np.nan), d_z_mist_gl=np.where(ok & np.isfinite(gl), zm - term(gl), np.nan))   # v2: both observed\n")
open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched", P, hashlib.sha256(t.encode()).hexdigest())
