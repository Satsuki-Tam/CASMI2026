"""W135 step 0 (135_decision.md §4-(i)): population census for the class-3 common-world batches -- COUNTS ONLY (no candidate, generation or
model output is read). Population = identities of identity fold 1 (unseen by the fold-1 fold-safe FPNet), not in MassSpecGym (raw or scorer
key), not a panel (enveda-np-examples) key, truth = a COCONUT structure (scorer key in the v2 pool with the COCONUT bit or raw key in the
COCONUT store, as p3_select_np.py), with at least one spectrum with a test adduct. Per identity: used-in-development flag (any key / identity
group of the exclusion files of p3_select_np's manifest, plus the dev tables made after it), timsTOF (enveda-180) availability, other
libraries, polarity, neutral mass band. Families: Morgan radius 2 / 2048 bits on the official-key structure (RemoveStereochemistry ->
tautomer canonical), Butina sphere exclusion; the size distribution is reported for several similarity thresholds (the threshold is fixed
in 136 by a rule written before this census: see w135_census.md). Murcko generic scaffolds are counted as an auxiliary.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_census.py"""
import glob, hashlib, json, os, pickle, sys, time
import numpy as np, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline")
sys.path.insert(0, B)
from b1_common import ADDUCT_SHIFT
FOLD = int(os.environ.get("W135_FOLD", "1")); OUT = os.path.join(ROOT, "experiments/w135/census" + ("" if FOLD == 1 else f"_fold{FOLD}")); os.makedirs(OUT, exist_ok=True); t0 = time.time()
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
census = pl.read_parquet(os.path.join(B, "eval_set2/census.parquet"))
folds = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet")).unique("inchikey14")
meta = pl.read_parquet(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet")).filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)))
pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"])
POOL_COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
COCO_RAW = set(str(x) for x in pickle.load(open(os.path.join(ROOT, "data/external/coconut/coco_meta.pkl"), "rb"))["keys"])   # own file (built by our COCONUT prep)
# used identities: every molecule table under experiments/ (dev, conf, locked, train pools, panels) -- conservative
used = set(); used_files = sorted(set(glob.glob(os.path.join(ROOT, "experiments/**/p[0-9]*_molecules.csv"), recursive=True)))
for f in used_files:
    d = pl.read_csv(f, infer_schema_length=10000)
    for col in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if col in d.columns: used |= set(str(x) for x in d[col].drop_nulls().to_list())
panel_keys = set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["inchikey14"].to_list())
c = census.join(folds.select("inchikey14", "scorer_key", "identity_group", "fold_identity", "smiles"), on="inchikey14", how="left")
counts = {"census": c.height}
c = c.filter(pl.col("fold_identity") == FOLD); counts[f"fold{FOLD}"] = c.height
c = c.filter(~pl.col("in_msg_raw") & ~pl.col("in_msg_scorer")); counts["not_msg"] = c.height
c = c.filter(~pl.col("inchikey14").is_in(list(panel_keys))); counts["not_panel"] = c.height
c = c.filter(pl.col("scorer_key").is_in(list(POOL_COCO)) | pl.col("inchikey14").is_in(list(COCO_RAW))); counts["coconut_truth"] = c.height
used_groups = set(folds.filter(pl.col("inchikey14").is_in(list(used)) | pl.col("scorer_key").is_in(list(used)))["identity_group"].to_list())
c = c.with_columns((pl.col("inchikey14").is_in(list(used)) | pl.col("scorer_key").is_in(list(used)) | pl.col("identity_group").is_in(list(used_groups)) | pl.col("in_dev")).alias("used"))
m = meta.filter(pl.col("inchikey14").is_in(c["inchikey14"].to_list()))
per = m.group_by("inchikey14").agg(pl.col("ingest_lib").unique().sort().str.join(";").alias("q_libs"), (pl.col("ingest_lib") == "enveda-180").sum().alias("n_tims"),
                                   (pl.col("ionization_mode") == "positive").sum().alias("n_pos_spec"), (pl.col("ionization_mode") == "negative").sum().alias("n_neg_spec"),
                                   pl.col("adduct").is_in(["[M+H]+", "[M+Na]+"]).sum().alias("n_hna"), pl.len().alias("n_spec"))
