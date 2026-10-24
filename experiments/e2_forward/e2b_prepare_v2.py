"""E2b v2 prep: same-formula isomer panels for molecules absent from MassSpecGym, with the fixes from Codex review 002.

Changes vs v1:
  * MassSpecGym exclusion uses the official scorer key (stereo removed, tautomer-canonical InChIKey14) in addition to raw keys.
  * Input spectra are restricted to the molecule's selection library (set A: enveda-180 = timsTOF only); instrument and library
    of every input spectrum are recorded.
  * The electron-mass correction is applied consistently (enveda-180 only) to spectra AND to the neutral mass of the candidate window.
  * Candidate identity and truth matching use the official scorer key for the selected candidates (window pre-filter by raw key,
    then the truth and the chosen decoys are canonicalised; decoys sharing the truth's key are removed and counted).
  * `truth_in_retrieval_window` replaces `truth_in_pubchem` (it only says whether the truth's raw key was in this tier's window).
  * The |precursor_error_ppm| < 10 selection filter is label-derived (not available at test time); it is kept as a label-quality
    filter mirroring the organisers' own test cleaning and its exclusion rate is recorded per library.

Usage: python -I -X utf8 e2b_prepare_v2.py <pubchem_tier_dir> <raw_dir> <processed_dir> <folds_dir> <msg_tsv> <out_dir> [n_mol] [n_cand] [seed] [random|hard]
"""
import json, sys, time
import numpy as np, pandas as pd, polars as pl
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.MolStandardize import rdMolStandardize
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
TAUT = rdMolStandardize.TautomerEnumerator()
t0 = time.time()
import os; os.makedirs(OUT, exist_ok=True)


def scorer_key(mol):
    try:
        m = Chem.Mol(mol); Chem.RemoveStereochemistry(m)
        return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]
    except Exception:
        return None


# ---- MassSpecGym identities: raw keys + official scorer keys of all unique MSG SMILES
msg = pl.read_csv(MSG, separator="\t", columns=["inchikey", "smiles"], infer_schema_length=10000, ignore_errors=True)
msg_raw = set(msg["inchikey"].str.slice(0, 14).drop_nulls().to_list())
msg_keys = set()
for smi in msg["smiles"].drop_nulls().unique().to_list():
    m = Chem.MolFromSmiles(smi)
    if m is not None:
        k = scorer_key(m)
        if k: msg_keys.add(k)
print(f"MSG: {len(msg_raw)} raw keys, {len(msg_keys)} scorer keys ({time.time()-t0:.0f}s)", flush=True)

