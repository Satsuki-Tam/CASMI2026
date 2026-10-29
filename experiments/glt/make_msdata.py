"""105 GLACIER adaptation: write an ms-pred dataset directory (labels.tsv + spec_files.hdf5 of SIRIUS-style .ms texts + splits/split.tsv) from
MassSpecGym rows (--msg_ids or --msg_n, stage 0) so that ms-pred's own MAGMa (src/ms_pred/magma/run_magma.py) and GLACIER's IntenDataset can read it.
.ms layout (ms_pred.common.parse_spectra): header lines '>key value' / '#key value', one blank line, then per spectrum '>collision <eV>' and
'mz intensity' lines. labels.tsv columns as MIST/ms-pred msg_all: dataset, spec, ionization, formula, smiles, inchikey, instrument,
collision_energies, precursor. Split file: name / split (train | val | test) by the --split rule.
Usage (Spark, .venv-glt): python experiments/glt/make_msdata.py --out data/glt/stage0 --msg_n 16 [--seed 0]"""
import argparse, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--msg_n", type=int, default=16); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--msg_tsv", default=os.path.join(ROOT, "data/external/massspecgym/MassSpecGym.tsv")); a = ap.parse_args()
sys.path.insert(0, os.path.join(ROOT, "data/external/ms-pred-train/ms-pred/src"))
import h5py
os.makedirs(os.path.join(a.out, "splits"), exist_ok=True)
msg = pd.read_csv(a.msg_tsv, sep="\t", usecols=["identifier", "mzs", "intensities", "smiles", "inchikey", "formula", "precursor_mz", "adduct", "instrument_type", "collision_energy", "fold"])
msg = msg[(msg.adduct == "[M+H]+") & msg.collision_energy.notna()]
rng = np.random.default_rng(a.seed); keys = sorted(msg.inchikey.unique()); pick = set(rng.permutation(keys)[:a.msg_n])
sel = msg[msg.inchikey.isin(pick)].groupby("inchikey", sort=True).head(2).reset_index(drop=True)   # up to 2 spectra per molecule
rows, h5 = [], h5py.File(os.path.join(a.out, "spec_files.hdf5"), "w")
dt = h5py.special_dtype(vlen=str)
for r in sel.itertuples(index=False):
    ce = float(r.collision_energy); mz = [float(x) for x in str(r.mzs).split(",")]; it = [float(x) for x in str(r.intensities).split(",")]
    txt = (f">compound {r.identifier}\n>formula {r.formula}\n>parentmass {float(r.precursor_mz)!r}\n>ionization {r.adduct}\n>InChIKey {r.inchikey}\n#smiles {r.smiles}\n"
           f"#INSTRUMENT TYPE {r.instrument_type}\n\n>collision {ce:g}\n" + "\n".join(f"{m!r} {i!r}" for m, i in zip(mz, it)) + "\n")
    ds_ = h5.create_dataset(f"{r.identifier}.ms", (1,), dtype=dt, compression="gzip"); ds_[0] = txt   # = ms_pred.common.HDF5Dataset.write_str (read_str reads [0])
    rows.append(dict(dataset="MassSpecGym", spec=r.identifier, ionization=r.adduct, formula=r.formula, smiles=r.smiles, inchikey=r.inchikey, instrument=r.instrument_type,
                     collision_energies=str([f"{ce:g}"]), precursor=float(r.precursor_mz)))
h5.close()
L = pd.DataFrame(rows); L.to_csv(os.path.join(a.out, "labels.tsv"), sep="\t", index=False)
sp = ["train" if i % 4 else "val" for i in range(len(L))]
pd.DataFrame(dict(name=L.spec, split=sp)).to_csv(os.path.join(a.out, "splits", "split.tsv"), sep="\t", index=False)
print(f"wrote {len(L)} spectra of {L.inchikey.nunique()} molecules to {a.out}")
