"""E2b prep: uncontaminated forward-model diagnostic sets (deterministic; random or hard decoys).

Set A ("timstof_unseen"): enveda-180 molecules in identity fold 0 that are NOT in MassSpecGym and have [M+H]+ spectra.
Set B ("np_unseen")     : natural-product-library molecules (gnps/riken/mona/massbank/msdial) NOT in MassSpecGym with
                          positive [M+H]+ spectra (other instruments; tests NP chemistry generalisation).
For each molecule: candidates = PubChem tier structures within 10 ppm of the neutral mass whose formula equals the
truth's formula (RDKit), deduplicated on InChIKey14, capped at N_CAND (truth always first; if the truth is absent
from PubChem it is added explicitly). MODE random: decoys sampled uniformly; MODE hard: the N_CAND-1 decoys with the
highest Morgan(2, 2048) Tanimoto to the truth. Spectra: the molecule's [M+H]+ spectra (max 8); enveda-180
positive-mode m/z shifted by -0.000548 Da (host advice: hidden test corrected for the electron mass, train was not).
Molecule sampling is deterministic: candidates are sorted by inchikey14 before pandas.sample(random_state=SEED).

Usage: python -I -X utf8 e2b_prepare.py <pubchem_tier_dir> <raw_dir> <processed_dir> <folds_dir> <msg_tsv> <out_dir> [n_mol] [n_cand] [seed] [random|hard]
Outputs: e2b_<set>[_hard]_in.json, e2b_<set>[_hard]_molecules.csv, e2b_summary[_hard].txt
"""
import json, sys, time
import numpy as np, pandas as pd, polars as pl
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")

T, RAW, PROC, FOLDS, MSG, OUT = sys.argv[1:7]
N_MOL = int(sys.argv[7]) if len(sys.argv) > 7 else 200
N_CAND = int(sys.argv[8]) if len(sys.argv) > 8 else 100
SEED = int(sys.argv[9]) if len(sys.argv) > 9 else 0
MODE = sys.argv[10] if len(sys.argv) > 10 else "random"
SUFFIX = "" if MODE == "random" else f"_{MODE}"
PROTON, ELECTRON, PPM = 1.007276, 0.000548, 10.0
rng = np.random.default_rng(SEED)
FPG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
t0 = time.time()

