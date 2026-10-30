"""152 feasibility (descriptive, reading fixed in reports/agent_review/152_feas_ionpattern.md): can the per-molecule ionization
pattern (observed in negative / positive mode under the Enveda timsTOF acquisition) be predicted from structure, and does it separate
a molecule from its same-formula decoys?
Data: train_meta rows of enveda-180 and enveda-np-examples (panel), the ten hidden-test adducts, base peak >= 1000.
Model: LightGBM binary on RDKit descriptors + acid/base group counts + Morgan counts; enveda-180 5-fold OOF by inchikey14 hash.
Usage: CUDA_VISIBLE_DEVICES=-1 python -X utf8 experiments/x152/ion_pattern_feas.py"""
import os, sys, hashlib, json, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import get_context

ROOT = r"C:\kaggle\CASMI"
OUT = os.path.join(ROOT, "experiments", "x152")
TEST_ADDUCTS = ["[M+H]+", "[M+NH4]+", "[M-H2O+H]+", "[M-2H2O+H]+", "[M+Na]+", "[M+K]+", "[M-H]-", "[M-H2O-H]-", "[M+CH2O2-H]-", "[M+Cl]-"]
SMARTS = {
    "cooh": "[CX3](=O)[OX2H1]", "phenol": "[OX2H1]c", "so3h": "[SX4](=O)(=O)[OX2H1]", "po3h": "[PX4](=O)[OX2H1]",
    "tetrazole": "c1nn[nH]n1", "sulfonamide_nh": "[NX3;H1,H2][SX4](=O)=O", "imide": "C(=O)[NX3H1]C(=O)",
    "alcohol": "[OX2H1][CX4]", "enol": "[OX2H1][CX3]=[CX3]",
    "amine_aliph": "[NX3;H2,H1,H0;!$(N[#6]=[#7,#8,#16]);!$(N[a]);!$(N[SX4]);!$(N-[#7,#8])]([CX4])",
    "aniline": "[NX3;H2,H1;!$(NC=O)]c", "pyridine_n": "[nX2;r6]", "imidazole": "[nX2;r5]:[c]:[nX3;r5]",
    "amidine": "[NX3;!$(NC=O)][CX3]=[NX2;!$(N-O)]", "quat_n": "[N+,n+;!$([N+][O-]);!$([n+][O-]);!$([N+]=O)]",
    "amide": "C(=O)[NX3]", "ester": "[CX3](=O)[OX2][#6]", "nitro": "[N+](=O)[O-]", "carbonyl": "[CX3]=O", "ether": "[OD2]([#6])[#6]",
}
N_DESC = 10 + 9 + len(SMARTS)
_PATS = None


def feats(smi):
    global _PATS
    from rdkit import Chem, RDLogger
    from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    if _PATS is None:
        _PATS = {k: Chem.MolFromSmarts(v) for k, v in SMARTS.items()}
    m = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
    if m is None:
        return None
    d = [Descriptors.MolWt(m), Descriptors.MolLogP(m), Descriptors.TPSA(m), rdMolDescriptors.CalcNumHBD(m), rdMolDescriptors.CalcNumHBA(m),
         rdMolDescriptors.CalcNumRotatableBonds(m), rdMolDescriptors.CalcNumRings(m), rdMolDescriptors.CalcNumAromaticRings(m),
         rdMolDescriptors.CalcFractionCSP3(m), Chem.GetFormalCharge(m)]
    cnt = {}
    for a in m.GetAtoms():
        cnt[a.GetSymbol()] = cnt.get(a.GetSymbol(), 0) + 1
    d += [cnt.get(s, 0) for s in ("C", "N", "O", "S", "P", "F", "Cl", "Br", "I")]
    d += [len(m.GetSubstructMatches(p)) for p in _PATS.values()]
    g = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)
    fp = g.GetCountFingerprintAsNumPy(m)
    return np.concatenate([np.asarray(d, np.float32), np.minimum(fp, 255).astype(np.float32)])


