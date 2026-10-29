"""133: adds the opt-in MIST block to experiments/b1_baseline/b1_rankfeats.py (no existing feature changes; only feature lists that name the new
columns need the `mist` argument). Block EXTRA_MIST, computed from per-candidate MIST outputs (experiments/mist/mist_score_v4.py) and the candidate's
neutral formula (wf_common.neutral_formula, the 128 definition):
  mist (cos, -1 when missing), z_mist (z within the list over finite values, missing -> list minimum), mist_missing, rank_mist (log1p rank),
  gap_mist (best z - z), margin_mist_mol (top-1 minus top-2 z, molecule-level), mist_nq (usable queries), mist_mol_noq (no candidate of the
  molecule has a usable MIST query: no_qrows / no_mist_adduct = MIST not applicable, e.g. negative-only), mist_mol_ok (share of candidates with
  status ok), within-formula: rank_mist_form (log1p rank of cos among the candidates of the same formula; NaN without a value), gap_mist_form (formula-group best cos
  - cos, raw cos = same conditioning), n_form (log1p size of the formula group), rank_form_mist (log1p rank of the formula group's best cos among
  the formula groups of the list), assignment quality of the candidate's formula: mist_fint (assigned intensity fraction), mist_npk (assigned
  peaks), mist_ppm (intensity-weighted ppm error), disagreement (NaN without a MIST value): d_rank_mist_fp (log rank MIST - log rank FP), d_z_mist_fp, d_z_mist_gl.
Usage: python -X utf8 experiments/mist/patch_rankfeats_m133.py"""
import hashlib, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b1_baseline", "b1_rankfeats.py")
s = open(P, encoding="utf-8").read().replace("\r\n", "\n")
assert hashlib.sha256(s.encode()).hexdigest().startswith("4cd59fbdab22"), "b1_rankfeats.py changed"
t = s


def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old)); t = t.replace(old, new)


rep("# monotone directions for the constrained variant",
    "# 133 (Codex 131 Q2): MIST (public ScaledMIST, MSG-trained) as ranker inputs, opt-in; see experiments/mist/patch_rankfeats_m133.py for the definitions\n"
    "EXTRA_MIST = [\"mist\", \"z_mist\", \"mist_missing\", \"rank_mist\", \"gap_mist\", \"margin_mist_mol\", \"mist_nq\", \"mist_mol_noq\", \"mist_mol_ok\", \"rank_mist_form\", \"gap_mist_form\", \"n_form\",\n"
    "              \"rank_form_mist\", \"mist_fint\", \"mist_npk\", \"mist_ppm\", \"d_rank_mist_fp\", \"d_z_mist_fp\", \"d_z_mist_gl\"]\n"
    "FEATSETS[\"v2_noice_ana_mist\"] = FEATSETS[\"v2_noice_ana\"] + EXTRA_MIST\n"
    "# monotone directions for the constrained variant")
rep("ppm_err, fp_rank_window, n_query, ce_known, n_window=np.nan, feats=None, exposure=None, libcond=None, analog=None, frag=None, cmp=None):",
    "ppm_err, fp_rank_window, n_query, ce_known, n_window=np.nan, feats=None, exposure=None, libcond=None, analog=None, frag=None, cmp=None, mist=None):")
rep("    return np.column_stack([cols[c] for c in feats])",
    "    if any(c in EXTRA_MIST for c in feats):   # 133\n"
    "        if mist is None: raise ValueError(\"feature list needs the MIST block but no mist arrays were given\")\n"
    "        cols.update(mist_block(mist, fp, gl))\n"
    "    return np.column_stack([cols[c] for c in feats])")
t += '''

def mist_block(mist, fp, gl):
    """133: EXTRA_MIST columns from dict(cos, nq, status, fint, npk, ppm, form) (one molecule's list; form = neutral formula or None)."""
    cos = np.asarray(mist["cos"], float); n = len(cos); st = np.asarray(mist["status"], dtype=object); form = list(mist["form"])
    ok = np.isfinite(cos); zm = term(cos); fp = np.asarray(fp, float); gl = np.asarray(gl, float)
    srt = np.sort(zm)[::-1]; margin = float(srt[0] - srt[1]) if n > 1 else 0.0
    rf = np.full(n, np.nan); gf = np.full(n, np.nan); nf = np.ones(n); best_of = {}
    groups = {}
    for i, f in enumerate(form): groups.setdefault(f if f is not None else ("__none__", i), []).append(i)
    for key, idx in groups.items():
        idx = np.asarray(idx, int); nf[idx] = len(idx); v = cos[idx]
        if np.isfinite(v).any():
            rf[idx] = rank_desc(v); gf[idx] = np.where(np.isfinite(v), np.nanmax(v) - v, np.nan); best_of[key] = float(np.nanmax(v))
        rf[idx[~np.isfinite(v)]] = np.nan   # a candidate without a MIST value has no within-formula rank
    fb = np.array([best_of.get(form[i] if form[i] is not None else ("__none__", i), np.nan) for i in range(n)], float)
    keys_ = [k for k in groups if k in best_of]; gbest = np.array([best_of[k] for k in keys_], float)
    grank = dict(zip(keys_, rank_desc(gbest))) if len(keys_) else {}
    rfm = np.array([grank.get(form[i] if form[i] is not None else ("__none__", i), np.nan) for i in range(n)], float)   # NaN: the formula group has no MIST value
    noq = bool(n) and all(str(x) in ("no_qrows", "no_mist_adduct") for x in st)
    return dict(mist=np.nan_to_num(cos, nan=-1.0), z_mist=zm, mist_missing=(~ok).astype(float), rank_mist=np.log1p(rank_desc(cos)), gap_mist=(float(np.max(zm)) - zm) if n else zm,
                margin_mist_mol=np.full(n, margin), mist_nq=np.asarray(mist["nq"], float), mist_mol_noq=np.full(n, float(noq)), mist_mol_ok=np.full(n, float(ok.mean()) if n else 0.0),
                rank_mist_form=np.log1p(rf), gap_mist_form=gf, n_form=np.log1p(nf), rank_form_mist=np.log1p(rfm),
                mist_fint=np.asarray(mist["fint"], float), mist_npk=np.asarray(mist["npk"], float), mist_ppm=np.asarray(mist["ppm"], float),
                d_rank_mist_fp=np.where(ok, np.log1p(rank_desc(cos)) - np.log1p(rank_desc(fp)), np.nan), d_z_mist_fp=np.where(ok, zm - zlist(fp), np.nan),
                d_z_mist_gl=np.where(ok, zm - term(gl), np.nan))
'''
open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched", P, hashlib.sha256(t.encode()).hexdigest())
