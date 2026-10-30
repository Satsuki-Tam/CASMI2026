"""145 (Codex 145 Q1, third mask point): in the C2 view the truth's train-only spellings must vanish, but b1_ewin merges the official key's spellings
(best f.z representative) BEFORE the view masks. This audit rebuilds the E window (e2_engine.EStores, the same stores) of every development C2
molecule and classifies the truth row's representative SMILES (the E table's smiles) by its own source flags in the window:
  visible = the representative SMILES string itself comes from COCONUT / PubChemLite / BIO (visible in C2) -> no optimism;
  train_only = the representative comes only from the train pool -> its f.z may exceed every C2-visible spelling (possible optimism);
  absent = not found (should not happen).
Writes experiments/e2/x145_alias_audit.csv (tag, set, molecule, class, n spellings of the truth key by source) + a summary. No model, no score.
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/x145_alias_audit.py"""
import os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
TAGS = {"np053f1dev": ("np053_f1dev", "p2_molecules.csv", ["NP_H", "NP_X", "NP_N"]), "np053f2dev": ("np053_f2dev", "p2_molecules.csv", ["NP_H", "NP_X", "NP_N"]),
        "f1dev": ("eval_set_f1", "p2_molecules.csv", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]),
        "f2dev": ("eval_set_f2", "p2_molecules.csv", ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]), "panel": ("panel_np250", "p1_molecules.csv", ["P_np250"])}
G = {}


def _init():   # workers read with pandas only: polars after fork can deadlock (the v1 run hung with every worker asleep)
    from e2_engine import EStores
    K = os.path.join(ROOT, "data/external_kaggle"); tier = os.path.join(ROOT, "data/external/pubchem_tier")
    pa = pd.read_parquet(f"{K}/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet", columns=["tier_row"]); pcl = np.unique(pa.tier_row[pa.tier_row >= 0].to_numpy())
    bio = pd.read_parquet(f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi-chebi-lmsd-structures/casmi-chebi-lmsd-structures/bio_structures.parquet", columns=["smiles", "monoisotopic_mass"]).dropna()
    pool = pd.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "smiles", "mass", "src", "pid"])
    csmi = pd.read_parquet(os.path.join(ROOT, "data/external/coconut/coco_meta.parquet"), columns=["smiles"]).smiles.to_numpy(); cmass = np.load(os.path.join(ROOT, "data/external/coconut/coco_mass.npy"))
    G["st"] = EStores(np.load(f"{tier}/pc_mass.npy", mmap_mode="r"), np.load(f"{tier}/pc_off.npy", mmap_mode="r"), np.load(f"{tier}/pc_smiles.npy", mmap_mode="r"), pcl, pool, cmass, csmi, bio)


def _one(t):
    tag, s, mid, M_by_add, rep = t; src = G["st"].window(M_by_add); d = src.get(rep)
    if d is None: return (tag, s, mid, "absent")
    return (tag, s, mid, "visible" if (d["coco"] or d["pcl"] or d["bio"]) else "train_only")


def main():
    t0 = time.time(); st = os.path.join(ROOT, "data/processed/spectra_store")
    meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64)
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    tasks = []; info = []
    for tag, (d, csv, sets) in TAGS.items():
        ev = pd.read_csv(os.path.join(ROOT, "experiments/b1_baseline", d, csv)); ev["molecule"] = ev.molecule.astype(str)
        for s in sets:
            E = pd.read_parquet(os.path.join(ROOT, "experiments/e2/ewin", d, f"ewin_{s}.parquet")); E["molecule"] = E.molecule.astype(str)
            T = E[E.is_truth]
            for r in T.itertuples(index=False):
                ok_c2 = not (r.in_train_c1 and not r.in_train_c2 and not (r.in_coconut or r.in_pcl or r.in_bio))   # the truth row survives in the C2 window
                info.append(dict(tag=tag, set=s, molecule=r.molecule, truth_train=bool(r.in_train_c1), truth_other=bool(r.in_coconut or r.in_pcl or r.in_bio), in_c2_window=ok_c2))
                if not (ok_c2 and r.in_train_c1): continue   # only truths that are ALSO train structures can carry a train-only representative
                lib = ev.loc[ev.molecule == r.molecule, "lib"].iloc[0]; shift = ELECTRON if lib == "enveda-180" else 0.0
                qr = select_queries(sorted(int(x) for x in ik_rows.get(r.molecule, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT), 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
                Mb = {}
                for x in qr:
                    sh = shift if mode_of_row[x] == "positive" else 0.0; Mb.setdefault(add_of_row[x], []).append(float(prec_of_row[x]) - sh + ADDUCT_SHIFT[add_of_row[x]])
                tasks.append((tag, s, r.molecule, {k: float(np.median(v)) for k, v in Mb.items()}, r.smiles))
    print(f"{len(info)} truth rows, {len(tasks)} to rebuild ({time.time()-t0:.0f}s)", flush=True)
    import multiprocessing as _mp
    with _mp.get_context("spawn").Pool(12, initializer=_init) as wp: res = wp.map(_one, tasks, chunksize=8)   # spawn: no inherited polars threads
    A = pd.DataFrame(info).merge(pd.DataFrame(res, columns=["tag", "set", "molecule", "rep_class"]), on=["tag", "set", "molecule"], how="left")
    A["rep_class"] = A.rep_class.where(A.rep_class.notna(), pd.Series(np.where(A.truth_train, "not_in_c2", "no_train_spelling"), index=A.index))
    A.to_csv(os.path.join(ROOT, "experiments/e2/x145_alias_audit.csv"), index=False)
    print(A.groupby(["tag", "rep_class"]).size().unstack(fill_value=0).to_string()); print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
