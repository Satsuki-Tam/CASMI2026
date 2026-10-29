"""141 (A3, GL discrimination objective) step 1, CPU: same-formula candidate decoys for the TRAIN spectra of data/glt/tims_s1 -- no model output.
For each train identity (official key of its SMILES): structures of the candidate stores (PubChem tier, v2 pool, COCONUT store) within +-2 mDa
of the truth's exact neutral mass whose neutral formula (wf_common.neutral_formula) equals the truth's, de-duplicated by official key;
excluded: the truth's official key, its tautomer-alias raw keys, every key of its identity group; and -- negatives count as TRAINING
EXPOSURE (Codex 141) -- every structure that is an identity of folds 0 / 1 / 2 or of the panel (official key or raw key in
identity_folds/structures.parquet with fold_identity in {0, 1, 2}, or a panel key), so that no current or future evaluation identity
(f1 / f2 / np053 / W135 / new timsTOF set / panel) is a negative. Candidates per identity are capped at --cap (200) by Tanimoto to the truth
(Morgan r2 2048, descending; ties by key) -- the pre-selection rule fixed before any GL scoring (Codex 141: "pre-selected set" recorded).
Writes data/glt/decoys/cands.parquet (identity key, candidate key, smiles, tanimoto, rank) + manifest.json (counts, exclusions, hashes).
The val spectra / identities are not touched.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/glt/make_glt_decoys.py [--cap 200]"""
import argparse, hashlib, json, os, pickle, sys, time
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
from wf_common import neutral_formula
ap = argparse.ArgumentParser(); ap.add_argument("--cap", type=int, default=200); ap.add_argument("--out", default="data/glt/decoys"); a = ap.parse_args(); t0 = time.time()
OUT = os.path.join(ROOT, a.out); os.makedirs(OUT, exist_ok=True)
if os.path.exists(os.path.join(OUT, "cands.parquet")): sys.exit("REFUSED: cands.parquet exists")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.Descriptors import ExactMolWt
from rdkit.Chem.MolStandardize import rdMolStandardize
RDLogger.DisableLog("rdApp.*"); T = rdMolStandardize.TautomerEnumerator()
def okey(smi):
    try:
        m = Chem.MolFromSmiles(smi); Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(T.Canonicalize(m))[:14]
    except Exception: return None
def rawkey(smi):
    try: return Chem.MolToInchiKey(Chem.MolFromSmiles(smi))[:14]
    except Exception: return None
D = os.path.join(ROOT, "data/glt/tims_s1"); lab = pd.read_csv(os.path.join(D, "labels.tsv"), sep="\t"); spl = pd.read_csv(os.path.join(D, "splits/split.tsv"), sep="\t")
lab = lab.merge(spl, left_on="spec", right_on="name"); tr = lab[lab.split == "train"]
st = pl.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet")).select("inchikey14", "scorer_key", "identity_group", "fold_identity")
EXCL = set(st.filter(pl.col("fold_identity").is_in([0, 1, 2]))["inchikey14"].to_list()) | set(x for x in st.filter(pl.col("fold_identity").is_in([0, 1, 2]))["scorer_key"].to_list() if x)
meta = pl.read_parquet(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet"), columns=["inchikey14", "ingest_lib", "scorer_ik14"])
PANEL = set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["inchikey14"].to_list()) | set(x for x in meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["scorer_ik14"].to_list() if x)
EXCL |= PANEL
G_ALL = {}
for ik, sk, g in st.select("inchikey14", "scorer_key", "identity_group").iter_rows():
    if g is not None: G_ALL.setdefault(g, set()).update(x for x in (ik, sk) if x)