def featurize(smiles, pool):
    out = pool.map(feats, smiles, chunksize=500)
    ok = np.array([o is not None for o in out], dtype=bool)
    X = np.stack([o for o in out if o is not None]) if ok.any() else np.zeros((0, N_DESC + 1024), np.float32)
    return X, ok


def formula(smi):
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdMolDescriptors
    RDLogger.DisableLog("rdApp.*")
    m = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
    return rdMolDescriptors.CalcMolFormula(m) if m is not None else None


def auc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if len(set(y)) == 2 else float("nan")


def main():
    t0 = time.time()
    import lightgbm as lgb
    tm = (pl.scan_parquet(os.path.join(ROOT, "data/processed/train_meta.parquet"))
          .select("inchikey14", "ingest_lib", "ionization_mode", "adduct", "base_peak_intensity")
          .filter(pl.col("ingest_lib").is_in(["enveda-180", "enveda-np-examples"])).collect())
    print("rows", tm.height, "| base_peak<1000 share", round(float((tm["base_peak_intensity"] < 1000).mean()), 4), flush=True)
    tm = tm.filter(pl.col("adduct").is_in(TEST_ADDUCTS) & (pl.col("base_peak_intensity") >= 1000))
    P = (tm.group_by("ingest_lib", "inchikey14").agg(has_neg=(pl.col("ionization_mode") == "negative").any(),
                                                     has_pos=(pl.col("ionization_mode") == "positive").any(), n=pl.len()).to_pandas())
    mol = pl.read_parquet(os.path.join(ROOT, "data/processed/train_molecules.parquet"), columns=["inchikey14", "smiles", "formula"]).to_pandas()
    P = P.merge(mol, on="inchikey14", how="left")
    E = P[P.ingest_lib == "enveda-180"].reset_index(drop=True)
    N = P[P.ingest_lib == "enveda-np-examples"].reset_index(drop=True)
    print("enveda-180 mols", len(E), "has_neg", round(E.has_neg.mean(), 3), "has_pos", round(E.has_pos.mean(), 3),
          "| panel mols", len(N), "has_neg", round(N.has_neg.mean(), 3), "has_pos", round(N.has_pos.mean(), 3), flush=True)
    ctx = get_context("spawn")
    with ctx.Pool(10) as pool:
        XE, okE = featurize(E.smiles.tolist(), pool); E = E[okE].reset_index(drop=True)
        XN, okN = featurize(N.smiles.tolist(), pool); N = N[okN].reset_index(drop=True)
        print(f"featurized E {XE.shape} N {XN.shape} | {time.time() - t0:.0f}s", flush=True)
        coco = pd.read_parquet(os.path.join(ROOT, "data/external/coconut/coco_meta.parquet"))
        need = set(N.formula.dropna())
        coco["formula"] = pool.map(formula, coco.smiles.tolist(), chunksize=2000)
        print(f"coconut formulas done | {time.time() - t0:.0f}s", flush=True)
        dec = coco[coco.formula.isin(need)].copy()
        rng = np.random.default_rng(20261030)
        rows = []
        for r in N.itertuples(index=False):
            dd = dec[(dec.formula == r.formula) & (dec["keys"] != r.inchikey14)]
            if len(dd) > 200:
                dd = dd.iloc[np.sort(rng.choice(len(dd), 200, replace=False))]
            for k, s in zip(dd["keys"], dd.smiles):
                rows.append((r.inchikey14, k, s))
        D = pd.DataFrame(rows, columns=["panel_ik", "key", "smiles"])
        XD, okD = featurize(D.smiles.tolist(), pool); D = D[okD].reset_index(drop=True)
        print(f"decoys {len(D)} for {D.panel_ik.nunique()} panel mols | {time.time() - t0:.0f}s", flush=True)
    params = dict(objective="binary", learning_rate=0.05, num_leaves=63, min_data_in_leaf=50, feature_fraction=0.8, bagging_fraction=0.8,
                  bagging_freq=1, lambda_l2=1.0, verbose=-1, seed=7, num_threads=12)
    fold = np.array([int(hashlib.md5(k.encode()).hexdigest(), 16) % 5 for k in E.inchikey14])
    res = {}
    keep = ~E.inchikey14.isin(set(N.inchikey14)).values
    res["panel_mols_also_in_enveda180"] = int((~keep).sum())
    for tgt in ("has_neg", "has_pos"):
        y = E[tgt].astype(int).values
        oof = np.zeros(len(E))
        for f in range(5):
            tr, va = fold != f, fold == f
            b = lgb.train(params, lgb.Dataset(XE[tr], y[tr]), num_boost_round=400)
            oof[va] = b.predict(XE[va])
        E[f"p_{tgt}"] = oof
        res[f"E_oof_auc_{tgt}"] = auc(y, oof)
        b = lgb.train(params, lgb.Dataset(XE[keep], y[keep]), num_boost_round=400)
        N[f"p_{tgt}"] = b.predict(XN)
        D[f"p_{tgt}"] = b.predict(XD)
        res[f"panel_auc_{tgt}"] = auc(N[tgt].astype(int).values, N[f"p_{tgt}"].values)
        print(tgt, "E OOF AUC", round(res[f"E_oof_auc_{tgt}"], 4), "| panel AUC", round(res[f"panel_auc_{tgt}"], 4), f"| {time.time() - t0:.0f}s", flush=True)
    # same-formula discordant pairs inside enveda-180 (OOF), pairwise accuracy for has_neg
    acc = []
    rng = np.random.default_rng(7)
    for fm, g in E.groupby("formula"):
        a = g[g.has_neg]; b_ = g[~g.has_neg]
        if len(a) == 0 or len(b_) == 0:
            continue
        for _ in range(min(20, len(a) * len(b_))):
            i = rng.integers(len(a)); j = rng.integers(len(b_))
            pa, pb = a.p_has_neg.iloc[i], b_.p_has_neg.iloc[j]
            acc.append(float(pa > pb) + 0.5 * float(pa == pb))
    res["E_same_formula_pair_acc_has_neg"] = float(np.mean(acc))
    res["E_same_formula_pairs"] = len(acc)
    # panel truth vs same-formula COCONUT decoys: log-likelihood of the observed pattern under each structure
    eps = 1e-4

    def ll(pn, pp, has_neg, has_pos):
        pn = np.clip(pn, eps, 1 - eps); pp = np.clip(pp, eps, 1 - eps)
        return (np.log(pn) if has_neg else np.log(1 - pn)) + (np.log(pp) if has_pos else np.log(1 - pp))

    fr = []
    for r in N.itertuples(index=False):
        dd = D[D.panel_ik == r.inchikey14]
        if len(dd) == 0:
            continue
        lt = float(ll(np.array([r.p_has_neg]), np.array([r.p_has_pos]), r.has_neg, r.has_pos)[0])
        ld = ll(dd.p_has_neg.values, dd.p_has_pos.values, r.has_neg, r.has_pos)
        fr.append(dict(ik=r.inchikey14, has_neg=r.has_neg, has_pos=r.has_pos, n_dec=len(dd),
                       frac_below=float(np.mean(ld < lt) + 0.5 * np.mean(ld == lt))))
    F = pd.DataFrame(fr)
    res["panel_truth_vs_decoy_mean"] = float(F.frac_below.mean())
    res["panel_mols_with_decoys"] = int(len(F))
    F["pat"] = np.where(F.has_neg & F.has_pos, "both", np.where(F.has_pos, "pos_only", "neg_only"))
    res["panel_truth_vs_decoy_by_pattern"] = F.groupby("pat").frac_below.agg(["mean", "size"]).round(4).to_dict()
    res["panel_truth_vs_decoy_quantiles"] = F.frac_below.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(3).to_dict()
    print(json.dumps(res, indent=1, default=str))
    F.to_csv(os.path.join(OUT, "panel_truth_vs_decoy.csv"), index=False)
    json.dump(res, open(os.path.join(OUT, "ion_pattern_feas.json"), "w"), indent=1, default=str)
    print(f"DONE {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