msg_ik = set(pl.read_csv(MSG, separator="\t", columns=["inchikey"], infer_schema_length=10000, ignore_errors=True)["inchikey"].str.slice(0, 14).drop_nulls().to_list())
folds = pd.read_parquet(f"{FOLDS}/structures.parquet")[["inchikey14", "fold_identity"]].drop_duplicates("inchikey14").set_index("inchikey14")
meta = pl.read_parquet(f"{PROC}/train_meta.parquet")
pos = meta.filter((pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive") & pl.col("precursor_error_ppm").abs().lt(10))
print(f"loaded in {time.time()-t0:.0f}s | mode {MODE}", flush=True)


def pick(lib_filter, name):
    d = pos.filter(lib_filter).filter(~pl.col("inchikey14").is_in(list(msg_ik)))
    mols = (d.group_by("inchikey14").agg(pl.col("normalized_smiles").first(), pl.col("molecular_formula").first(), pl.len().alias("n_spec"),
                                         pl.col("ingest_lib").first(), pl.col("precursor_mz").median().alias("prec"))
            .sort("inchikey14").to_pandas())
    if name == "timstof_unseen":
        mols = mols[mols.inchikey14.map(lambda k: folds.fold_identity.get(k, -1) == 0)]
    mols = mols.sort_values("inchikey14").sample(n=min(N_MOL, len(mols)), random_state=SEED)
    print(f"{name}: sampled {len(mols)}; libs {mols.ingest_lib.value_counts().to_dict()}; first {mols.inchikey14.iloc[0]}", flush=True)
    return mols


sets = {"timstof_unseen": pick(pl.col("ingest_lib") == "enveda-180", "timstof_unseen"),
        "np_unseen": pick(pl.col("ingest_lib").is_in(["gnps", "riken", "mona", "massbank", "msdial"]), "np_unseen")}
all_ids = sorted(set().union(*[set(m.inchikey14) for m in sets.values()]))

sp = (pl.scan_parquet(f"{RAW}/train.parquet")
      .filter(pl.col("inchikey14").is_in(all_ids) & (pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive"))
      .select("inchikey14", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type",
              "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units", "ingest_lib", "precursor_error_ppm").collect())
sp = sp.filter(pl.col("precursor_error_ppm").abs() < 10).sort("inchikey14", "precursor_mz")
print(f"spectra fetched: {sp.height} rows for {sp['inchikey14'].n_unique()} molecules in {time.time()-t0:.0f}s", flush=True)
spectra_by = {}
for s in sp.iter_rows(named=True):
    shift = ELECTRON if s["ingest_lib"] == "enveda-180" else 0.0
    spectra_by.setdefault(s["inchikey14"], []).append(dict(
        mz=[float(x) - shift for x in s["ms2_mzs"]], it=[float(x) for x in s["ms2_normalized_intensities"]], prec=float(s["precursor_mz"]) - shift,
        adduct=s["adduct"], mode=s["ionization_mode"], instrument=s["instrument_type"],
        ce_ev=[float(x) for x in s["collision_energy_ev"]] if s["collision_energy_ev"] is not None else None,
        ce_orig=s["collision_energy_orig"], ce_units=s["collision_energy_orig_units"]))

mass = np.load(f"{T}/pc_mass.npy", mmap_mode="r"); off = np.load(f"{T}/pc_off.npy", mmap_mode="r"); buf = np.load(f"{T}/pc_smiles.npy", mmap_mode="r")


def window_smiles(target):
    tol = target * PPM * 1e-6
    a = int(np.searchsorted(mass, target - tol, "left")); b = int(np.searchsorted(mass, target + tol, "right"))
    if b <= a: return []
    o = np.asarray(off[a:b + 1]).astype(np.int64); raw = bytes(buf[o[0]:o[-1]]); base = o[0]
    return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(b - a)]


summary = []
for name, mols in sets.items():
    items, rows = [], []
    for j, r in enumerate(mols.itertuples(index=False)):
        tm = Chem.MolFromSmiles(r.normalized_smiles)
        if tm is None or r.inchikey14 not in spectra_by: continue
        truth_ik = Chem.MolToInchiKey(tm)[:14]; f_truth = CalcMolFormula(tm)
        cands = {}
        for s in window_smiles(float(r.prec) - PROTON):
            m = Chem.MolFromSmiles(s)
            if m is None or CalcMolFormula(m) != f_truth: continue
            k = Chem.MolToInchiKey(m)[:14]
            if k not in cands: cands[k] = (s, m)
        in_pubchem = truth_ik in cands
        cands.pop(truth_ik, None)
        others = sorted(cands.items())                       # deterministic order before sampling
        if len(others) > N_CAND - 1:
            if MODE == "hard":
                tfp = FPG.GetFingerprint(tm)
                sims = np.array([DataStructs.TanimotoSimilarity(tfp, FPG.GetFingerprint(m)) for _, (s, m) in others])
                order = np.argsort(-sims, kind="stable")[: N_CAND - 1]
                others = [others[i] for i in order]
            else:
                idx = rng.choice(len(others), N_CAND - 1, replace=False); others = [others[i] for i in idx]
        cand_smiles = [r.normalized_smiles] + [s for _, (s, m) in others]
        items.append(dict(mid=r.inchikey14, spectra=spectra_by[r.inchikey14][:8], cands=cand_smiles))
        rows.append(dict(molecule=r.inchikey14, lib=r.ingest_lib, formula=f_truth, n_window_same_formula=len(cands) + int(in_pubchem),
                         truth_in_pubchem=in_pubchem, n_cands=len(cand_smiles), n_spectra=min(8, len(spectra_by[r.inchikey14]))))
        if (j + 1) % 50 == 0: print(f"  {name}: {j+1}/{len(mols)} ({time.time()-t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/e2b_{name}{SUFFIX}_molecules.csv", index=False)
    json.dump(items, open(f"{OUT}/e2b_{name}{SUFFIX}_in.json", "w"))
    n_pred = sum(len(it["cands"]) * len({(s["adduct"], tuple(s["ce_ev"] or [])) for s in it["spectra"]}) for it in items)
    line = (f"{name}{SUFFIX}: {len(items)} molecules | truth in PubChem {int(df.truth_in_pubchem.sum())} | same-formula isomers in window: median {df.n_window_same_formula.median():.0f}, "
            f"p90 {df.n_window_same_formula.quantile(.9):.0f} | candidates median {df.n_cands.median():.0f} | ~{n_pred:,} predictions | {time.time()-t0:.0f}s")
    print(line, flush=True); summary.append(line)
open(f"{OUT}/e2b_summary{SUFFIX}.txt", "w").write("\n".join(summary))