folds = pd.read_parquet(f"{FOLDS}/structures.parquet")[["inchikey14", "fold_identity"]].drop_duplicates("inchikey14").set_index("inchikey14")
keys = pl.read_parquet(f"{PROC}/train_scorer_keys.parquet").select("normalized_smiles", "scorer_ik14")
meta = pl.read_parquet(f"{PROC}/train_meta.parquet").join(keys, on="normalized_smiles", how="left")
pos_all = meta.filter((pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive"))
pos = pos_all.filter(pl.col("precursor_error_ppm").abs().lt(10))
excl = pos_all.group_by("ingest_lib").agg(pl.len().alias("n"), (pl.col("precursor_error_ppm").abs() >= 10).sum().alias("n_excluded_ppm"))
print("label-quality filter |ppm|<10 exclusions by library:", excl.sort("n", descending=True).to_dict(as_series=False), flush=True)


def pick(lib_filter, name):
    d = pos.filter(lib_filter).filter(~pl.col("inchikey14").is_in(list(msg_raw)) & ~pl.col("scorer_ik14").is_in(list(msg_keys)))
    mols = (d.group_by("inchikey14").agg(pl.col("normalized_smiles").first(), pl.col("scorer_ik14").first(), pl.col("molecular_formula").first(),
                                         pl.len().alias("n_spec"), pl.col("ingest_lib").first())
            .sort("inchikey14").to_pandas())
    if name == "timstof_unseen":
        mols = mols[mols.inchikey14.map(lambda k: folds.fold_identity.get(k, -1) == 0)]
    mols = mols.sort_values("inchikey14").sample(n=min(N_MOL, len(mols)), random_state=SEED)
    print(f"{name}: eligible {len(d['inchikey14'].unique())}, sampled {len(mols)}; libs {mols.ingest_lib.value_counts().to_dict()}", flush=True)
    return mols


sets = {"timstof_unseen": pick(pl.col("ingest_lib") == "enveda-180", "timstof_unseen"),
        "np_unseen": pick(pl.col("ingest_lib").is_in(["gnps", "riken", "mona", "massbank", "msdial"]), "np_unseen")}
all_ids = sorted(set().union(*[set(m.inchikey14) for m in sets.values()]))
lib_of = {r.inchikey14: r.ingest_lib for m in sets.values() for r in m.itertuples(index=False)}

sp = (pl.scan_parquet(f"{RAW}/train.parquet")
      .filter(pl.col("inchikey14").is_in(all_ids) & (pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive"))
      .select("inchikey14", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type",
              "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units", "ingest_lib", "precursor_error_ppm").collect())
sp = sp.filter(pl.col("precursor_error_ppm").abs() < 10).sort("inchikey14", "precursor_mz")
spectra_by = {}
for s in sp.iter_rows(named=True):
    if s["ingest_lib"] != lib_of.get(s["inchikey14"]):      # restrict to the selection library (set A: timsTOF only)
        continue
    shift = ELECTRON if s["ingest_lib"] == "enveda-180" else 0.0
    spectra_by.setdefault(s["inchikey14"], []).append(dict(
        mz=[float(x) - shift for x in s["ms2_mzs"]], it=[float(x) for x in s["ms2_normalized_intensities"]], prec=float(s["precursor_mz"]) - shift,
        adduct=s["adduct"], mode=s["ionization_mode"], instrument=s["instrument_type"], lib=s["ingest_lib"],
        ce_ev=[float(x) for x in s["collision_energy_ev"]] if s["collision_energy_ev"] is not None else None,
        ce_orig=s["collision_energy_orig"], ce_units=s["collision_energy_orig_units"]))
print(f"spectra fetched for {len(spectra_by)} molecules ({time.time()-t0:.0f}s)", flush=True)

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
        spectra = spectra_by[r.inchikey14][:8]
        truth_raw = Chem.MolToInchiKey(tm)[:14]; truth_key = scorer_key(tm); f_truth = CalcMolFormula(tm)
        prec = float(np.median([s["prec"] for s in spectra]))          # corrected precursor m/z
        cands = {}
        for s in window_smiles(prec - PROTON):
            m = Chem.MolFromSmiles(s)
            if m is None or CalcMolFormula(m) != f_truth: continue
            k = Chem.MolToInchiKey(m)[:14]
            if k not in cands: cands[k] = (s, m)
        in_window = truth_raw in cands
        cands.pop(truth_raw, None)
        others = sorted(cands.items())
        if len(others) > N_CAND - 1:
            if MODE == "hard":
                tfp = FPG.GetFingerprint(tm)
                sims = np.array([DataStructs.TanimotoSimilarity(tfp, FPG.GetFingerprint(m)) for _, (s, m) in others])
                order = np.argsort(-sims, kind="stable")[: N_CAND - 1]; others = [others[i] for i in order]
            else:
                idx = rng.choice(len(others), N_CAND - 1, replace=False); others = [others[i] for i in idx]
        # official identity for the selected candidates: drop decoys that are the same scored identity as the truth, merge duplicates
        seen = {truth_key}; cand_smiles = [r.normalized_smiles]; n_alias = 0
        for _, (s, m) in others:
            k = scorer_key(m)
            if k is None or k in seen:
                n_alias += int(k == truth_key); continue
            seen.add(k); cand_smiles.append(s)
        items.append(dict(mid=r.inchikey14, spectra=spectra, cands=cand_smiles))
        rows.append(dict(molecule=r.inchikey14, scorer_key=truth_key, lib=r.ingest_lib, formula=f_truth, n_window_same_formula=len(cands) + int(in_window),
                         truth_in_retrieval_window=in_window, n_cands=len(cand_smiles), n_truth_aliases_removed=n_alias, n_spectra=len(spectra),
                         instruments="|".join(sorted({s["instrument"] or "" for s in spectra})), spectra_libs="|".join(sorted({s["lib"] for s in spectra}))))
        if (j + 1) % 50 == 0: print(f"  {name}: {j+1}/{len(mols)} ({time.time()-t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/e2b_{name}{SUFFIX}_molecules.csv", index=False)
    json.dump(items, open(f"{OUT}/e2b_{name}{SUFFIX}_in.json", "w"))
    n_pred = sum(len(it["cands"]) * len({(s["adduct"], tuple(s["ce_ev"] or [])) for s in it["spectra"]}) for it in items)
    line = (f"{name}{SUFFIX}: {len(items)} molecules | truth in retrieval window {int(df.truth_in_retrieval_window.sum())} | same-formula isomers: median {df.n_window_same_formula.median():.0f}, "
            f"p90 {df.n_window_same_formula.quantile(.9):.0f} | candidates median {df.n_cands.median():.0f} | truth aliases removed {int(df.n_truth_aliases_removed.sum())} | "
            f"instruments {df.instruments.value_counts().to_dict()} | ~{n_pred:,} predictions | {time.time()-t0:.0f}s")
    print(line, flush=True); summary.append(line)
open(f"{OUT}/e2b_summary{SUFFIX}.txt", "w").write("\n".join(summary))
