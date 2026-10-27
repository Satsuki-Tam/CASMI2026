"""Exploratory: how related are the panel (enveda-np-examples, closest to the hidden test) molecules to EACH OTHER? (host 2026-10-26: label-free
use of similarity between test spectra is allowed -> transductive analog propagation is worth it only if test molecules have relatives in the test.)
Per molecule: best other-panel-molecule by shifted entropy similarity (same polarity, up to 3 representative spectra each) and that neighbour's
structural Morgan Tanimoto; also the best structural neighbour."""
import os, sys, numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
from b1_common import ADDUCT_SHIFT, clean_peaks, entropy_weight
from b1_analog import sim_pair
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*"); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
st = f"{ROOT}/data/processed/spectra_store"
meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
P = meta.filter((pl.col("ingest_lib") == "enveda-np-examples") & pl.col("adduct").is_in(list(ADDUCT_SHIFT))).to_pandas()
MZ = np.load(f"{st}/spec_mz.npy", mmap_mode="r"); IT = np.load(f"{st}/spec_int.npy", mmap_mode="r"); OFF = np.load(f"{st}/spec_off.npy")
def prep(r):
    mz = np.asarray(MZ[OFF[r]:OFF[r + 1]], np.float64); it = np.asarray(IT[OFF[r]:OFF[r + 1]], np.float64)
    mz, it = clean_peaks(mz, it, prec=None, floor=0.005, top=64)
    if len(mz) < 3: return None
    p = entropy_weight(it); p = p / p.sum(); S = float(-(p[p > 0] * np.log(p[p > 0])).sum()); o = np.argsort(mz)
    return (mz[o], p[o], S, float(P.loc[P.row == r, "precursor_mz"].iloc[0]))
reps = {}
for (k, mode), g in P.groupby(["scorer_ik14", "ionization_mode"]):
    g = g.assign(pref=~g.adduct.isin(["[M+H]+", "[M-H]-"]), dce=(g.ce_mean.fillna(35) - 35).abs()).sort_values(["pref", "dce", "row"]).head(3)
    sp = [x for x in (prep(int(r)) for r in g.row) if x is not None]
    if sp: reps[(k, mode)] = sp
keys = sorted({k for k, _ in reps}); print("panel molecules with spectra:", len(keys))
ts = pd.read_parquet(f"{ROOT}/data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet", columns=["key", "smiles"]).drop_duplicates("key")
smi = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
fps = {k: MG.GetFingerprint(Chem.MolFromSmiles(smi[k])) for k in keys if k in smi and Chem.MolFromSmiles(smi[k]) is not None}
keys = [k for k in keys if k in fps]; n = len(keys); print("with structures:", n)
T = np.zeros((n, n)); Ssp = np.zeros((n, n))
for i in range(n):
    T[i] = DataStructs.BulkTanimotoSimilarity(fps[keys[i]], [fps[k] for k in keys])
    for j in range(i + 1, n):
        best = 0.0
        for mode in ("positive", "negative"):
            a = reps.get((keys[i], mode)); b = reps.get((keys[j], mode))
            if a and b: best = max(best, max(sim_pair(x, y) for x in a for y in b))
        Ssp[i, j] = Ssp[j, i] = best
np.fill_diagonal(T, 0); np.fill_diagonal(Ssp, 0)
bs = Ssp.max(1); bj = Ssp.argmax(1); tan_of_bs = T[np.arange(n), bj]; bt = T.max(1)
print(f"best spectral neighbour sim: median {np.median(bs):.3f}, share >=0.5 {np.mean(bs >= 0.5):.3f}, >=0.7 {np.mean(bs >= 0.7):.3f}")
print(f"tanimoto of that neighbour: median {np.median(tan_of_bs):.3f}; share with spectral>=0.5 AND tanimoto>=0.5: {np.mean((bs >= 0.5) & (tan_of_bs >= 0.5)):.3f}")
print(f"best structural neighbour tanimoto: median {np.median(bt):.3f}, share >=0.5 {np.mean(bt >= 0.5):.3f}, >=0.7 {np.mean(bt >= 0.7):.3f}")
for thr in (0.3, 0.5, 0.7):
    m = Ssp >= thr; ok = (T[m] >= 0.5).mean() if m.any() else float('nan')
    print(f"  pairs with spectral sim >= {thr}: {int(m.sum() // 2)}; share of those with tanimoto >= 0.5: {ok:.3f}")