c = c.join(per, on="inchikey14", how="inner"); counts["with_test_adduct_spectra"] = c.height
counts["with_timstof"] = int((c["n_tims"] > 0).sum()); counts["unused"] = int((~c["used"]).sum()); counts["unused_with_timstof"] = int(((~c["used"]) & (c["n_tims"] > 0)).sum())
print(counts, flush=True)
# official-key structures, Morgan FPs, Murcko generic scaffolds
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina
RDLogger.DisableLog("rdApp.*"); T = rdMolStandardize.TautomerEnumerator()
fps, ok_rows, murcko, mass = [], [], [], []
for i, s in enumerate(c["smiles"].to_list()):
    mol = Chem.MolFromSmiles(s) if s else None
    if mol is None: continue
    try:
        Chem.RemoveStereochemistry(mol); mol = T.Canonicalize(mol)
        fps.append(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)); ok_rows.append(i); mass.append(Descriptors.ExactMolWt(mol))
        try: murcko.append(Chem.MolToSmiles(MurckoScaffold.MakeScaffoldGeneric(MurckoScaffold.GetScaffoldForMol(mol))))
        except Exception: murcko.append("")
    except Exception: continue
c = c[ok_rows].with_columns(pl.Series("mass", mass), pl.Series("murcko_generic", murcko)); counts["fingerprinted"] = c.height
n = len(fps); print(f"fingerprints {n} ({time.time()-t0:.0f}s)", flush=True)
sims = [DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i]) for i in range(1, n)]
dists = [1.0 - x for row in sims for x in row]
fam = {}
for thr in (0.4, 0.5, 0.6, 0.7):
    cl = Butina.ClusterData(dists, n, 1.0 - thr, isDistData=True)
    lab = np.empty(n, np.int64)
    for k, members in enumerate(cl): lab[list(members)] = k
    sizes = np.bincount(lab); fam[thr] = lab
    in_fam = sizes[lab] >= 2; used_np = c["used"].to_numpy()
    fam_unused = np.array([not used_np[lab == k].any() for k in range(len(sizes))])
    counts[f"butina_{thr}"] = dict(n_clusters=int(len(sizes)), singletons=int((sizes == 1).sum()), fam_ge2=int((sizes >= 2).sum()), members_in_fam_ge2=int(in_fam.sum()),
                                   fam_ge3=int((sizes >= 3).sum()), max_size=int(sizes.max()), size_hist={str(s): int((sizes == s).sum()) for s in range(2, 9)} | {">8": int((sizes > 8).sum())},
                                   fam_ge2_all_unused=int(((sizes >= 2) & fam_unused).sum()), members_fam_ge2_all_unused=int(sum(sizes[k] for k in range(len(sizes)) if sizes[k] >= 2 and fam_unused[k])),
                                   members_fam_ge2_with_timstof=int((in_fam & (c["n_tims"].to_numpy() > 0)).sum()))
    print(thr, counts[f"butina_{thr}"], flush=True)
mg = c["murcko_generic"].value_counts(); counts["murcko_generic"] = dict(n=int(mg.height), empty=int(c.filter(pl.col("murcko_generic") == "").height), ge2=int((mg["count"] >= 2).sum()))
c = c.with_columns(*[pl.Series(f"fam{int(t*100)}", fam[t]) for t in fam])
c.drop("smiles").write_parquet(os.path.join(OUT, "population.parquet"))
counts["inputs_sha256"] = {"census": sha(os.path.join(B, "eval_set2/census.parquet")), "structures": sha(os.path.join(ROOT, "data/external/identity_folds/structures.parquet")),
                           "script": sha(os.path.abspath(__file__))}
counts["used_files"] = len(used_files); counts["seconds"] = round(time.time() - t0)
json.dump(counts, open(os.path.join(OUT, "census.json"), "w"), indent=1); print(json.dumps(counts)[:3000])
