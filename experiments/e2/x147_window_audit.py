"""147 reach audit (Codex 147 Q4 / Q5, descriptive): the 92 'window-outside' absent molecules of the 140 ledger (P c2, fold-1 development,
820 molecules). For each: library, labelled query adducts, ppm error between the truth's monoisotopic neutral mass and the query-derived neutral
mass (median over the selected queries, labelled adduct), and whether another common adduct explains the precursor within 10 ppm.
Purpose: is the dev window loss a library-metadata artefact (absent from the clean Enveda hidden test) or a genuine reach limit?
Usage: python -X utf8 experiments/e2/x147_window_audit.py"""
import os, sys
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
from rdkit import Chem, RDLogger
from rdkit.Chem.Descriptors import ExactMolWt
RDLogger.DisableLog("rdApp.*")


def main():
    L = pd.read_parquet(os.path.join(ROOT, "experiments/w135/ledger/ledger.parquet")); L["molecule"] = L.molecule.astype(str)
    W = L[L.layer == "absent"]; print("absent sub-layers:", W["sub"].value_counts().to_dict())
    csvs = [os.path.join(ROOT, "experiments/b1_baseline", d, "p2_molecules.csv") for d in ("eval_set_f1", "np053_f1dev")]
    ev = pd.concat([pd.read_csv(c) for c in csvs]); ev["molecule"] = ev.molecule.astype(str); ev = ev.drop_duplicates(["set", "molecule"]).set_index(["set", "molecule"])
    ts = pd.read_parquet(os.path.join(ROOT, "data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet"), columns=["key", "smiles"]).drop_duplicates("key")
    k2s = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    st = os.path.join(ROOT, "data/processed/spectra_store"); meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "precursor_mz", "ce_mean", "ionization_mode"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); prec_of_row = meta["precursor_mz"].to_numpy().astype(float); ce_of_row = meta["ce_mean"].to_numpy().astype(float); mode_of_row = meta["ionization_mode"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    out = []
    for r in W.itertuples(index=False):
        e = ev.loc[(r.set, r.molecule)]; smi = k2s.get(str(e.scorer_key)); m = Chem.MolFromSmiles(smi) if smi else None
        M_true = ExactMolWt(m) if m is not None else np.nan; lib = e.lib; sh = ELECTRON if lib == "enveda-180" else 0.0
        qrows = sorted(int(x) for x in ik_rows.get(r.molecule, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        Ms = [float(prec_of_row[x]) - (sh if mode_of_row[x] == "positive" else 0.0) + ADDUCT_SHIFT[add_of_row[x]] for x in q]
        ppm = (np.median(Ms) - M_true) / M_true * 1e6 if Ms and np.isfinite(M_true) else np.nan
        alt = []
        for x in q:
            p_ = float(prec_of_row[x]) - (sh if mode_of_row[x] == "positive" else 0.0)
            for ad, d in ADDUCT_SHIFT.items():
                if (ad.endswith("+")) != (mode_of_row[x] == "positive"): continue
                if abs((p_ + d - M_true) / M_true * 1e6) <= 10: alt.append(ad)
        out.append(dict(set=r.set, molecule=r.molecule, sub=r["sub"] if isinstance(r, dict) else getattr(r, "sub"), lib=lib, adducts=",".join(sorted({add_of_row[x] for x in q})), n_q=len(q), ppm=ppm,
                        alt_adducts=",".join(sorted(set(alt)))))
    O = pd.DataFrame(out); O.to_csv(os.path.join(ROOT, "experiments/e2/x147_window_audit.csv"), index=False)
    for sub, g in O.groupby("sub"):
        print(f"\n== {sub}: n {len(g)}"); print("libraries:", g.lib.value_counts().to_dict())
        a = g.ppm.abs(); print(f"|ppm|: <=10 {int((a <= 10).sum())}, 10-50 {int(((a > 10) & (a <= 50)).sum())}, >50 {int((a > 50).sum())}, nan {int(a.isna().sum())}")
        print("explained by another listed adduct within 10 ppm:", int((g.alt_adducts != "").sum()), "| examples:", g[g.alt_adducts != ""].alt_adducts.value_counts().head(5).to_dict())


if __name__ == "__main__":
    main()
