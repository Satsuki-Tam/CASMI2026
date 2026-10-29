"""105 GLACIER timsTOF adaptation, stage 1 data: an ms-pred dataset (labels.tsv, spec_files.hdf5, splits/split.tsv, manifest.json) of competition
train spectra measured on timsTOF (ingest_lib enveda-180), adduct [M+H]+, from identity folds 3 / 4 only (folds 1 / 2 = our development tables,
fold 0 = our confirmation sets), minus every identity group that appears in any selection roster of experiments/b1_baseline (p1 / p2_molecules.csv,
panel) -- label-free selection (no model output is read).
Per identity: up to --per_id spectra with distinct rounded CE (eV), lowest row first; enveda-180 positive spectra get the store's electron-mass
correction (m/z and precursor - ELECTRON, as b1_features). Identities are taken in the order of sha256(salt + identity key) (fixed, no peeking);
split by the same hash (val = every 10th). The SMILES is the training structure of the scorer key (train_structs.parquet). Instrument token
'QTOF' (= gl_runner's token for timsTOF queries).
Usage (Spark, .venv-glt): python experiments/glt/make_glt_data.py --out data/glt/tims_s1 --n_id 2000 [--per_id 4] [--salt glt105]"""
import argparse, glob, hashlib, json, os, sys
import numpy as np, pandas as pd, polars as pl, h5py
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments", "b1_baseline"))
from b1_common import ELECTRON
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--n_id", type=int, default=2000); ap.add_argument("--per_id", type=int, default=4)
ap.add_argument("--salt", default="glt105"); ap.add_argument("--folds", default="3,4"); a = ap.parse_args()
S = os.path.join(ROOT, "data/processed/spectra_store")
meta = pl.read_parquet(f"{S}/spec_meta.parquet"); folds = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/spectra_folds.parquet"))
m = meta.join(folds.select(["row", "identity_group", "fold_identity"]), on="row", how="left")
FOLDS = [int(x) for x in a.folds.split(",")]
cand = m.filter((pl.col("ingest_lib") == "enveda-180") & (pl.col("adduct") == "[M+H]+") & pl.col("fold_identity").is_in(FOLDS) & pl.col("scorer_ik14").is_not_null() & pl.col("ce_mean").is_not_null())
# every identity group used by any roster (development, confirmation, panel, spares): never trained on
used = set()
for f in glob.glob(os.path.join(ROOT, "experiments/b1_baseline/**/p[12]_molecules.csv"), recursive=True):
    try: d = pd.read_csv(f, usecols=lambda c: c in ("identity_group", "molecule", "scorer_key"))
    except Exception: continue
    if "identity_group" in d.columns: used |= set(int(x) for x in d.identity_group.dropna().astype(int) if int(x) >= 0)
panel_ids = set(m.filter(pl.col("ingest_lib") == "enveda-np-examples")["identity_group"].drop_nulls().to_list())
cand = cand.filter(~pl.col("identity_group").is_in(sorted(used | panel_ids)))
ts = pd.read_parquet(os.path.join(ROOT, "data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet"), columns=["key", "smiles"]).drop_duplicates("key")
KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
cand = cand.filter(pl.col("scorer_ik14").is_in(list(KEY_SMI)))
ids = sorted(set(cand["identity_group"].to_list()), key=lambda g: hashlib.sha256(f"{a.salt}|{g}".encode()).hexdigest())[:a.n_id]
sel = cand.filter(pl.col("identity_group").is_in(ids)).sort(["identity_group", "row"]).to_pandas()
S_MZ = np.load(f"{S}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{S}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{S}/spec_off.npy")
os.makedirs(os.path.join(a.out, "splits"), exist_ok=True)
h5 = h5py.File(os.path.join(a.out, "spec_files.hdf5"), "w"); dt = h5py.special_dtype(vlen=str); rows = []
for g, h in sel.groupby("identity_group", sort=False):
    h = h.assign(ce_r=h.ce_mean.round(0)).drop_duplicates("ce_r").head(a.per_id)
    for r in h.itertuples(index=False):
        sh = ELECTRON if r.ionization_mode == "positive" else 0.0
        so, eo = int(S_OFF[r.row]), int(S_OFF[r.row + 1]); mz = np.asarray(S_MZ[so:eo], np.float64) - sh; it = np.asarray(S_IT[so:eo], np.float64)
        if len(mz) == 0: continue
        prec = float(r.precursor_mz) - sh; name = f"glt_{int(r.row)}"; smi = KEY_SMI[str(r.scorer_ik14)]
        txt = (f">compound {name}\n>parentmass {prec!r}\n>ionization [M+H]+\n>InChIKey {r.scorer_ik14}\n#smiles {smi}\n#INSTRUMENT TYPE QTOF\n\n>collision {float(r.ce_mean):g}\n"
               + "\n".join(f"{x!r} {y!r}" for x, y in zip(mz.tolist(), it.tolist())) + "\n")
        ds_ = h5.create_dataset(f"{name}.ms", (1,), dtype=dt, compression="gzip"); ds_[0] = txt
        rows.append(dict(dataset="casmi26_enveda180", spec=name, ionization="[M+H]+", formula="", smiles=smi, inchikey=str(r.scorer_ik14), instrument="QTOF",
                         collision_energies=str([f"{float(r.ce_mean):g}"]), precursor=prec, identity_group=int(g), fold_identity=int(r.fold_identity), store_row=int(r.row)))
h5.close()
L = pd.DataFrame(rows)
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
L["formula"] = [CalcMolFormula(Chem.MolFromSmiles(s)) if Chem.MolFromSmiles(s) is not None else "" for s in L.smiles]
L = L[L.formula != ""]
L.to_csv(os.path.join(a.out, "labels.tsv"), sep="\t", index=False)
val = {g for g in L.identity_group.unique() if int(hashlib.sha256(f"{a.salt}|split|{g}".encode()).hexdigest(), 16) % 10 == 0}
pd.DataFrame(dict(name=L.spec, split=["val" if g in val else "train" for g in L.identity_group])).to_csv(os.path.join(a.out, "splits", "split.tsv"), sep="\t", index=False)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man = dict(n_identity_requested=a.n_id, n_identity=int(L.identity_group.nunique()), n_spectra=len(L), per_id=a.per_id, folds=FOLDS, salt=a.salt, used_identity_groups_excluded=len(used),
           panel_groups_excluded=len(panel_ids), candidates_after_exclusion=int(cand["identity_group"].n_unique()), val_identities=len(val),
           ce_quantiles=[float(x) for x in np.quantile(L.collision_energies.map(lambda s: float(eval(s)[0])), [0, 0.25, 0.5, 0.75, 1])],
           files={f: sha(os.path.join(a.out, f)) for f in ("labels.tsv", "spec_files.hdf5", "splits/split.tsv")})
json.dump(man, open(os.path.join(a.out, "manifest.json"), "w"), indent=1); print(json.dumps(man, indent=1))
