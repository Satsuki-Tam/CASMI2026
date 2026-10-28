"""111 mechanism diagnostics (111_prereg_nscorer.md section 3, descriptive, label-using; never used for the decision), written before any 111 model
was trained. Per checkpoint ck and C2 view frame (b1_locked_eval.view_frame rule: in_short_c2 & (in_tier | in_coconut | in_train_c2)) of the fold-1
tables, with N / Fs from experiments/n111/scores/s<ck>/ and the merged-logit FP score fp of the table:
  (1) same-formula groups: molecules whose truth has >= 1 other candidate of the same molecular formula (RDKit CalcMolFormula of the candidate
      SMILES); MRR of the truth inside its formula group under N, Fs and fp (ties pessimistic), group sizes;
  (2) FP collisions: share of those molecules where another same-formula candidate has a bit vector identical to the truth's (fph equal) -- such
      decoys cannot be separated by N, Fs or fp;
  (3) seen-candidate bias (label-free part): share of the top-1 under N / Fs / fp that is a training structure (in_train_c2), and the mean rank
      percentile of training-structure candidates under each score; (label part) truth rank under N vs Fs among rows with the truth in the frame.
Usage (Spark, experiments/b1_baseline): python -X utf8 x111_diag.py [--cks s2000 s8000 s20000]"""
import argparse, os
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--cks", nargs="+", default=["s2000", "s8000", "s20000"]); a = ap.parse_args()
TABS = {"f1dev": ("run_f1dev", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]), "np053f1dev": ("run_np053_f1dev", ["NP_H", "NP_X", "NP_N"])}


def formulas(smis):
    from rdkit import Chem, RDLogger
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    RDLogger.DisableLog("rdApp.*"); out = []
    for s in smis:
        m = Chem.MolFromSmiles(s); out.append(CalcMolFormula(m) if m is not None else None)
    return out


def rank_in(scores, idx):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18); return int(np.sum(s >= s[idx]))


frames = {}
for tag, (run, sets) in TABS.items():
    for s in sets:
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "official_key", "is_truth", "in_short_c2", "in_tier", "in_coconut", "in_train_c2", "fp"])
        keep = F.in_short_c2.astype(bool) & (F.in_tier.astype(bool) | F.in_coconut.astype(bool) | F.in_train_c2.astype(bool))
        frames[(tag, s)] = F[keep].reset_index(drop=True)
allsmi = sorted({x for f in frames.values() for x in f.smiles.astype(str)})
with Pool(12) as p: res = p.map(formulas, [allsmi[i:i + 2000] for i in range(0, len(allsmi), 2000)])
FORM = dict(zip(allsmi, [x for r in res for x in r]))
L = ["# 111 mechanism diagnostics (descriptive; C2 view frames of the fold-1 tables)", ""]
for ck in a.cks:
    L += [f"## {ck}", "", "| cell | molecules with a same-formula group | median group size | formula-group MRR N / Fs / fp | truth FP-collision share | top-1 is a train structure N / Fs / fp | train-candidate mean rank pct N / Fs / fp | truth rank median N / Fs |", "|---|---:|---:|---|---:|---|---|---|"]
    for (tag, s), F in frames.items():
        S = pd.read_parquet(os.path.join(ROOT, "experiments", "n111", "scores", ck, f"n111_{tag}_{s}.parquet"), columns=["molecule", "smiles", "N", "Fs", "fph"])
        G = F.merge(S, on=["molecule", "smiles"], how="left", validate="one_to_one"); G["form"] = G.smiles.astype(str).map(FORM)
        ng = 0; sizes = []; rr = {"N": [], "Fs": [], "fp": []}; coll = 0; top_tr = {"N": [], "Fs": [], "fp": []}; pct = {"N": [], "Fs": [], "fp": []}; tr_rank = {"N": [], "Fs": []}
        for mid, g in G.groupby("molecule", sort=False):
            tr_ = g.in_train_c2.values.astype(bool)
            for k in ("N", "Fs", "fp"):
                v = g[k].values.astype(float); o = np.argsort(-np.nan_to_num(v, nan=-1e18), kind="stable")
                top_tr[k].append(bool(tr_[o[0]])) if len(o) else None
                if tr_.any() and len(g) > 1:
                    r = np.empty(len(g)); r[o] = np.arange(len(g)); pct[k].append(float(np.mean(r[tr_] / (len(g) - 1))))
            t = np.flatnonzero(g.is_truth.values.astype(bool))
            if not len(t): continue
            ti = int(t[0]); tr_rank["N"].append(rank_in(g.N.values, ti)); tr_rank["Fs"].append(rank_in(g.Fs.values, ti))
            fg = g[g.form == g.form.values[ti]]
            if len(fg) < 2 or g.form.values[ti] is None: continue
            ng += 1; sizes.append(len(fg)); fti = int(np.flatnonzero(fg.is_truth.values.astype(bool))[0])
            for k in ("N", "Fs", "fp"):
                rk = rank_in(fg[k].values, fti); rr[k].append(1.0 / rk if rk <= 25 else 0.0)
            coll += int((fg.fph.values == fg.fph.values[fti]).sum() > 1)
        mm = lambda x: f"{np.mean(x):.3f}" if len(x) else "n/a"
        L.append(f"| {tag} {s} | {ng} | {np.median(sizes) if sizes else 0:.0f} | {mm(rr['N'])} / {mm(rr['Fs'])} / {mm(rr['fp'])} | {coll / max(1, ng):.3f} | {mm(top_tr['N'])} / {mm(top_tr['Fs'])} / {mm(top_tr['fp'])} | "
                 f"{mm(pct['N'])} / {mm(pct['Fs'])} / {mm(pct['fp'])} | {np.median(tr_rank['N']) if tr_rank['N'] else float('nan'):.0f} / {np.median(tr_rank['Fs']) if tr_rank['Fs'] else float('nan'):.0f} |")
    L.append("")
open(os.path.join(HERE, "diag/x111_diag.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