# candidate stores (as b1_features)
tmass = np.load(os.path.join(ROOT, "data/external/pubchem_tier/pc_mass.npy"), mmap_mode="r"); toff = np.load(os.path.join(ROOT, "data/external/pubchem_tier/pc_off.npy"), mmap_mode="r")
tbuf = np.load(os.path.join(ROOT, "data/external/pubchem_tier/pc_smiles.npy"), mmap_mode="r")
pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet")).select("smiles", "mass"); po = np.argsort(pool["mass"].to_numpy(), kind="stable")
pmass = pool["mass"].to_numpy()[po]; psmi = pool["smiles"].to_numpy()[po]
cmeta = pickle.load(open(os.path.join(ROOT, "data/external/coconut/coco_meta.pkl"), "rb")); cmass = np.load(os.path.join(ROOT, "data/external/coconut/coco_mass.npy")); csmi = np.asarray(cmeta["smiles"])   # our own COCONUT prep file
def window(M, tol=0.002):
    out = set(); lo = int(np.searchsorted(tmass, M - tol, "left")); hi = int(np.searchsorted(tmass, M + tol, "right"))
    if hi > lo:
        o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
        out |= {raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)}
    lo = int(np.searchsorted(pmass, M - tol, "left")); hi = int(np.searchsorted(pmass, M + tol, "right")); out |= {str(s) for s in psmi[lo:hi]}
    lo = int(np.searchsorted(cmass, M - tol, "left")); hi = int(np.searchsorted(cmass, M + tol, "right")); out |= {str(s) for s in csmi[lo:hi]}
    return out
ids = tr.drop_duplicates("inchikey")[["inchikey", "smiles", "identity_group"]]
stats = dict(train_spectra=len(tr), train_identities=len(ids), excluded_fold012_panel_keys=len(EXCL))
def job(r):   # one identity (fork: the stores and exclusion sets are shared)
    ik, smi, grp = r; smi = str(smi); m = Chem.MolFromSmiles(smi)
    if m is None: return ik, []
    tk = okey(smi); f = neutral_formula(smi); M = ExactMolWt(m); tfp = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
    own = {tk, str(ik)[:14]} | G_ALL.get(grp, set())
    try:
        mm = Chem.MolFromSmiles(smi); Chem.RemoveStereochemistry(mm); own |= {Chem.MolToInchiKey(x)[:14] for x in T.Enumerate(mm)}
    except Exception: pass
    cand = {}
    for s_ in window(M):
        if neutral_formula(s_) != f: continue
        rk = rawkey(s_); ok = okey(s_)
        if ok is None or ok in own or rk in own or ok in EXCL or rk in EXCL or ok in cand: continue
        cm = Chem.MolFromSmiles(s_); cfp = AllChem.GetMorganFingerprintAsBitVect(cm, 2, nBits=2048) if cm is not None else None
        cand[ok] = (s_, float(DataStructs.TanimotoSimilarity(tfp, cfp)) if cfp is not None else 0.0)
    top = sorted(cand.items(), key=lambda kv: (-kv[1][1], kv[0]))[:a.cap]
    return ik, [dict(identity=str(ik), truth_key=tk, cand_key=ok, smiles=s_, tanimoto=tn, rank=i + 1, n_same_formula=len(cand)) for i, (ok, (s_, tn)) in enumerate(top)]
from multiprocessing import Pool
rows, n_none = [], 0
with Pool(12) as pool_:
    for ik, rr in pool_.imap_unordered(job, list(ids.itertuples(index=False, name=None)), chunksize=4):
        rows += rr; n_none += int(not rr)
rows.sort(key=lambda d: (d["identity"], d["rank"]))
R = pd.DataFrame(rows); R.to_parquet(os.path.join(OUT, "cands.parquet"), index=False)
stats.update(identities_with_candidates=int(R.identity.nunique()) if len(R) else 0, identities_without=n_none, rows=len(R), median_same_formula=float(R.groupby("identity").n_same_formula.first().median()) if len(R) else 0.0,
             cap=a.cap, seconds=round(time.time() - t0), cands_sha256=sha(os.path.join(OUT, "cands.parquet")), labels_sha256=sha(os.path.join(D, "labels.tsv")), script_sha256=sha(os.path.abspath(__file__)))
json.dump(stats, open(os.path.join(OUT, "manifest.json"), "w"), indent=1); print(json.dumps(stats, indent=1))
